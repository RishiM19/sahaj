import { useState } from "react";
import { type Observation, sendChatMessage } from "../api";
import type { Persona } from "../personas";

interface Message {
  from: "user" | "sahaj";
  text: string;
  observations?: Observation[];
}

export default function ChatScreen({ persona }: { persona: Persona }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(persona.seedMessage);
  const [quickReplies, setQuickReplies] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    setMessages((m) => [...m, { from: "user", text }]);
    setInput("");
    setQuickReplies([]);
    setLoading(true);
    try {
      const res = await sendChatMessage(persona.phone, text);
      setMessages((m) => [
        ...m,
        { from: "sahaj", text: res.reply, observations: res.observations },
      ]);
      setQuickReplies(res.suggested_actions);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { from: "sahaj", text: `(couldn't reach SAHAJ - is the backend running? ${err})` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="phone-shell">
      <div className="chat-header">
        SAHAJ
        <small>Official financial assistant · always on</small>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            Send {persona.name}'s message below to see SAHAJ trace it end to end.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i}>
            <div className={`bubble ${m.from}`}>{m.text}</div>
            {m.observations
              ?.filter((o) => o.headline !== "(unavailable)")
              .map((o, j) => (
                <div key={j} className={`observation-card ${o.severity}`}>
                  <div className="headline">
                    {o.severity === "critical" ? "⚠ " : ""}
                    {o.agent}
                  </div>
                  {o.headline}
                </div>
              ))}
          </div>
        ))}
        {loading && <div className="bubble sahaj">…</div>}
      </div>
      {quickReplies.length > 0 && (
        <div className="quick-replies">
          {quickReplies.map((qr) => (
            <button key={qr} className="quick-reply" onClick={() => send(qr)}>
              {qr}
            </button>
          ))}
        </div>
      )}
      <div className="chat-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
          placeholder="Type a message…"
        />
        <button onClick={() => send(input)} aria-label="Send">
          ➤
        </button>
      </div>
    </div>
  );
}
