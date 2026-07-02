const API_BASE = "http://localhost:8000";

export interface Observation {
  agent: string;
  headline: string;
  details: Record<string, unknown>;
  severity: "info" | "warning" | "critical";
  suggested_actions: string[];
}

export interface ChatResponse {
  reply: string;
  suggested_actions: string[];
  observations: Observation[];
  bft: {
    behavioral_state: string;
    state_score: number;
    trust_level: number;
  };
}

export interface UssdResponse {
  screen: string;
  suggested_actions: string[];
}

export interface BftSnapshot {
  phone: string;
  name: string | null;
  behavioral_state: string;
  state_score: number;
  trust_level: number;
  income_trend_pct: number | null;
  current_balance: number | null;
}

export async function sendChatMessage(phone: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, message }),
  });
  if (!res.ok) throw new Error(`chat request failed: ${res.status}`);
  return res.json();
}

export async function sendUssdMessage(phone: string, message: string): Promise<UssdResponse> {
  const res = await fetch(`${API_BASE}/api/ussd/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, message }),
  });
  if (!res.ok) throw new Error(`ussd request failed: ${res.status}`);
  return res.json();
}

export async function getBft(phone: string): Promise<BftSnapshot> {
  const res = await fetch(`${API_BASE}/api/chat/bft/${encodeURIComponent(phone)}`);
  if (!res.ok) throw new Error(`bft lookup failed: ${res.status}`);
  return res.json();
}
