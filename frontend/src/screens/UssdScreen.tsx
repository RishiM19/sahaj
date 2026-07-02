import { useState } from "react";
import { sendUssdMessage } from "../api";
import type { Persona } from "../personas";

export default function UssdScreen({ persona }: { persona: Persona }) {
  const [screen, setScreen] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(text: string) {
    if (!text.trim() || loading) return;
    setLoading(true);
    try {
      const res = await sendUssdMessage(persona.phone, text);
      setScreen(res.screen);
      setInput("");
    } catch (err) {
      setScreen(`(no signal - backend unreachable: ${err})`);
    } finally {
      setLoading(false);
    }
  }

  function press(digit: string) {
    setInput((v) => v + digit);
  }

  return (
    <div className="ussd-shell">
      <div className="ussd-screen">
        <div className="title">SAHAJ · *99#</div>
        {loading
          ? "connecting…"
          : (screen ?? `No internet. No data plan.\n\nDial *99# to reach SAHAJ.\n\nTry: "${persona.seedMessage}"`)}
      </div>
      <div className="ussd-input-row" style={{ marginBottom: "0.6rem" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit(input)}
          placeholder={screen ? "Reply…" : "Type your message and dial"}
        />
        <button onClick={() => submit(input)}>SEND</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.4rem" }}>
        {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((d) => (
          <button key={d} className="ussd-input-row-key" onClick={() => press(d)}>
            {d}
          </button>
        ))}
        <button onClick={() => setInput("")}>CLR</button>
        <button onClick={() => press("0")}>0</button>
        <button onClick={() => submit(input)}>SEND</button>
      </div>
    </div>
  );
}
