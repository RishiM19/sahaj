"""The Orchestrator: LangGraph wiring three steps around the shared
blackboard - dispatch every PTP-allowed agent in parallel, compose the one
reply the user actually sees out of their observations, then write the
outcome back onto the Behavioral Financial Twin so the next turn starts
sharper. See docs/ARCHITECTURE.md ("System layers") for the full picture.
"""

from __future__ import annotations

import asyncio
import json

import asyncpg
from langgraph.graph import END, START, StateGraph
from neo4j import AsyncDriver
from qdrant_client import AsyncQdrantClient

from app.agents.base import Agent, Observation, TurnContext
from app.agents.cash_flow import CashFlowAgent
from app.agents.community_intelligence import CommunityIntelligenceAgent
from app.agents.crisis_intercept import CrisisInterceptAgent
from app.agents.financial_psyche import FinancialPsycheAgent
from app.agents.learning_literacy import LearningLiteracyAgent
from app.agents.life_simulator import LifeSimulatorAgent
from app.agents.scam_guard import ScamGuardAgent
from app.agents.scheme_navigator import SchemeNavigatorAgent
from app.bft.service import BFTService
from app.llm.client import LLMClient
from app.orchestrator.state import TurnState
from app.rag.schemes import SchemeIndex
from app.trust.ptp import agent_allowed, max_response_depth

_COMPOSE_SYSTEM = """You are SAHAJ, a financial assistant for Indian users the formal system
underserves. You've just received a set of internal observations from specialist agents about
one user message. Compose ONE short reply to the user - warm, direct, no jargon, in the same
language register as their message. If an agent flagged a scam, lead with that. If there's a
cash-flow risk, state the number plainly (day/amount), don't hedge it away. Never mention you
are "composing from observations" - just answer as SAHAJ.

Reply with strict JSON only:
{"reply": "<the message to send the user, 2-5 sentences>", "suggested_actions": ["<short quick-reply label>", ...]}
Offer at most 3 suggested_actions, only if there's a natural next step."""


def _bft_lines(bft) -> str:
    trend = bft.income_trend_pct
    return (
        f"User state: {bft.behavioral_state.name} (score {bft.state_score:.0f}), "
        f"trust level {bft.trust_level}, "
        f"income trend {trend:+.0f}%." if trend is not None else
        f"User state: {bft.behavioral_state.name} (score {bft.state_score:.0f}), trust level {bft.trust_level}."
    )


class Orchestrator:
    def __init__(
        self,
        neo4j_driver: AsyncDriver,
        pg_pool: asyncpg.Pool,
        qdrant: AsyncQdrantClient,
        llm: LLMClient | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.bft = BFTService(neo4j_driver)
        self.agents: list[Agent] = [
            FinancialPsycheAgent(self.llm),
            ScamGuardAgent(self.llm, pg_pool),
            CashFlowAgent(),
            LifeSimulatorAgent(self.llm),
            SchemeNavigatorAgent(SchemeIndex(qdrant)),
            CrisisInterceptAgent(),
            CommunityIntelligenceAgent(pg_pool),
            LearningLiteracyAgent(self.llm),
        ]
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(TurnState)
        graph.add_node("dispatch_agents", self._dispatch_agents)
        graph.add_node("compose", self._compose)
        graph.add_node("update_state", self._update_state)
        graph.add_edge(START, "dispatch_agents")
        graph.add_edge("dispatch_agents", "compose")
        graph.add_edge("compose", "update_state")
        graph.add_edge("update_state", END)
        return graph.compile()

    async def _dispatch_agents(self, state: TurnState) -> dict:
        ctx = TurnContext(
            phone=state["phone"], channel=state["channel"], message=state["message"], bft=state["bft"]
        )
        allowed = [a for a in self.agents if agent_allowed(a.min_trust_level, ctx.bft.trust_level)]

        async def run_one(agent: Agent) -> Observation | None:
            try:
                return await agent.run(ctx)
            except Exception as exc:  # one agent failing must not sink the whole turn
                return Observation(
                    agent=agent.name, headline="(unavailable)", details={"error": str(exc)}
                )

        results = await asyncio.gather(*(run_one(a) for a in allowed))
        observations = [o for o in results if o is not None]

        state_update = next(
            (o.details for o in observations if o.agent == "financial_psyche"), None
        )
        return {"observations": observations, "state_update": state_update}

    async def _compose(self, state: TurnState) -> dict:
        bft = state["bft"]
        depth = max_response_depth(bft.trust_level)
        obs_lines = "\n".join(
            f"- [{o.agent} / {o.severity}] {o.headline} {json.dumps(o.details, default=str)}"
            for o in state["observations"]
        )
        prompt = (
            f"{_bft_lines(bft)}\n"
            f"Response depth allowed: {depth}\n"
            f"User message: {state['message']!r}\n"
            f"Agent observations:\n{obs_lines or '(none)'}"
        )
        critical = [o for o in state["observations"] if o.severity == "critical"]

        try:
            result = await self.llm.complete_json(prompt, system=_COMPOSE_SYSTEM, temperature=0.4)
            narrative = result.get("reply", "").strip()
            actions = [a for a in result.get("suggested_actions", []) if isinstance(a, str)][:3]
        except Exception:
            narrative = ""
            actions = []

        if not actions and critical:
            actions = critical[0].suggested_actions

        # A small local model paraphrasing multiple observations sometimes drops
        # the one that matters most. Critical safety facts (an unregistered
        # lender, a CFTI-matched scam) are never left to depend on that - they're
        # always surfaced verbatim, with the LLM's narrative underneath for
        # context and tone rather than as the only carrier of the warning.
        alert_lines = "\n".join(f"⚠ {o.headline}" for o in critical)
        reply = f"{alert_lines}\n\n{narrative}".strip() if alert_lines else narrative
        if not reply:
            reply = "I couldn't reach the reasoning model - try again in a moment."

        return {"response": reply, "suggested_actions": actions}

    async def _update_state(self, state: TurnState) -> dict:
        phone = state["phone"]
        update = state.get("state_update")
        if update and update.get("proposed_score") is not None:
            factors = [f for f in [update.get("emotion"), update.get("bias")] if f]
            await self.bft.update_behavioral_state(phone, update["proposed_score"], factors)
        await self.bft.log_query(phone, state["channel"], query_type="turn")
        return {}

    async def handle_turn(self, phone: str, channel: str, message: str) -> TurnState:
        bft = await self.bft.get_or_create_user(phone)
        initial: TurnState = {
            "phone": phone,
            "channel": channel,
            "message": message,
            "bft": bft,
            "observations": [],
            "response": "",
            "suggested_actions": [],
            "state_update": None,
        }
        return await self._graph.ainvoke(initial)
