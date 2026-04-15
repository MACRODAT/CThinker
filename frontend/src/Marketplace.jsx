import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://127.0.0.1:8000/api";

// ── Colour helpers ─────────────────────────────────────────────────────────────
const CAT_COLORS = {
  Intelligence: { bg: "#0c1a2e", accent: "#38bdf8", icon: "🧠" },
  Communication:{ bg: "#0e1a14", accent: "#4ade80", icon: "📡" },
  Economy:      { bg: "#1a1200", accent: "#fbbf24", icon: "💰" },
  Strategy:     { bg: "#1a0e2e", accent: "#a78bfa", icon: "♟️" },
  Creative:     { bg: "#1a0e18", accent: "#f472b6", icon: "✨" },
  Automation:   { bg: "#0a1a1a", accent: "#2dd4bf", icon: "⚙️" },
  General:      { bg: "#111318", accent: "#94a3b8", icon: "🔧" },
};
const catStyle = (cat) => CAT_COLORS[cat] || CAT_COLORS["General"];

// ── Badge ─────────────────────────────────────────────────────────────────────
const Badge = ({ children, color = "#374151" }) => (
  <span style={{
    fontSize: 9, padding: "2px 7px", borderRadius: 4,
    background: color + "22", color, fontWeight: 700,
    letterSpacing: "0.4px", border: `1px solid ${color}33`,
  }}>{children}</span>
);

// ── Tool Card ─────────────────────────────────────────────────────────────────
function ToolCard({ tool, agents, ownedSet, onBuy, onInvoke, workshopMode = false, onValidate }) {
  const [expanded, setExpanded] = useState(false);
  const [buyAgent, setBuyAgent] = useState("");
  const [invokeAgent, setInvokeAgent] = useState("");
  const [invokeArgs, setInvokeArgs] = useState("");
  const cs = catStyle(tool.category);
  const isOwned = ownedSet.has(tool.id);

  return (
    <div style={{
      background: cs.bg, border: `1px solid ${cs.accent}22`,
      borderRadius: 10, padding: "14px 16px", marginBottom: 10,
      transition: "border-color 0.2s",
    }}
      onMouseEnter={e => e.currentTarget.style.borderColor = cs.accent + "66"}
      onMouseLeave={e => e.currentTarget.style.borderColor = cs.accent + "22"}
    >
      {/* ── Header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5, flexWrap: "wrap" }}>
            <span style={{ fontSize: 11, fontFamily: "monospace", color: cs.accent, fontWeight: 700 }}>
              {cs.icon} {tool.id}
            </span>
            <Badge color={cs.accent}>{tool.category}</Badge>
            {isOwned && <Badge color="#4ade80">✅ OWNED</Badge>}
            {tool.workshop_validated && !workshopMode && <Badge color="#a78bfa">✓ Validated</Badge>}
            <Badge color="#94a3b8">v{tool.version || "1.0"}</Badge>
            {(tool.purchase_count > 0) && <Badge color="#fbbf24">🛒 {tool.purchase_count}</Badge>}
          </div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 4 }}>
            {tool.name}
          </div>
        </div>

        {/* Prices */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4, flexShrink: 0 }}>
          {(tool.ownership_price > 0) && (
            <span style={{ fontSize: 11, color: cs.accent, fontWeight: 700 }}>
              🏷️ Own: {tool.ownership_price} pts
            </span>
          )}
          {(tool.price > 0) && (
            <span style={{ fontSize: 10, color: "#94a3b8" }}>
              {isOwned ? "Free ✅" : `Use: ${tool.price} pts/call`}
            </span>
          )}
          {(tool.price === 0 && tool.ownership_price === 0) && (
            <span style={{ fontSize: 10, color: "#4ade80" }}>FREE</span>
          )}
        </div>
      </div>

      {/* Description snippet */}
      <div style={{
        fontSize: 11, color: "#94a3b8", marginTop: 2,
        fontFamily: "monospace", lineHeight: 1.6,
        whiteSpace: "pre-wrap",
      }}>
        {tool.description.split("\n").slice(0, 2).join("\n")}
      </div>

      {/* Owner */}
      <div style={{ fontSize: 10, color: "#4b5563", marginTop: 5 }}>
        Owner: {tool.owner_name || tool.owner_id || "FOUNDER"}
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(v => !v)}
        style={{
          marginTop: 8, fontSize: 10, color: cs.accent,
          background: "none", border: "none", cursor: "pointer", padding: 0,
        }}
      >
        {expanded ? "▲ Less" : "▼ Details & Actions"}
      </button>

      {expanded && (
        <div style={{ marginTop: 10, borderTop: `1px solid ${cs.accent}22`, paddingTop: 10 }}>
          {/* Full description */}
          <pre style={{
            background: "#060810", border: `1px solid #1e222d`,
            borderRadius: 6, padding: "8px 12px",
            fontSize: 10, color: "#a5b4fc",
            fontFamily: "monospace", whiteSpace: "pre-wrap",
            maxHeight: 160, overflowY: "auto", marginBottom: 10,
          }}>
            {tool.description}
          </pre>

          {/* Prompt template preview */}
          {tool.prompt_template && (
            <>
              <div style={{ fontSize: 10, color: "#6b7280", marginBottom: 4 }}>CTHINKING Template:</div>
              <pre style={{
                background: "#060810", border: "1px solid #1a2030",
                borderRadius: 6, padding: "8px 12px",
                fontSize: 10, color: "#67e8f9",
                fontFamily: "monospace", whiteSpace: "pre-wrap",
                maxHeight: 180, overflowY: "auto", marginBottom: 12,
              }}>
                {tool.prompt_template}
              </pre>
            </>
          )}

          {/* Workshop-only: Validate */}
          {workshopMode && onValidate && (
            <button
              onClick={() => onValidate(tool.id)}
              style={{
                padding: "6px 14px", background: "#4f46e5", color: "#fff",
                border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 700,
                fontSize: 11, marginRight: 8,
              }}
            >
              ✅ Validate → Publish to Marketplace
            </button>
          )}

          {/* Buy ownership */}
          {!workshopMode && !isOwned && (tool.ownership_price > 0) && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10, flexWrap: "wrap" }}>
              <select
                value={buyAgent}
                onChange={e => setBuyAgent(e.target.value)}
                style={{ padding: "4px 8px", background: "#0d0f14", color: "#d1d5db", border: "1px solid #374151", borderRadius: 6, fontSize: 11 }}
              >
                <option value="">— select agent —</option>
                {agents.map(a => (
                  <option key={a.id} value={a.id}>{a.name_id} ({a.wallet_current} pts)</option>
                ))}
              </select>
              <button
                onClick={() => buyAgent && onBuy(tool.id, buyAgent)}
                disabled={!buyAgent}
                style={{
                  padding: "5px 14px", background: cs.accent + "22", color: cs.accent,
                  border: `1px solid ${cs.accent}55`, borderRadius: 6, cursor: "pointer",
                  fontWeight: 700, fontSize: 11, opacity: buyAgent ? 1 : 0.4,
                }}
              >
                🛒 Buy Ownership ({tool.ownership_price} pts)
              </button>
            </div>
          )}

          {/* Invoke (test tool) */}
          {!workshopMode && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <select
                value={invokeAgent}
                onChange={e => setInvokeAgent(e.target.value)}
                style={{ padding: "4px 8px", background: "#0d0f14", color: "#d1d5db", border: "1px solid #374151", borderRadius: 6, fontSize: 11 }}
              >
                <option value="">— agent —</option>
                {agents.map(a => (
                  <option key={a.id} value={a.id}>{a.name_id}</option>
                ))}
              </select>
              <input
                value={invokeArgs}
                onChange={e => setInvokeArgs(e.target.value)}
                placeholder="args (comma-separated)"
                style={{
                  padding: "4px 8px", background: "#0d0f14", color: "#d1d5db",
                  border: "1px solid #374151", borderRadius: 6, fontSize: 11,
                  width: 180,
                }}
              />
              <button
                onClick={() => invokeAgent && onInvoke(tool.id, invokeAgent, invokeArgs)}
                disabled={!invokeAgent}
                style={{
                  padding: "5px 14px", background: "#0f2620", color: "#4ade80",
                  border: "1px solid #4ade8055", borderRadius: 6, cursor: "pointer",
                  fontWeight: 700, fontSize: 11, opacity: invokeAgent ? 1 : 0.4,
                }}
              >
                ▶ Test Invoke
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Marketplace Panel ────────────────────────────────────────────────────
export default function Marketplace({ agents = [] }) {
  const [tab, setTab]               = useState("marketplace"); // marketplace | workshop | stats
  const [tools, setTools]           = useState([]);
  const [workshop, setWorkshop]     = useState([]);
  const [stats, setStats]           = useState(null);
  const [category, setCategory]     = useState("ALL");
  const [categories, setCategories] = useState([]);
  const [search, setSearch]         = useState("");
  const [ownedMap, setOwnedMap]     = useState({}); // agent_id → Set<tool_id>
  const [invokeResult, setInvokeResult] = useState(null);
  const [loading, setLoading]       = useState(false);
  const [toast, setToast]           = useState(null);

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  // ── Fetch everything ────────────────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [mkt, ws, cats, st] = await Promise.all([
        fetch(`${API_BASE}/marketplace`).then(r => r.json()),
        fetch(`${API_BASE}/workshop`).then(r => r.json()),
        fetch(`${API_BASE}/marketplace/categories`).then(r => r.json()),
        fetch(`${API_BASE}/marketplace/stats`).then(r => r.json()),
      ]);
      setTools(Array.isArray(mkt) ? mkt : []);
      setWorkshop(Array.isArray(ws) ? ws : []);
      setCategories(["ALL", ...(Array.isArray(cats) ? cats : [])]);
      setStats(st);
    } catch (e) {
      showToast("Failed to load marketplace", "error");
    }
    setLoading(false);
  }, []);

  const fetchOwnerships = useCallback(async () => {
    const map = {};
    for (const ag of agents) {
      try {
        const data = await fetch(`${API_BASE}/agents/${ag.id}/owned-tools`).then(r => r.json());
        map[ag.id] = new Set(Array.isArray(data) ? data.map(d => d.tool_id) : []);
      } catch { map[ag.id] = new Set(); }
    }
    setOwnedMap(map);
  }, [agents]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { if (agents.length) fetchOwnerships(); }, [agents, fetchOwnerships]);

  // ── Actions ─────────────────────────────────────────────────────────────────
  const handleBuy = async (toolId, agentId) => {
    try {
      const r = await fetch(`${API_BASE}/marketplace/${toolId}/buy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId }),
      }).then(r => r.json());
      if (r.error) { showToast(r.error, "error"); return; }
      showToast(`✅ Purchased "${toolId}" for ${r.price_paid} pts!`);
      fetchOwnerships();
      fetchData();
    } catch { showToast("Purchase failed", "error"); }
  };

  const handleInvoke = async (toolId, agentId, args) => {
    setInvokeResult({ loading: true, toolId });
    try {
      const r = await fetch(`${API_BASE}/tools/${toolId}/invoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, args }),
      }).then(r => r.json());
      setInvokeResult({ toolId, result: r.result || r.error || JSON.stringify(r) });
    } catch (e) {
      setInvokeResult({ toolId, result: `Error: ${e.message}` });
    }
  };

  const handleValidate = async (toolId) => {
    try {
      const r = await fetch(`${API_BASE}/workshop/${toolId}/validate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ownership_price: 0, price: 0 }),
      }).then(r => r.json());
      if (r.error) { showToast(r.error, "error"); return; }
      showToast(`✅ "${toolId}" published to Marketplace!`);
      fetchData();
    } catch { showToast("Validation failed", "error"); }
  };

  // ── Owned check helper ────────────────────────────────────────────────────
  const allOwned = new Set(Object.values(ownedMap).flatMap(s => [...s]));

  // ── Filtered tools ─────────────────────────────────────────────────────────
  const filtered = tools.filter(t => {
    const matchCat = category === "ALL" || t.category === category;
    const q = search.toLowerCase();
    const matchSearch = !q || t.name.toLowerCase().includes(q)
      || t.id.toLowerCase().includes(q)
      || (t.category || "").toLowerCase().includes(q);
    return matchCat && matchSearch;
  });

  // ── Group by category for display ─────────────────────────────────────────
  const grouped = {};
  filtered.forEach(t => {
    const c = t.category || "General";
    if (!grouped[c]) grouped[c] = [];
    grouped[c].push(t);
  });

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: "0 0 40px", position: "relative" }}>

      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed", bottom: 24, right: 24, zIndex: 999,
          background: toast.type === "error" ? "#7f1d1d" : "#052e16",
          color: toast.type === "error" ? "#fca5a5" : "#4ade80",
          border: `1px solid ${toast.type === "error" ? "#991b1b" : "#166534"}`,
          borderRadius: 10, padding: "10px 18px", fontSize: 13, fontWeight: 600,
          boxShadow: "0 4px 24px rgba(0,0,0,0.5)",
        }}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #0d1117 0%, #090c14 100%)",
        borderBottom: "1px solid #1e222d", padding: "20px 24px 0",
        marginBottom: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
          <span style={{ fontSize: 22 }}>🛒</span>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#f1f5f9" }}>Tool Marketplace</div>
            <div style={{ fontSize: 11, color: "#6b7280" }}>
              Buy tools once, use forever · or pay per call
            </div>
          </div>
          {stats && (
            <div style={{ marginLeft: "auto", display: "flex", gap: 16 }}>
              {[
                { label: "On Market", val: stats.marketplace_count, c: "#38bdf8" },
                { label: "Workshop", val: stats.workshop_count, c: "#fbbf24" },
                { label: "Purchases", val: stats.total_purchases, c: "#4ade80" },
                { label: "Revenue", val: `${stats.total_revenue_pts} pts`, c: "#a78bfa" },
              ].map(s => (
                <div key={s.label} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 16, fontWeight: 800, color: s.c }}>{s.val}</div>
                  <div style={{ fontSize: 9, color: "#4b5563" }}>{s.label}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 2 }}>
          {[
            { id: "marketplace", label: `🛒 Marketplace (${tools.length})` },
            { id: "workshop",    label: `🔬 Workshop (${workshop.length})` },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: "8px 16px", fontSize: 12, fontWeight: 700,
                background: tab === t.id ? "#1e222d" : "transparent",
                color: tab === t.id ? "#f1f5f9" : "#6b7280",
                border: "none", borderBottom: tab === t.id ? "2px solid #6366f1" : "2px solid transparent",
                cursor: "pointer", borderRadius: "6px 6px 0 0",
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Invoke result bar */}
      {invokeResult && (
        <div style={{
          background: "#060810", borderBottom: "1px solid #1e222d",
          padding: "10px 24px", display: "flex", gap: 12, alignItems: "flex-start",
        }}>
          <span style={{ fontSize: 11, color: "#6366f1", fontWeight: 700, flexShrink: 0 }}>
            {invokeResult.loading ? "⏳ Running…" : `▶ ${invokeResult.toolId}`}
          </span>
          <pre style={{
            margin: 0, fontSize: 11, color: "#4ade80", fontFamily: "monospace",
            whiteSpace: "pre-wrap", flex: 1, maxHeight: 120, overflowY: "auto",
          }}>
            {invokeResult.loading ? "…" : invokeResult.result}
          </pre>
          <button onClick={() => setInvokeResult(null)}
            style={{ background: "none", border: "none", color: "#6b7280", cursor: "pointer", fontSize: 14 }}>✕</button>
        </div>
      )}

      {/* Content */}
      <div style={{ padding: "20px 24px" }}>

        {/* ── MARKETPLACE TAB ── */}
        {tab === "marketplace" && (
          <>
            {/* Filter bar */}
            <div style={{ display: "flex", gap: 10, marginBottom: 18, flexWrap: "wrap", alignItems: "center" }}>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="🔍 Search tools…"
                style={{
                  padding: "7px 14px", background: "#0d0f14", color: "#d1d5db",
                  border: "1px solid #374151", borderRadius: 8, fontSize: 12,
                  flex: "1 1 200px", minWidth: 150,
                }}
              />
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {categories.map(c => {
                  const cs = catStyle(c);
                  return (
                    <button key={c} onClick={() => setCategory(c)} style={{
                      padding: "5px 12px", fontSize: 11, fontWeight: 700,
                      background: category === c ? cs.accent + "22" : "transparent",
                      color: category === c ? cs.accent : "#6b7280",
                      border: `1px solid ${category === c ? cs.accent + "55" : "#374151"}`,
                      borderRadius: 20, cursor: "pointer",
                    }}>
                      {c === "ALL" ? "All" : (CAT_COLORS[c]?.icon || "🔧") + " " + c}
                    </button>
                  );
                })}
              </div>
            </div>

            {loading && <div style={{ color: "#6b7280", fontSize: 13, marginBottom: 20 }}>Loading…</div>}

            {/* Grouped by category */}
            {Object.entries(grouped).map(([cat, catTools]) => {
              const cs = catStyle(cat);
              return (
                <div key={cat} style={{ marginBottom: 24 }}>
                  <div style={{
                    display: "flex", alignItems: "center", gap: 8,
                    marginBottom: 10, paddingBottom: 6,
                    borderBottom: `1px solid ${cs.accent}33`,
                  }}>
                    <span style={{ fontSize: 16 }}>{cs.icon}</span>
                    <span style={{ fontSize: 13, fontWeight: 800, color: cs.accent }}>
                      {cat}
                    </span>
                    <span style={{
                      fontSize: 10, background: cs.accent + "22", color: cs.accent,
                      padding: "1px 8px", borderRadius: 10, fontWeight: 600,
                    }}>
                      {catTools.length} tools
                    </span>
                  </div>
                  {catTools.map(t => (
                    <ToolCard
                      key={t.id}
                      tool={t}
                      agents={agents}
                      ownedSet={allOwned}
                      onBuy={handleBuy}
                      onInvoke={handleInvoke}
                    />
                  ))}
                </div>
              );
            })}

            {filtered.length === 0 && !loading && (
              <div style={{ color: "#6b7280", fontSize: 13, textAlign: "center", padding: "40px 0" }}>
                No tools found. Try a different search or category.
              </div>
            )}
          </>
        )}

        {/* ── WORKSHOP TAB ── */}
        {tab === "workshop" && (
          <>
            <div style={{
              background: "#1a1200", border: "1px solid #fbbf2444",
              borderRadius: 8, padding: "12px 16px", marginBottom: 18, fontSize: 12,
              color: "#fbbf24",
            }}>
              🔬 Workshop tools are pending validation. Click <strong>Validate</strong> to publish them to the Marketplace.
            </div>

            {workshop.length === 0 && (
              <div style={{ color: "#6b7280", fontSize: 13, textAlign: "center", padding: "40px 0" }}>
                No tools in workshop.
              </div>
            )}
            {workshop.map(t => (
              <ToolCard
                key={t.id}
                tool={{ ...t, owner_name: t.creator_name }}
                agents={agents}
                ownedSet={allOwned}
                onBuy={() => {}}
                onInvoke={handleInvoke}
                workshopMode
                onValidate={handleValidate}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}
