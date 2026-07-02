import { useEffect, useState } from "react";
import { type BftSnapshot, getBft, raiseTrustLevel } from "./api";
import { PERSONAS, type Persona } from "./personas";
import ChatScreen from "./screens/ChatScreen";
import UssdScreen from "./screens/UssdScreen";

type Tab = "chat" | "ussd";

export default function App() {
  const [persona, setPersona] = useState<Persona>(PERSONAS[0]);
  const [tab, setTab] = useState<Tab>("chat");
  const [bft, setBft] = useState<Record<string, BftSnapshot>>({});
  const [upgrading, setUpgrading] = useState(false);
  const [upgradeError, setUpgradeError] = useState<string | null>(null);

  async function refresh(phone: string) {
    try {
      const snap = await getBft(phone);
      setBft((b) => ({ ...b, [phone]: snap }));
    } catch {
      // backend not up yet - the screens themselves surface that error
    }
  }

  useEffect(() => {
    refresh(persona.phone);
    const id = setInterval(() => refresh(persona.phone), 4000);
    return () => clearInterval(id);
  }, [persona, tab]);

  async function handleRaiseTrust(phone: string, currentLevel: number) {
    setUpgrading(true);
    setUpgradeError(null);
    try {
      await raiseTrustLevel(phone, currentLevel + 1);
      await refresh(phone);
    } catch (err) {
      setUpgradeError(err instanceof Error ? err.message : String(err));
    } finally {
      setUpgrading(false);
    }
  }

  return (
    <>
      <div className="app-header">
        <h1>
          SAHAJ<span className="dot">.</span>
        </h1>
        <span className="tagline">A financial agent that acts before you ask</span>
      </div>
      <div className="layout">
        <div className="sidebar">
          {PERSONAS.map((p) => {
            const snap = bft[p.phone];
            const isActive = p.phone === persona.phone;
            return (
              <div key={p.phone} className={`persona-card ${isActive ? "active" : ""}`}>
                <button className="persona-card-select" onClick={() => setPersona(p)}>
                  <span className="name" style={{ color: p.color }}>
                    {p.name}
                  </span>
                  <span className="role">{p.role}</span>
                  {snap && (
                    <span className="bft-badge">
                      <span className={`badge state-${snap.behavioral_state}`}>
                        {snap.behavioral_state}
                      </span>
                      <span className="badge">trust L{snap.trust_level}</span>
                      {snap.income_verified && <span className="badge badge-verified">income ✓</span>}
                      {snap.digilocker_linked && <span className="badge badge-verified">DigiLocker ✓</span>}
                    </span>
                  )}
                </button>
                {isActive && snap && snap.trust_level < 4 && (
                  <button
                    className="raise-trust"
                    disabled={upgrading}
                    onClick={() => handleRaiseTrust(p.phone, snap.trust_level)}
                  >
                    {upgrading ? "…" : `Raise to L${snap.trust_level + 1}`}
                  </button>
                )}
                {isActive && upgradeError && <div className="upgrade-error">{upgradeError}</div>}
              </div>
            );
          })}
        </div>
        <div className="main">
          <div className="tabs">
            <button className={`tab ${tab === "chat" ? "active" : ""}`} onClick={() => setTab("chat")}>
              Tier 2/4 · Chat (WhatsApp / PWA)
            </button>
            <button className={`tab ${tab === "ussd" ? "active" : ""}`} onClick={() => setTab("ussd")}>
              Tier 1 · USSD *99#
            </button>
          </div>
          {tab === "chat" ? <ChatScreen persona={persona} /> : <UssdScreen persona={persona} />}
        </div>
      </div>
    </>
  );
}
