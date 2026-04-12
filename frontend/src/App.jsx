import { useState, useEffect, useCallback, useRef } from "react";
import './index.css';

const DEPT_META = {
  HF:  { name: "Health & Wellness",  color: "#4ade80", dim: "#052e16", icon: "🌱" },
  ING: { name: "Engineering",        color: "#22d3ee", dim: "#0c2030", icon: "⚙️" },
  STP: { name: "Strategic Planning", color: "#fb923c", dim: "#2d1500", icon: "📊" },
  UIT: { name: "Useful Intelligence",color: "#c084fc", dim: "#1e0a30", icon: "🧠" },
  FIN: { name: "Financing",          color: "#fbbf24", dim: "#1c1600", icon: "💰" },
};

const THREAD_COSTS = { Memo: 25, Strategy: 100, Endeavor: 100 };
const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE  = "ws://127.0.0.1:8000/ws";

const mkId  = () => Math.random().toString(36).slice(2, 8).toUpperCase();
const hhmm  = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

// ── Simple Markdown renderer (no deps) ────────────────────────────────────────
function renderMd(raw) {
  if (!raw) return '<span style="color:#374151;font-style:italic">Nothing to preview</span>';
  let s = raw
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  // Fenced code blocks
  s = s.replace(/```[\w]*\n?([\s\S]*?)```/g,
    '<pre style="background:#070809;padding:12px 14px;border-radius:6px;overflow-x:auto;border:1px solid #1e222d;margin:10px 0">' +
    '<code style="font-family:\'JetBrains Mono\',monospace;font-size:11px;color:#a5b4fc;line-height:1.6">$1</code></pre>');
  // Inline code
  s = s.replace(/`([^`]+)`/g,
    '<code style="background:#0b0c10;padding:1px 6px;border-radius:4px;font-size:12px;color:#a5b4fc;font-family:monospace">$1</code>');
  // Bold + italic combined
  s = s.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em style="color:#f9fafb">$1</em></strong>');
  // Bold
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong style="color:#f9fafb">$1</strong>');
  // Italic
  s = s.replace(/\*([^*\n]+)\*/g, '<em style="color:#e2e8f0">$1</em>');
  // H3
  s = s.replace(/^### (.+)$/gm,
    '<h3 style="color:#c084fc;font-size:13px;font-weight:700;margin:14px 0 6px;letter-spacing:0.5px">$1</h3>');
  // H2
  s = s.replace(/^## (.+)$/gm,
    '<h2 style="color:#818cf8;font-size:15px;font-weight:700;margin:16px 0 8px">$1</h2>');
  // H1
  s = s.replace(/^# (.+)$/gm,
    '<h1 style="color:#6366f1;font-size:18px;font-weight:800;margin:18px 0 10px">$1</h1>');
  // Horizontal rule
  s = s.replace(/^---$/gm, '<hr style="border:none;border-top:1px solid #1e222d;margin:12px 0">');
  // Unordered lists (-, *, •)
  s = s.replace(/^[•\-\*] (.+)$/gm,
    '<li style="color:#d1d5db;padding:3px 0;list-style:disc">$1</li>');
  s = s.replace(/(<li[^>]*>.*?<\/li>\n?)+/gs,
    '<ul style="padding-left:22px;margin:8px 0">$&</ul>');
  // Numbered lists
  s = s.replace(/^\d+\. (.+)$/gm,
    '<li style="color:#d1d5db;padding:3px 0;list-style:decimal">$1</li>');
  // Newlines → breaks (but not inside pre/code)
  s = s.replace(/\n/g, '<br>');
  return s;
}

// ── Markdown Editor / Split-view component ───────────────────────────────────
function MarkdownEditor({ value, onChange, rows = 7, placeholder = "Write markdown here…", label = null }) {
  const [mode, setMode] = useState("split"); // edit | split | preview
  const [isFull, setIsFull] = useState(false);

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") setIsFull(false);
    };
    if (isFull) {
      window.addEventListener("keydown", handleEsc);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "auto";
    }
    return () => {
      window.removeEventListener("keydown", handleEsc);
      document.body.style.overflow = "auto";
    };
  }, [isFull]);

  const editorH = isFull ? "calc(100vh - 100px)" : `${rows * 22}px`;

  const toolbar = (
    <div style={{ display: "flex", gap: 3, alignItems: "center" }}>
      <div style={{ display: "flex", gap: 3, marginRight: 8 }}>
        {["edit", "split", "preview"].map(m => (
          <button key={m} onClick={() => setMode(m)}
            style={{
              padding: "2px 8px", fontSize: 10, cursor: "pointer",
              background: mode === m ? "#6366f1" : "#11141a",
              border: `1px solid ${mode === m ? "#6366f1" : "#1e222d"}`,
              borderRadius: 4, color: mode === m ? "#fff" : "#6b7280",
              textTransform: "uppercase", letterSpacing: 0.5,
            }}>
            {m}
          </button>
        ))}
      </div>
      <button onClick={() => setIsFull(!isFull)}
        title={isFull ? "Exit Full Screen (Esc)" : "Full Screen"}
        style={{
          padding: "2px 8px", fontSize: 12, cursor: "pointer",
          background: isFull ? "#ef444422" : "#1e222d",
          border: `1px solid ${isFull ? "#ef4444" : "#2d3748"}`,
          borderRadius: 4, color: isFull ? "#ef4444" : "#9ca3af",
          display: "flex", alignItems: "center", justifyContent: "center"
        }}>
        {isFull ? "✕ Close" : "⛶"}
      </button>
    </div>
  );

  const wrapperStyle = isFull ? {
    position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh",
    background: "#070809", zIndex: 9999, padding: "20px 40px",
    display: "flex", flexDirection: "column"
  } : { position: "relative" };

  return (
    <div style={wrapperStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <label style={{ fontSize: 12, color: "#9ca3af", fontWeight: 500 }}>
          {label || (isFull ? "Fullscreen Editor" : "")}
        </label>
        {toolbar}
      </div>
      
      <div style={{
        display: "flex", border: "1px solid #1e222d", borderRadius: 8, overflow: "hidden",
        flex: isFull ? 1 : "initial"
      }}>
        {(mode === "edit" || mode === "split") && (
          <textarea
            value={value || ""}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            autoFocus={isFull}
            style={{
              flex: 1, border: "none", outline: "none",
              borderRight: mode === "split" ? "1px solid #1e222d" : "none",
              resize: "none", height: editorH,
              fontFamily: "'JetBrains Mono', 'Fira Mono', monospace",
              fontSize: isFull ? 14 : 12, background: "#0a0b0e",
              padding: "16px", color: "#d4d8e8", lineHeight: 1.65,
            }}
          />
        )}
        {(mode === "preview" || mode === "split") && (
          <div
            className="md-viewer"
            style={{
              flex: 1, padding: "16px", background: "#0d0f14",
              height: editorH, overflowY: "auto",
              fontSize: isFull ? 15 : 13, lineHeight: 1.65, color: "#9ca3af",
            }}
            dangerouslySetInnerHTML={{ __html: renderMd(value) }}
          />
        )}
      </div>
    </div>
  );
}

// ── Logger Level Badge Config ────────────────────────────────────────────────
const LOG_COLORS = {
  INFO:  "#6b7280",
  TICK:  "#3b82f6",
  LLM:   "#a855f7",
  TOOL:  "#f97316",
  POINT: "#10b981",
  WARN:  "#eab308",
  ERROR: "#ef4444",
};

// ── Logger View ──────────────────────────────────────────────────────────────
function Logger({ liveLogs, state }) {
  const [filter, setFilter]   = useState({ level: "", category: "", agent: "", search: "" });
  const [expanded, setExpanded] = useState(new Set());
  const [dbLogs, setDbLogs]   = useState([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const bottomRef = useRef(null);

  // Fetch historical logs from DB on mount
  useEffect(() => {
    fetch(`${API_BASE}/logs?limit=400`)
      .then(r => r.json())
      .then(data => setDbLogs(Array.isArray(data) ? data.reverse() : []))
      .catch(() => {});
  }, []);

  // Merge live + db logs, newest first, deduplicated by time+event
  const seen  = new Set();
  const merged = [...liveLogs, ...dbLogs].filter(l => {
    const key = `${l.time}|${l.event}|${l.agent_id}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  const filtered = merged.filter(l => {
    if (filter.level    && l.level    !== filter.level)    return false;
    if (filter.category && l.category !== filter.category) return false;
    if (filter.agent    && l.agent_id !== filter.agent)    return false;
    if (filter.search) {
      const hay = JSON.stringify(l).toLowerCase();
      if (!hay.includes(filter.search.toLowerCase())) return false;
    }
    return true;
  });

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && bottomRef.current)
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
  }, [liveLogs.length, autoScroll]);

  const toggleExpand = (i) => setExpanded(s => {
    const ns = new Set(s);
    ns.has(i) ? ns.delete(i) : ns.add(i);
    return ns;
  });

  const clearLive = () => {
    fetch(`${API_BASE}/logs`, { method: "DELETE" }).then(() => setDbLogs([]));
  };

  const agentIds = Object.keys(state.agents || {});

  return (
    <div style={{ height: "calc(100vh - 140px)", display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Header + Filter bar */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <input
          placeholder="🔍 Search all fields…"
          value={filter.search}
          onChange={e => setFilter({ ...filter, search: e.target.value })}
          style={{ flex: "2 1 160px", minWidth: 140 }}
        />
        <select value={filter.level} onChange={e => setFilter({ ...filter, level: e.target.value })} style={{ flex: "1 1 100px" }}>
          <option value="">All Levels</option>
          {Object.keys(LOG_COLORS).map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <select value={filter.category} onChange={e => setFilter({ ...filter, category: e.target.value })} style={{ flex: "1 1 110px" }}>
          <option value="">All Categories</option>
          {["ENGINE", "AGENT", "LLM", "TOOL", "SYSTEM"].map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={filter.agent} onChange={e => setFilter({ ...filter, agent: e.target.value })} style={{ flex: "1 1 110px" }}>
          <option value="">All Agents</option>
          {agentIds.map(id => <option key={id} value={id}>{state.agents[id]?.name_id || id}</option>)}
        </select>
        <button className="btn btn-soft" onClick={() => setFilter({ level: "", category: "", agent: "", search: "" })} style={{ fontSize: 11 }}>Reset</button>
        <button className="btn btn-soft" onClick={clearLive} style={{ fontSize: 11, color: "#ef4444" }}>🗑 Clear DB</button>
        <div
          onClick={() => setAutoScroll(v => !v)}
          style={{
            cursor: "pointer", fontSize: 11, padding: "4px 10px",
            background: autoScroll ? "#064e3b" : "#1a1d24",
            color: autoScroll ? "#34d399" : "#6b7280",
            borderRadius: 6, border: "1px solid #1e222d", userSelect: "none"
          }}>
          {autoScroll ? "⬇ Auto" : "⬇ Off"}
        </div>
        <span style={{ fontSize: 11, color: "#4b5563", padding: "0 4px" }}>{filtered.length} entries</span>
      </div>

      {/* Level legend */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {Object.entries(LOG_COLORS).map(([lv, col]) => (
          <span key={lv} onClick={() => setFilter(f => ({ ...f, level: f.level === lv ? "" : lv }))}
            style={{
              fontSize: 10, padding: "2px 8px", borderRadius: 3, cursor: "pointer",
              background: col + "22", color: col, border: `1px solid ${col}55`,
              fontWeight: 700, letterSpacing: 0.5,
              opacity: filter.level && filter.level !== lv ? 0.35 : 1,
            }}>
            {lv}
          </span>
        ))}
      </div>

      {/* Log rows */}
      <div style={{
        flex: 1, overflowY: "auto", background: "#070809",
        border: "1px solid #1a1d24", borderRadius: 8, fontFamily: "monospace",
      }}>
        {filtered.length === 0 && (
          <div style={{ color: "#374151", textAlign: "center", padding: 60, fontSize: 13 }}>
            No log entries yet — engine will emit logs on next tick.
          </div>
        )}
        {filtered.map((log, i) => {
          const isExp = expanded.has(i);
          let details = {};
          try { details = typeof log.details === "string" ? JSON.parse(log.details) : (log.details || {}); } catch {}
          const col = LOG_COLORS[log.level] || "#6b7280";
          return (
            <div key={i}
              onClick={() => toggleExpand(i)}
              style={{
                padding: "7px 14px",
                borderBottom: "1px solid #111316",
                cursor: "pointer",
                background: isExp ? "#0d0f14" : "transparent",
                transition: "background 0.1s",
              }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span className="mono" style={{ fontSize: 10, color: "#2d3748", minWidth: 74, flexShrink: 0 }}>
                  {log.time ? new Date(log.time).toLocaleTimeString() : "—"}
                </span>
                <span style={{
                  fontSize: 9, fontWeight: 800, letterSpacing: 0.8,
                  padding: "1px 6px", borderRadius: 3,
                  background: col + "22", color: col,
                  minWidth: 44, textAlign: "center", flexShrink: 0
                }}>{log.level}</span>
                <span style={{ fontSize: 10, color: "#374151", minWidth: 58, flexShrink: 0 }}>{log.category}</span>
                <span style={{ fontSize: 12, color: "#c9d1d9", fontWeight: 500, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {log.event}
                  {details.agent && <span style={{ color: "#6b7280" }}> · {details.agent}</span>}
                  {details.elapsed_s && <span style={{ color: "#4b5563" }}> · {details.elapsed_s}s</span>}
                </span>
                {log.agent_id && (
                  <span style={{ fontSize: 10, color: "#818cf8", flexShrink: 0, marginRight: 6 }}>
                    {state.agents?.[log.agent_id]?.name_id || log.agent_id}
                  </span>
                )}
                <span style={{ fontSize: 10, color: "#2d3748", flexShrink: 0 }}>{isExp ? "▲" : "▼"}</span>
              </div>

              {isExp && (
                <div style={{
                  marginTop: 8, padding: "10px 14px",
                  background: "#040506", borderRadius: 6,
                  border: "1px solid #1a1d24",
                }}>
                  {/* Quick fields */}
                  {details.prompt_preview && (
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ fontSize: 9, color: "#4b5563", fontWeight: 700, letterSpacing: 1, marginBottom: 4 }}>PROMPT PREVIEW</div>
                      <div style={{ fontSize: 11, color: "#6b7280", lineHeight: 1.6, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                        {details.prompt_preview}
                      </div>
                    </div>
                  )}
                  {details.response_preview && (
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ fontSize: 9, color: "#4b5563", fontWeight: 700, letterSpacing: 1, marginBottom: 4 }}>RESPONSE PREVIEW</div>
                      <div style={{ fontSize: 11, color: "#9ca3af", lineHeight: 1.6, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                        {details.response_preview}
                      </div>
                    </div>
                  )}
                  <div style={{ fontSize: 9, color: "#374151", fontWeight: 700, letterSpacing: 1, marginBottom: 4 }}>FULL DETAILS</div>
                  <pre style={{
                    margin: 0, fontSize: 11, color: "#6b7280",
                    whiteSpace: "pre-wrap", wordBreak: "break-all",
                    lineHeight: 1.6, maxHeight: 240, overflowY: "auto",
                  }}>
                    {JSON.stringify(details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [state, setState] = useState({ heartbeat: 0, departments: {}, agents: {}, threads: {}, prompts: {}, settings: {}, tools: {} });
  const [feed, setFeed]   = useState([]);
  const [logs, setLogs]   = useState([]);   // live log stream from WebSocket
  const [expandedFeedId, setExpandedFeedId] = useState(null);
  const [view, setView]   = useState("dashboard");

  const fetchState = useCallback(async () => {
    try {
      const r    = await fetch(`${API_BASE}/state`);
      const body = await r.json();
      setState(s => ({ ...s, ...body }));
    } catch (e) { console.error("fetch state error", e); }
  }, []);

  useEffect(() => {
    fetchState();
    const ws = new WebSocket(WS_BASE);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "heartbeat") {
        setState(s => ({ ...s, heartbeat: data.counter }));
        if (data.counter % 5 === 0) fetchState();
      } else if (data.type === "feed") {
        const item = data.feed_item;
        setFeed(f => [{ id: mkId(), time: hhmm(new Date().toISOString()), agent: item.agent, dept: item.dept, msg: item.msg, full: item.full_msg }, ...f].slice(0, 60));
        fetchState();
      } else if (data.type === "log") {
        setLogs(l => [data.log, ...l].slice(0, 600));
      }
    };
    return () => ws.close();
  }, [fetchState]);

  // Actions
  const createThread  = useCallback(async (ownerAgentId, topic, aim) => {
    await fetch(`${API_BASE}/threads`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ topic, aim, owner_agent_id: ownerAgentId }) });
    fetchState();
  }, [fetchState]);
  const approveThread = useCallback(async (tid) => { await fetch(`${API_BASE}/threads/${tid}/approve`, { method: "POST" }); fetchState(); }, [fetchState]);
  const rejectThread  = useCallback(async (tid) => { await fetch(`${API_BASE}/threads/${tid}/reject`,  { method: "POST" }); fetchState(); }, [fetchState]);
  const deleteThread  = useCallback(async (tid) => {
    if (window.confirm("Delete thread and all its messages?")) {
      await fetch(`${API_BASE}/threads/${tid}`, { method: "DELETE" });
      fetchState();
    }
  }, [fetchState]);
  const updateThread  = useCallback(async (tid, payload) => {
    await fetch(`${API_BASE}/threads/${tid}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    fetchState();
  }, [fetchState]);
  const postMessage   = useCallback(async (tid, agentId, content) => {
    await fetch(`${API_BASE}/threads/${tid}/messages`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ who: agentId, what: content }) });
    fetchState();
  }, [fetchState]);
  const updatePrompt  = useCallback(async (pid, payload) => {
    await fetch(`${API_BASE}/prompts/${pid}`,  { method: "PUT",  headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    fetchState();
  }, [fetchState]);
  const updateAgent   = useCallback(async (aid, payload) => {
    await fetch(`${API_BASE}/agents/${aid}`,   { method: "PUT",  headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    fetchState();
  }, [fetchState]);
  const addDeptPoints = useCallback(async (deptId, amount) => {
    await fetch(`${API_BASE}/departments/${deptId}/points`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ amount }) });
    fetchState();
  }, [fetchState]);
  const updateSetting = useCallback(async (key, value) => {
    await fetch(`${API_BASE}/settings/${key}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value }) });
    fetchState();
  }, [fetchState]);

  const navLinks = [
    { id: "dashboard",   label: "Dashboard",    icon: "⊞" },
    { id: "agents",      label: "Agents",        icon: "👥" },
    { id: "departments", label: "Departments",   icon: "🏢" },
    { id: "chats",       label: "Agent Chats",   icon: "🗯️" },
    { id: "threads",     label: "Threads",       icon: "💬" },
    { id: "tools",       label: "Agent Tools",   icon: "🛠️" },
    { id: "founder",     label: "Economy",       icon: "👑" },
    { id: "prompts",     label: "Prompt Design", icon: "✨" },
    { id: "logger",      label: "System Logger", icon: "📋" },
    { id: "settings",    label: "Settings",      icon: "⚙️" },
  ];

  const logCount = logs.length;

  return (
    <div className="app-container">
      {/* LEFT SIDEBAR */}
      <div className="sidebar">
        <div className="logo-area">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, background: "linear-gradient(135deg,#6366f1,#a855f7)", borderRadius: 8, display:"flex",alignItems:"center",justifyContent:"center" }}>
              <div style={{ width: 12, height: 12, background: "#fff", borderRadius: 2 }} />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: "#fff", letterSpacing: 0.5 }}>CTHINKER</div>
              <div style={{ fontSize: 10, color: "#6b7280" }}>Command Center</div>
            </div>
          </div>
        </div>

        <div className="nav-section" style={{ flex: 1, overflowY: "auto" }}>
          <div className="nav-header">NAVIGATION</div>
          {navLinks.map(l => (
            <div key={l.id} className={`nav-link ${view === l.id ? "active" : ""}`} onClick={() => setView(l.id)}
              style={{ position: "relative" }}>
              <span style={{ marginRight: 10, fontSize: 14 }}>{l.icon}</span>
              {l.label}
              {l.id === "logger" && logCount > 0 && (
                <span style={{
                  marginLeft: "auto", fontSize: 9, background: "#6366f1",
                  color: "#fff", borderRadius: 8, padding: "1px 6px", fontWeight: 700,
                }}>{logCount > 99 ? "99+" : logCount}</span>
              )}
            </div>
          ))}

          <div className="nav-header" style={{ marginTop: 24 }}>DEPARTMENTS</div>
          {Object.entries(DEPT_META).map(([id, meta]) => {
            const d   = state.departments[id];
            const pts = d?.ledger?.current || 0;
            return (
              <div key={id} className="nav-link" style={{ justifyContent: "space-between" }} onClick={() => setView("departments")}>
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: meta.color }} />
                  <span style={{ fontSize: 12 }}>{meta.name}</span>
                </span>
                <span className="mono" style={{ fontSize: 11, color: pts < 100 ? "#ef4444" : "#6b7280" }}>{pts}</span>
              </div>
            );
          })}
        </div>

        <div style={{ padding: 20, borderTop: "1px solid #1a1d24" }}>
          <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 6 }}>SYSTEM STATUS</div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981", boxShadow: "0 0 10px #10b981" }} />
            <span style={{ color: "#e2e8f0", fontSize: 12, fontWeight: 500 }}>Online &amp; Linked</span>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="main-content">
        <div style={{ height: 60, borderBottom: "1px solid #1a1d24", display: "flex", alignItems: "center", padding: "0 24px", justifyContent: "space-between" }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: "#fff", textTransform: "capitalize" }}>
            {navLinks.find(l => l.id === view)?.label || view}
          </div>
          <div className="mono" style={{ background: "#11141a", border: "1px solid #1e222d", padding: "6px 12px", borderRadius: 6, fontSize: 12, color: "#8b92a5" }}>
            Heartbeat: <span style={{ color: "#6366f1", fontWeight: 700 }}>{String(state.heartbeat).padStart(4, "0")}</span>/3600
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
          {view === "dashboard"   && <Dashboard   state={state} />}
          {view === "agents"      && <Agents       state={state} createThread={createThread} updateAgent={updateAgent} setView={setView} />}
          {view === "departments" && <Departments  state={state} />}
          {view === "chats"       && <Chats        state={state} fetchState={fetchState} />}
          {view === "threads"     && <Threads      state={state} approveThread={approveThread} rejectThread={rejectThread} deleteThread={deleteThread} updateThread={updateThread} postMessage={postMessage} />}
          {view === "tools"       && <Tools        state={state} fetchState={fetchState} />}
          {view === "founder"     && <Founder      state={state} addDeptPoints={addDeptPoints} />}
          {view === "prompts"     && <Prompts      state={state} updatePrompt={updatePrompt} />}
          {view === "logger"      && <Logger       liveLogs={logs} state={state} />}
          {view === "settings"    && <Settings     state={state} updateSetting={updateSetting} />}
        </div>
      </div>

      {/* RIGHT ACTIVITY PANEL */}
      <div className="right-panel">
        <div style={{ padding: 16, borderBottom: "1px solid #1a1d24", background: "#0b0c10" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", letterSpacing: 1, textTransform: "uppercase" }}>Activity Feed</div>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: 12 }}>
          {feed.length === 0 && <div style={{ fontSize: 12, color: "#4b5563", textAlign: "center", marginTop: 40 }}>Waiting for ticks…</div>}
          {feed.map(f => {
            const isExp = expandedFeedId === f.id;
            return (
              <div key={f.id} 
                onClick={() => setExpandedFeedId(isExp ? null : f.id)}
                style={{ 
                  background: isExp ? "#0d0f14" : "#11141a", 
                  border: `1px solid ${isExp ? "#6366f1" : "#1a1d24"}`, 
                  borderRadius: 8, padding: 10, marginBottom: 8,
                  cursor: "pointer", transition: "all 0.2s"
                }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: f.dept ? DEPT_META[f.dept]?.color : "#818cf8" }}>{f.agent}</span>
                  <span className="mono" style={{ fontSize: 10, color: "#4b5563" }}>{f.time}</span>
                </div>
                <div style={{ fontSize: 11, color: isExp ? "#d1d5db" : "#9ca3af", lineHeight: 1.5 }}>
                  {isExp ? (
                    <div style={{ wordBreak: "break-word" }} dangerouslySetInnerHTML={{ __html: renderMd(f.full || f.msg) }} />
                  ) : (
                    f.msg
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function Dashboard({ state }) {
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 20 }}>
        {Object.entries(DEPT_META).map(([id, meta]) => {
          const dept = state.departments[id];
          if (!dept) return null;
          const ceo = dept.ceo_name_id ? state.agents[dept.ceo_name_id] : null;
          return (
            <div key={id} className="card glow-border" style={{ "--glow": meta.color }}>
              <div style={{ height: 3, background: meta.color }} />
              <div className="card-header">
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span>{meta.icon}</span>
                    <span style={{ fontWeight: 600, color: "#fff", fontSize: 15 }}>{meta.name}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#6b7280" }}>CEO: {ceo ? ceo.name_id : "Vacant"}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div className="mono" style={{ fontSize: 20, fontWeight: 600, color: meta.color }}>{dept.ledger?.current || 0}</div>
                  <div style={{ fontSize: 10, color: "#6b7280" }}>BUDGET</div>
                </div>
              </div>
              <div className="card-body" style={{ background: meta.dim, padding: "12px 16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                  <span style={{ color: "#9ca3af" }}>Agents Active</span>
                  <span style={{ color: "#fff", fontWeight: 500 }}>{dept.agents?.length || 0}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginTop: 8 }}>
                  <span style={{ color: "#9ca3af" }}>Transactions</span>
                  <span style={{ color: "#fff", fontWeight: 500 }}>{dept.ledger?.log?.length || 0}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Agents ────────────────────────────────────────────────────────────────────
function Agents({ state, createThread, updateAgent, setView }) {
  const [sel, setSel]   = useState(null);
  const [draft, setDraft] = useState({});
  const [savedField, setSavedField] = useState(null);
  const agent = sel ? state.agents[sel] : null;

  useEffect(() => {
    if (agent) setDraft({ custom_prompt: agent.custom_prompt || "", memory: agent.memory || "" });
  }, [sel]);

  const updateDraft = (field, val) => {
    setDraft(d => ({ ...d, [field]: val }));
  };

  const handleApply = (field) => {
    updateAgent(sel, { [field]: draft[field] });
    setSavedField(field);
    setTimeout(() => setSavedField(null), 2000);
  };

  return (
    <div style={{ display: "flex", gap: 24, height: "100%" }}>
      <div style={{ width: 280, flexShrink: 0, display: "flex", flexDirection: "column", gap: 8 }}>
        <input type="text" placeholder="Search agents…" style={{ marginBottom: 8 }} />
        <div style={{ overflowY: "auto", flex: 1, paddingRight: 4 }}>
          {Object.entries(state.agents).map(([id, a]) => (
            <div key={id} onClick={() => setSel(id)}
              style={{ padding: "12px 16px", background: sel === id ? "#1e1b4b" : "#11141a", border: `1px solid ${sel === id ? "#6366f1" : "#1a1d24"}`, borderRadius: 8, cursor: "pointer", marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: "#e2e8f0" }}>{a.is_ceo ? "★ " : ""}{a.name_id}</span>
                <span style={{ fontSize: 11, color: "#10b981" }}>{a.wallet?.current || 0}pt</span>
              </div>
              <div style={{ fontSize: 11, color: "#6b7280" }}>{a.department || "Freelance"} · {a.mode}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, background: "#11141a", border: "1px solid #1a1d24", borderRadius: 12, overflowY: "auto", padding: 24 }}>
        {!agent ? (
          <div style={{ color: "#6b7280", textAlign: "center", marginTop: 100 }}>Select an agent to view details</div>
        ) : (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #1e222d", paddingBottom: 20, marginBottom: 20 }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                  <h2 style={{ margin: 0, color: "#fff", fontSize: 24 }}>{agent.name_id}</h2>
                  <button className="btn btn-primary" style={{ padding: "4px 12px", fontSize: 11 }} onClick={() => setView("chats")}>PRIVATE CHAT</button>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <span style={{ padding: "4px 8px", background: "#1e222d", borderRadius: 4, fontSize: 11 }}>{agent.department || "No Dept"}</span>
                  <span style={{ padding: "4px 8px", background: "#1e1b4b", color: "#818cf8", borderRadius: 4, fontSize: 11 }}>{agent.is_ceo ? "CEO" : "Agent"}</span>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div className="mono" style={{ fontSize: 28, fontWeight: 700, color: "#10b981" }}>{agent.wallet?.current || 0}</div>
                <div style={{ fontSize: 10, color: "#6b7280", letterSpacing: 1 }}>WALLET PTS</div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
              <div className="card">
                <div className="card-header" style={{ fontSize: 12, fontWeight: 600, color: "#9ca3af" }}>CONFIGURATION</div>
                <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  <div>
                    <label style={{ display: "block", fontSize: 11, marginBottom: 6, color: "#6b7280" }}>Operating Mode</label>
                    <select value={agent.mode} onChange={e => updateAgent(sel, { mode: e.target.value })} style={{ width: "100%" }}>
                      {Object.keys(state.prompts).map(k => <option key={k} value={k}>{k}</option>)}
                    </select>
                    {agent.next_mode && (
                      <div style={{ fontSize: 11, color: "#6366f1", marginTop: 6 }}>→ Self-selecting: <strong>{agent.next_mode}</strong></div>
                    )}
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <label style={{ fontSize: 11, color: "#6b7280" }}>Personal Directives (markdown)</label>
                      <button className="btn btn-soft" onClick={() => handleApply("custom_prompt")} style={{ fontSize: 10, padding: "2px 8px" }}>
                        {savedField === "custom_prompt" ? "✓ Saved!" : "Save Directives"}
                      </button>
                    </div>
                    <MarkdownEditor
                      value={draft.custom_prompt || ""}
                      onChange={val => updateDraft("custom_prompt", val)}
                      rows={6}
                      placeholder="Inject custom markdown-formatted directives for this agent…"
                    />
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6, marginTop: 4 }}>
                      <label style={{ fontSize: 11, color: "#6b7280" }}>Memory Scratchpad</label>
                      <button className="btn btn-soft" onClick={() => handleApply("memory")} style={{ fontSize: 10, padding: "2px 8px" }}>
                        {savedField === "memory" ? "✓ Saved!" : "Save Memory"}
                      </button>
                    </div>
                    <textarea rows={3} value={draft.memory || ""} onChange={e => updateDraft("memory", e.target.value)}
                      placeholder="Agent short-term memory…" style={{ width: "100%", resize: "vertical" }} />
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header" style={{ fontSize: 12, fontWeight: 600, color: "#9ca3af" }}>NEW THREAD</div>
                <div className="card-body">
                  <CreateThreadForm agentId={sel} wallet={agent.wallet?.current} create={createThread} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function CreateThreadForm({ agentId, wallet, create }) {
  const [f, setF] = useState({ topic: "", aim: "Memo" });
  return (
    <div>
      <input placeholder="Thread topic…" value={f.topic} onChange={e => setF({ ...f, topic: e.target.value })} style={{ width: "100%", marginBottom: 12 }} />
      <select value={f.aim} onChange={e => setF({ ...f, aim: e.target.value })} style={{ width: "100%", marginBottom: 16 }}>
        {Object.entries(THREAD_COSTS).map(([k, v]) => <option key={k} value={k}>{k} — {v} pts</option>)}
      </select>
      <button className="btn btn-primary" style={{ width: "100%" }}
        onClick={() => { if (f.topic) { create(agentId, f.topic, f.aim); setF({ topic: "", aim: "Memo" }); } }}>
        Initiate Thread
      </button>
    </div>
  );
}

// ── Prompts ───────────────────────────────────────────────────────────────────
function Prompts({ state, updatePrompt }) {
  const [sel, setSel] = useState(null);
  const [edit, setEdit] = useState({ name: "", system_prompt: "", user_prompt_template: "", custom_directives: "" });
  const [entries, setEntries] = useState([]);
  const [newEntry, setNewEntry] = useState({ title: "", body: "" });
  const [showEntries, setShowEntries] = useState(false);
  const [saved, setSaved] = useState(false);

  const pArr = Object.values(state.prompts || {});

  useEffect(() => {
    if (sel && state.prompts[sel]) {
      const p = state.prompts[sel];
      setEdit({ name: p.name || p.id, system_prompt: p.system_prompt || "", user_prompt_template: p.user_prompt_template || "", custom_directives: p.custom_directives || "" });
    }
  }, [sel]);

  const fetchEntries = async () => {
    const r = await fetch(`${API_BASE}/prompt-entries`);
    setEntries(await r.json());
  };
  useEffect(() => { fetchEntries(); }, []);

  const saveEntry = async () => {
    if (!newEntry.title || !newEntry.body) return;
    await fetch(`${API_BASE}/prompt-entries`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(newEntry) });
    setNewEntry({ title: "", body: "" });
    fetchEntries();
  };
  const deleteEntry = async (id) => {
    await fetch(`${API_BASE}/prompt-entries/${id}`, { method: "DELETE" });
    fetchEntries();
  };

  const handleSave = async () => {
    await updatePrompt(sel, edit);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ display: "flex", gap: 20, height: "100%" }}>
      {/* Mode list */}
      <div style={{ width: 200, flexShrink: 0, overflowY: "auto" }}>
        <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 600, letterSpacing: 1, marginBottom: 10, textTransform: "uppercase" }}>Modes</div>
        {pArr.map(p => (
          <div key={p.id} onClick={() => setSel(p.id)} className="card"
            style={{ cursor: "pointer", marginBottom: 10, borderColor: sel === p.id ? "#6366f1" : "#1a1d24", background: sel === p.id ? "#1e1b4b" : "#11141a" }}>
            <div className="card-body" style={{ padding: "10px 12px" }}>
              <div style={{ fontWeight: 600, color: "#e2e8f0", marginBottom: 2 }}>{p.name || p.id}</div>
              <div style={{ fontSize: 10, color: "#4b5563", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.system_prompt?.slice(0, 50)}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Editor */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {!sel ? (
          <div style={{ textAlign: "center", color: "#6b7280", marginTop: 100 }}>Select a prompt template to edit</div>
        ) : (
          <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div className="card-header">
              <span style={{ fontWeight: 600, color: "#fff", fontSize: 15 }}>Edit: {sel}</span>
              <button className="btn btn-primary" onClick={handleSave}>{saved ? "✓ Saved!" : "Save Changes"}</button>
            </div>
            <div className="card-body" style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 20 }}>

              <div>
                <label style={{ display: "block", fontSize: 12, marginBottom: 6, color: "#9ca3af", fontWeight: 500 }}>Display Name</label>
                <input value={edit.name} onChange={e => setEdit({ ...edit, name: e.target.value })} style={{ width: "100%" }} />
              </div>

              <MarkdownEditor
                label="System Prompt — Identity & Strategy"
                value={edit.system_prompt}
                onChange={val => setEdit({ ...edit, system_prompt: val })}
                rows={8}
                placeholder="# Role\nDescribe who this agent is…"
              />

              <div>
                <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 6 }}>Behavioural rules applied whenever any agent runs in this mode.</div>
                <MarkdownEditor
                  label="Mode Directives — injected every tick"
                  value={edit.custom_directives}
                  onChange={val => setEdit({ ...edit, custom_directives: val })}
                  rows={5}
                  placeholder="- Rule 1\n- Rule 2"
                />
              </div>

              <div>
                <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 6 }}>Appended last — specifies exact reply format and goals.</div>
                <MarkdownEditor
                  label="User Prompt Template — reply format & goals"
                  value={edit.user_prompt_template}
                  onChange={val => setEdit({ ...edit, user_prompt_template: val })}
                  rows={6}
                  placeholder="TASK: Describe 1 action… End with [MEM: note]"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Saved Entries */}
      <div style={{ width: 250, flexShrink: 0, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 600, letterSpacing: 1, textTransform: "uppercase" }}>Saved Entries</div>
          <button className="btn btn-soft" style={{ fontSize: 11, padding: "3px 8px" }} onClick={() => setShowEntries(v => !v)}>{showEntries ? "▲" : "▼ Add"}</button>
        </div>
        {showEntries && (
          <div className="card">
            <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <input placeholder="Entry title…" value={newEntry.title} onChange={e => setNewEntry({ ...newEntry, title: e.target.value })} style={{ width: "100%" }} />
              <textarea rows={3} placeholder="Prompt text…" value={newEntry.body} onChange={e => setNewEntry({ ...newEntry, body: e.target.value })} style={{ width: "100%", resize: "vertical" }} />
              <button className="btn btn-primary" style={{ width: "100%" }} onClick={saveEntry}>Save Entry</button>
            </div>
          </div>
        )}
        <div style={{ flex: 1, overflowY: "auto" }}>
          {entries.length === 0 && <div style={{ fontSize: 12, color: "#4b5563", textAlign: "center", marginTop: 20 }}>No saved entries.</div>}
          {entries.map(e => (
            <div key={e.id} style={{ background: "#11141a", border: "1px solid #1a1d24", borderRadius: 8, padding: 10, marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 600, fontSize: 12, color: "#e2e8f0" }}>{e.title}</span>
                <button onClick={() => deleteEntry(e.id)} style={{ background: "none", border: "none", color: "#6b7280", cursor: "pointer" }}>✕</button>
              </div>
              <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 8, lineHeight: 1.5 }}>{e.body.slice(0, 100)}{e.body.length > 100 ? "…" : ""}</div>
              <button className="btn btn-soft" style={{ fontSize: 11, padding: "3px 10px", width: "100%" }} onClick={() => navigator.clipboard.writeText(e.body)}>Copy</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Threads ───────────────────────────────────────────────────────────────────
function Threads({ state, approveThread, rejectThread, deleteThread, updateThread, postMessage }) {
  const [sel, setSel] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [newTopic, setNewTopic] = useState("");
  
  const tArr   = Object.values(state.threads).reverse();
  const thread = sel ? state.threads[sel] : null;

  useEffect(() => {
    if (thread) {
      setNewTopic(thread.topic);
      setEditMode(false);
    }
  }, [sel]);

  const saveTopic = () => {
    updateThread(sel, { topic: newTopic });
    setEditMode(false);
  };

  return (
    <div style={{ display: "flex", gap: 24, height: "100%" }}>
      <div style={{ width: 320, flexShrink: 0, overflowY: "auto" }}>
        {tArr.map(t => (
          <div key={t.id} onClick={() => setSel(t.id)} className="card"
            style={{ cursor: "pointer", marginBottom: 12, borderColor: sel === t.id ? "#6366f1" : "#1a1d24", background: sel === t.id ? "#1e1b4b" : "#11141a" }}>
            <div className="card-body" style={{ padding: "12px 16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontWeight: 600, color: "#e2e8f0" }}>{t.topic.slice(0, 30)}</span>
                <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: t.status === "OPEN" ? "#064e3b" : "#1e222d", color: t.status === "OPEN" ? "#34d399" : "#9ca3af" }}>{t.status}</span>
              </div>
              <div style={{ fontSize: 11, color: "#6b7280" }}>{t.aim} · {t.point_wallet?.budget || 0}pt budget</div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
        {!thread ? <div style={{ textAlign: "center", color: "#6b7280", marginTop: 100 }}>Select a thread</div> : (
          <>
            <div className="card">
              <div className="card-body">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    {editMode ? (
                      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                        <input value={newTopic} onChange={e => setNewTopic(e.target.value)} style={{ fontSize: 20, fontWeight: 700, width: "100%", background: "#0b0c10" }} />
                        <button className="btn btn-primary" onClick={saveTopic}>Save</button>
                        <button className="btn btn-soft" onClick={() => setEditMode(false)}>Cancel</button>
                      </div>
                    ) : (
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <h2 style={{ margin: 0, color: "#fff" }}>{thread.topic}</h2>
                        <button onClick={() => setEditMode(true)} style={{ background: "none", border: "none", color: "#6366f1", cursor: "pointer", fontSize: 16 }}>✎</button>
                      </div>
                    )}
                    <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 8, display: "flex", gap: 16 }}>
                      <span>Owner: <b style={{ color: "#e2e8f0" }}>{state.agents[thread.owner_agent]?.name_id}</b></span>
                      <span>Dept: <b style={{ color: DEPT_META[thread.owner_department]?.color || "#fff" }}>{thread.owner_department || "none"}</b></span>
                      <span>Aim: <b style={{ color: "#6366f1" }}>{thread.aim}</b></span>
                    </div>
                  </div>
                  <div style={{ textAlign: "right", minWidth: 120 }}>
                    <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: "#10b981" }}>{thread.point_wallet?.budget || 0} pt</div>
                    <div style={{ fontSize: 10, color: "#6b7280", letterSpacing: 1 }}>CURRENT BUDGET</div>
                    <div style={{ display: "flex", gap: 8, marginTop: 12, justifyContent: "flex-end" }}>
                      {(thread.status === "OPEN" || thread.status === "ACTIVE") && (
                        <>
                          <button className="btn" style={{ background: "#064e3b", color: "#34d399", fontSize: 11, padding: "5px 12px" }} onClick={() => approveThread(sel)}>Approve</button>
                          <button className="btn" style={{ background: "#7f1d1d", color: "#f87171", fontSize: 11, padding: "5px 12px" }} onClick={() => rejectThread(sel)}>Reject</button>
                        </>
                      )}
                      <button className="btn" style={{ background: "#1a1d24", color: "#6b7280", fontSize: 11, padding: "5px 12px" }} onClick={() => deleteThread(sel)}>Delete</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20, flex: 1, overflow: "hidden" }}>
              {/* MESSAGES */}
              <div className="card" style={{ display: "flex", flexDirection: "column" }}>
                <div className="card-header" style={{ fontSize: 11, fontWeight: 800, color: "#6366f1", letterSpacing: 1.5 }}>DISCUSSION LOG</div>
                <div className="card-body" style={{ flex: 1, overflowY: "auto", background: "#08090c" }}>
                  {thread.messages_log?.filter(m => !m.what.startsWith("INVESTMENT")).map((m, i) => (
                    <div key={i} style={{ marginBottom: 16 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, color: "#818cf8", fontSize: 12 }}>{state.agents[m.who]?.name_id || m.who}</span>
                        <span className="mono" style={{ fontSize: 10, color: "#4b5563" }}>{hhmm(m.when)}</span>
                      </div>
                      <div style={{ color: "#e2e8f0", backgroundColor: "#11141a", padding: "12px 16px", borderRadius: "0 10px 10px 10px", fontSize: 13, border: "1px solid #1a1d24", lineHeight: 1.5 }}
                         dangerouslySetInnerHTML={{ __html: renderMd(m.what) }} />
                    </div>
                  ))}
                </div>
              </div>

              {/* FINANCIAL LEDGER */}
              <div className="card" style={{ display: "flex", flexDirection: "column" }}>
                <div className="card-header" style={{ fontSize: 11, fontWeight: 800, color: "#10b981", letterSpacing: 1.5 }}>FINANCIAL LEDGER</div>
                <div className="card-body" style={{ flex: 1, overflowY: "auto", background: "#0a0b0e" }}>
                  {thread.messages_log?.filter(m => m.points !== 0).reverse().map((m, i) => (
                    <div key={i} style={{ padding: "10px 0", borderBottom: "1px solid #161922" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: "#e2e8f0" }}>{m.what.replace("INVESTMENT: ", "")}</span>
                        <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: m.points > 0 ? "#10b981" : "#ef4444" }}>
                          {m.points > 0 ? "+" : ""}{m.points} pt
                        </span>
                      </div>
                      <div style={{ fontSize: 10, color: "#4b5563" }}>
                        {hhmm(m.when)} · {state.agents[m.who]?.name_id || m.who}
                      </div>
                    </div>
                  ))}
                  {(!thread.messages_log?.some(m => m.points !== 0)) && (
                    <div style={{ textAlign: "center", color: "#374151", fontSize: 12, marginTop: 40 }}>No financial history</div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Departments ───────────────────────────────────────────────────────────────
function Departments({ state }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 20 }}>
      {Object.entries(DEPT_META).map(([id, meta]) => {
        const dept = state.departments[id];
        if (!dept) return null;
        const allA   = dept.agents?.map(aid => state.agents[aid]).filter(Boolean) || [];
        const ceo    = allA.find(a => a.is_ceo);
        const members = allA.filter(a => !a.is_ceo);
        return (
          <div key={id} className="card" style={{ borderTop: `3px solid ${meta.color}` }}>
            <div className="card-header" style={{ gap: 10 }}>
              <span style={{ fontSize: 18 }}>{meta.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, color: "#fff", fontSize: 15 }}>{meta.name}</div>
                <div style={{ fontSize: 11, color: meta.color }}>{id}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: meta.color }}>{dept.ledger?.current ?? 0}</div>
                <div style={{ fontSize: 10, color: "#6b7280" }}>BUDGET PTS</div>
              </div>
            </div>
            <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {ceo && (
                <div style={{ background: "#0a0b0e", border: `1px solid ${meta.color}44`, borderRadius: 8, padding: "10px 14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <span style={{ fontSize: 10, fontWeight: 700, color: meta.color, letterSpacing: 1 }}>CEO  </span>
                      <span style={{ fontWeight: 600, color: "#fff", fontSize: 13 }}>{ceo.name_id}</span>
                    </div>
                    <span style={{ fontSize: 11, color: "#818cf8", background: "#1e1b4b", padding: "2px 8px", borderRadius: 4 }}>{ceo.mode}</span>
                  </div>
                  <div style={{ display: "flex", gap: 16, marginTop: 6, fontSize: 11, color: "#6b7280" }}>
                    <span>Wallet: <span style={{ color: "#10b981" }}>{ceo.wallet?.current ?? 0} pts</span></span>
                    <span>Ticks: {ceo.ticks}s</span>
                    {ceo.next_mode && <span style={{ color: "#6366f1" }}>→ {ceo.next_mode}</span>}
                  </div>
                  {ceo.memory && <div style={{ marginTop: 6, fontSize: 11, color: "#4b5563", fontStyle: "italic" }}>💭 {ceo.memory.slice(0, 80)}</div>}
                </div>
              )}
              {members.length > 0 && <div style={{ fontSize: 10, color: "#374151", fontWeight: 600, letterSpacing: 1 }}>MEMBERS</div>}
              {members.map(a => (
                <div key={a.id} style={{ background: "#0d0f14", border: "1px solid #1a1d24", borderRadius: 6, padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 500, color: "#e2e8f0", fontSize: 12 }}>{a.name_id}</div>
                    <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>
                      Wallet: <span style={{ color: "#10b981" }}>{a.wallet?.current ?? 0}</span> · Tick: {a.ticks}s
                    </div>
                  </div>
                  <span style={{ fontSize: 11, color: "#9ca3af", background: "#1a1d24", padding: "2px 8px", borderRadius: 4 }}>{a.mode}</span>
                </div>
              ))}
              {(dept.ledger?.log?.length > 0) && (
                <div style={{ marginTop: 4, borderTop: "1px solid #1a1d24", paddingTop: 8 }}>
                  <div style={{ fontSize: 10, color: "#374151", fontWeight: 600, letterSpacing: 1, marginBottom: 6 }}>RECENT LEDGER</div>
                  {dept.ledger.log.slice(-4).reverse().map((l, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#6b7280", marginBottom: 3 }}>
                      <span>{l.who}</span>
                      <span style={{ color: l.amount < 0 ? "#ef4444" : "#10b981", fontFamily: "monospace" }}>{l.amount > 0 ? `+${l.amount}` : l.amount}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Founder / Economy ─────────────────────────────────────────────────────────
function Founder({ state, addDeptPoints }) {
  return (
    <div className="card">
      <div className="card-header" style={{ fontSize: 14, fontWeight: 600, color: "#fff" }}>Department Treasuries</div>
      <div className="card-body">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }}>
          {Object.entries(DEPT_META).map(([id, meta]) => {
            const current = state.departments[id]?.ledger?.current || 0;
            return (
              <div key={id} style={{ background: "#0a0b0e", border: "1px solid #1a1d24", borderRadius: 8, padding: 16 }}>
                <div style={{ color: meta.color, fontWeight: 600, marginBottom: 12 }}>{meta.name}</div>
                <div className="mono" style={{ fontSize: 24, color: "#fff", marginBottom: 16 }}>{current} pts</div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-soft" style={{ flex: 1 }} onClick={() => addDeptPoints(id, 100)}>+100</button>
                  <button className="btn btn-soft" style={{ flex: 1 }} onClick={() => addDeptPoints(id, 500)}>+500</button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Chats ─────────────────────────────────────────────────────────────────────
function Chats({ state, fetchState }) {
  const [sel, setSel]       = useState(null);
  const [msg, setMsg]       = useState("");
  const [loading, setLoading] = useState(false);

  const chatThreads   = Object.values(state.threads).filter(t => t.aim === "Chat");
  const agents        = Object.values(state.agents);
  const selectedAgent = state.agents[sel];
  const activeThread  = chatThreads.find(t => t.owner_agent == sel);

  const sendChat = async () => {
    if (!sel || !msg.trim() || loading) return;
    setLoading(true);
    try {
      await fetch(`${API_BASE}/agents/${sel}/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: msg }) });
      setMsg(""); fetchState();
    } finally { setLoading(false); }
  };

  return (
    <div style={{ display: "flex", gap: 20, height: "calc(100vh - 160px)" }}>
      <div style={{ width: 240, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 600, letterSpacing: 1, textTransform: "uppercase" }}>Direct Message</div>
        {agents.map(a => (
          <div key={a.id} onClick={() => setSel(a.id)} className="card"
            style={{ cursor: "pointer", borderColor: sel === a.id ? "#6366f1" : "transparent", background: sel === a.id ? "#1e1b4b" : "#11141a" }}>
            <div className="card-body" style={{ padding: "10px 14px", display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: DEPT_META[a.department]?.color || "#6b7280" }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{a.name_id}</div>
                <div style={{ fontSize: 10, color: "#6b7280" }}>{a.mode}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }} className="card">
        {!sel ? (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", color: "#4b5563" }}>
            <div style={{ fontSize: 40, marginBottom: 10 }}>🗯️</div>
            <div>Select an agent to begin a direct conversation</div>
          </div>
        ) : (
          <>
            <div className="card-header" style={{ justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>{selectedAgent.name_id}</div>
                <span style={{ fontSize: 11, color: "#6b7280", background: "#1a1d24", padding: "2px 8px", borderRadius: 4 }}>{selectedAgent.mode}</span>
              </div>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
              {!activeThread && <div style={{ textAlign: "center", color: "#4b5563", fontSize: 12, marginTop: 40 }}>No previous conversation.</div>}
              {activeThread?.messages_log.map((m, i) => (
                <div key={i} style={{
                  alignSelf: m.who === "FOUNDER" ? "flex-end" : "flex-start",
                  maxWidth: "80%",
                  background: m.who === "FOUNDER" ? "#4f46e5" : "#1a1d24",
                  color: "#fff", padding: "10px 14px",
                  borderRadius: m.who === "FOUNDER" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                  fontSize: 13, lineHeight: 1.5,
                }}>
                  <div style={{ fontSize: 10, opacity: 0.6, marginBottom: 4 }}>{m.who === "FOUNDER" ? "YOU" : selectedAgent.name_id}</div>
                  <div dangerouslySetInnerHTML={{ __html: renderMd(m.what) }} />
                </div>
              ))}
              {loading && (
                <div style={{ alignSelf: "flex-start", background: "#1a1d24", padding: "10px 14px", borderRadius: "12px 12px 12px 2px", fontSize: 12, color: "#6b7280" }}>
                  {selectedAgent.name_id} is thinking…
                </div>
              )}
            </div>
            <div style={{ padding: 16, borderTop: "1px solid #1a1d24", display: "flex", gap: 10 }}>
              <input placeholder={`Message ${selectedAgent.name_id}…`} value={msg} onChange={e => setMsg(e.target.value)} onKeyDown={e => e.key === "Enter" && sendChat()} style={{ flex: 1 }} />
              <button className="btn btn-primary" onClick={sendChat} disabled={loading || !msg.trim()}>{loading ? "…" : "Send"}</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ToolTesterModal({ tool, agents, onClose }) {
  const [agentId, setAgentId] = useState(agents[0]?.id || "");
  const [args, setArgs] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const invoke = async () => {
    setLoading(true);
    setResult(null);
    try {
      const r = await fetch(`${API_BASE}/tools/${tool.id}/invoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, args })
      });
      const data = await r.json();
      setResult(data.result || data.error || "No result returned.");
    } catch (e) {
      setResult("Error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
      background: "rgba(0,0,0,0.8)", backdropFilter: "blur(4px)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
    }} onClick={onClose}>
      <div className="card" style={{ width: 440, padding: 0, border: "1px solid #312e81", boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)" }} onClick={e => e.stopPropagation()}>
        <div className="card-header" style={{ justifyContent: "space-between", borderBottom: "1px solid #1a1d24", padding: "16px 20px" }}>
          <div>
            <h3 style={{ margin: 0, color: "#fff", fontSize: 16 }}>Test: {tool.name}</h3>
            <div className="mono" style={{ fontSize: 10, color: "#6366f1", marginTop: 2 }}>{tool.id}</div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#6b7280", fontSize: 20, cursor: "pointer" }}>✕</button>
        </div>
        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 20, padding: 24 }}>
          <div>
            <label style={{ display: "block", fontSize: 10, color: "#6366f1", fontWeight: 800, letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>Execute as Agent</label>
            <select value={agentId} onChange={e => setAgentId(e.target.value)} style={{ width: "100%", background: "#0b0c10", border: "1px solid #1e222d" }}>
              {agents.map(a => <option key={a.id} value={a.id}>{a.name_id} ({a.wallet?.current} pts)</option>)}
            </select>
          </div>
          <div>
            <label style={{ display: "block", fontSize: 10, color: "#6366f1", fontWeight: 800, letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>Arguments (CSV)</label>
            <input value={args} onChange={e => setArgs(e.target.value)} placeholder="e.g. topic, aim" style={{ width: "100%", background: "#0b0c10", border: "1px solid #1e222d" }} />
            <div style={{ fontSize: 10, color: "#4b5563", marginTop: 6, fontStyle: "italic" }}>
              Format: {tool.description.match(/\((.*?)\)/)?.[1] || "no arguments required"}
            </div>
          </div>
          
          <button className="btn btn-primary" onClick={invoke} disabled={loading || !agentId} style={{ height: 42, width: "100%", marginTop: 8 }}>
            {loading ? "Invoking Tool..." : "Run Manual Test"}
          </button>

          {result !== null && (
            <div style={{ marginTop: 12, borderTop: "1px solid #1a1d24", paddingTop: 16 }}>
              <label style={{ display: "block", fontSize: 10, color: "#10b981", fontWeight: 800, letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>Execution Result</label>
              <div style={{
                background: "#08090c", border: "1px solid #1a1d24", borderRadius: 8,
                padding: "12px 16px", fontSize: 12, color: "#e2e8f0", fontFamily: "monospace",
                lineHeight: 1.6, maxHeight: 180, overflowY: "auto", whiteSpace: "pre-wrap"
              }}>
                {result}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Tools ─────────────────────────────────────────────────────────────────────
function Tools({ state, fetchState }) {
  const tools  = Object.values(state.tools || {});
  const agents = Object.values(state.agents || {});
  const [instr, setInstr] = useState(state.settings?.tools_instruction_prefix || "");
  const [testTool, setTestTool] = useState(null);

  useEffect(() => {
    if (state.settings?.tools_instruction_prefix !== undefined) setInstr(state.settings.tools_instruction_prefix);
  }, [state.settings?.tools_instruction_prefix]);

  const toggleTool = async (tid, current) => {
    await fetch(`${API_BASE}/tools/${tid}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled: !current }) });
    fetchState();
  };
  const saveInstr = async () => {
    await fetch(`${API_BASE}/settings/tools_instruction_prefix`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value: instr }) });
    fetchState();
  };

  const TOOL_ICONS = { modify_own_tick: "⏱️", get_time: "🕐", get_weather: "🌤️", get_news: "📰" };
  const enabledTools = tools.filter(t => t.enabled);
  const previewText  = `${instr}\n\n${enabledTools.map(t => `- ${t.description}`).join("\n") || "No tools."}`;

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ display: "flex", gap: 32, marginBottom: 40, alignItems: "stretch" }}>
        <div style={{ flex: 1 }}>
          <h1 style={{ color: "#fff", fontSize: 22, marginBottom: 8 }}>Agent Capabilities</h1>
          <p style={{ color: "#6b7280", fontSize: 13, marginBottom: 20 }}>Define the global tool instructions and toggle individual tools on/off.</p>
          <div className="card" style={{ padding: 20 }}>
            <label style={{ display: "block", fontSize: 10, color: "#6366f1", fontWeight: 800, letterSpacing: 1.5, marginBottom: 10, textTransform: "uppercase" }}>Global Tool Instruction Prompt</label>
            <textarea value={instr} onChange={e => setInstr(e.target.value)} style={{ height: 120, width: "100%", fontSize: 13, padding: 12, marginBottom: 14, background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0", borderRadius: 8 }} />
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button className="btn btn-primary" onClick={saveInstr} disabled={instr === state.settings?.tools_instruction_prefix}>Save Prompt</button>
            </div>
          </div>
        </div>
        <div style={{ width: 420 }}>
          <label style={{ display: "block", fontSize: 10, color: "#9ca3af", fontWeight: 800, letterSpacing: 1.5, marginBottom: 10, textTransform: "uppercase" }}>Agent Context Preview</label>
          <div className="card" style={{ flex: 1, background: "#0b0c10", padding: 16, border: "1px dashed #1e222d", position: "relative", height: "calc(100% - 26px)" }}>
            <div style={{ position: "absolute", top: 8, right: 10, fontSize: 9, color: "#4b5563", background: "#11141a", padding: "2px 6px", borderRadius: 4 }}>READ ONLY</div>
            <pre style={{ whiteSpace: "pre-wrap", fontSize: 11, color: "#6b7280", lineHeight: 1.6, margin: 0, fontFamily: "monospace" }}>{previewText}</pre>
          </div>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 20 }}>
        {tools.map(t => (
          <div key={t.id} className="card" style={{ opacity: t.enabled ? 1 : 0.55 }}>
            <div className="card-header" style={{ justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: t.enabled ? "#1e1b4b" : "#1a1d24", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ fontSize: 16 }}>{TOOL_ICONS[t.id] || "🔧"}</span>
                </div>
                <div>
                  <div style={{ fontWeight: 700, color: "#fff" }}>{t.name}</div>
                  <div className="mono" style={{ fontSize: 10, color: "#6366f1" }}>{t.id}</div>
                </div>
              </div>
              <div onClick={() => toggleTool(t.id, t.enabled)}
                style={{ width: 44, height: 22, borderRadius: 100, background: t.enabled ? "#6366f1" : "#1a1d24", position: "relative", cursor: "pointer", transition: "all 0.3s", border: "1px solid #1e222d" }}>
                <div style={{ width: 16, height: 16, borderRadius: "50%", background: "#fff", position: "absolute", top: 2, left: t.enabled ? 24 : 3, transition: "all 0.3s" }} />
              </div>
            </div>
            <div className="card-body">
              <div style={{ fontSize: 12, color: "#9ca3af", lineHeight: 1.6, marginBottom: 12 }}>{t.description}</div>
              <div style={{ display: "flex", justifyContent: "space-between", paddingTop: 12, borderTop: "1px solid #1a1d24", alignItems: "center" }}>
                <span style={{ fontSize: 11, color: "#4b5563" }}>Status: <span style={{ fontWeight: 600, color: t.enabled ? "#10b981" : "#ef4444" }}>{t.enabled ? "ACTIVE" : "DISABLED"}</span></span>
                <button className="btn btn-soft" style={{ fontSize: 10, padding: "4px 10px" }} onClick={() => setTestTool(t)}>Test Tool</button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {testTool && <ToolTesterModal tool={testTool} agents={agents} onClose={() => setTestTool(null)} />}
    </div>
  );
}

// ── Settings ──────────────────────────────────────────────────────────────────
function Settings({ state, updateSetting }) {
  const [ollamaModel,     setOllamaModel]     = useState("");
  const [ollamaServer,    setOllamaServer]    = useState("");
  const [availableModels, setAvailableModels] = useState([]);
  const [loadingModels,   setLoadingModels]   = useState(false);
  const [testResult,      setTestResult]      = useState(null);
  const [testing,         setTesting]         = useState(false);
  const [saved,           setSaved]           = useState(false);

  useEffect(() => {
    if (state.settings) {
      if (state.settings.ollama_model  !== undefined) setOllamaModel(state.settings.ollama_model);
      if (state.settings.ollama_server !== undefined) setOllamaServer(state.settings.ollama_server);
    }
  }, [state.settings]);

  const fetchModels = async () => {
    setLoadingModels(true);
    try {
      const r = await fetch(`${API_BASE}/ollama-models`);
      const b = await r.json();
      if (b.status === "success") setAvailableModels(b.models);
    } catch {}
    setLoadingModels(false);
  };
  useEffect(() => { fetchModels(); }, []);

  const saveSettings = async () => {
    await updateSetting("ollama_model", ollamaModel);
    await updateSetting("ollama_server", ollamaServer);
    setSaved(true); setTimeout(() => setSaved(false), 2000);
  };

  const testConnection = async () => {
    setTesting(true); setTestResult(null);
    try {
      const r = await fetch(`${API_BASE}/test-ollama`);
      setTestResult(await r.json());
    } catch (e) {
      setTestResult({ status: "error", message: e.message });
    }
    setTesting(false);
  };

  return (
    <div className="card" style={{ maxWidth: 640, margin: "0 auto" }}>
      <div className="card-header" style={{ fontSize: 14, fontWeight: 600, color: "#fff" }}>Global Settings</div>
      <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div>
          <label style={{ display: "block", fontSize: 12, marginBottom: 6, color: "#9ca3af", fontWeight: 500 }}>Ollama Server URL</label>
          <input value={ollamaServer} onChange={e => setOllamaServer(e.target.value)} placeholder="http://localhost:11434" style={{ width: "100%" }} />
        </div>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <label style={{ fontSize: 12, color: "#9ca3af", fontWeight: 500 }}>Active Model</label>
            <button className="btn btn-soft" style={{ fontSize: 11, padding: "3px 10px" }} onClick={fetchModels} disabled={loadingModels}>
              {loadingModels ? "…" : "↻ Refresh"}
            </button>
          </div>
          {availableModels.length > 0 ? (
            <select value={ollamaModel} onChange={e => setOllamaModel(e.target.value)} style={{ width: "100%" }}>
              {availableModels.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          ) : (
            <input value={ollamaModel} onChange={e => setOllamaModel(e.target.value)} placeholder="e.g. gemma3:4b" style={{ width: "100%" }} />
          )}
          <div style={{ fontSize: 11, color: "#4b5563", marginTop: 6 }}>Model used for all agent reasoning loops. Default: gemma3:4b</div>
        </div>
        <button className="btn btn-primary" onClick={saveSettings} style={{ minWidth: 120 }}>
          {saved ? "✓ Saved!" : "Save Settings"}
        </button>

        <div style={{ borderTop: "1px solid #1a1d24", paddingTop: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <div style={{ fontWeight: 500, color: "#e2e8f0", fontSize: 14 }}>Connection Test</div>
              <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>Sends a live prompt to verify server + model. May take 20–90s on cold start.</div>
            </div>
            <button className="btn btn-soft" onClick={testConnection} disabled={testing} style={{ minWidth: 130, flexShrink: 0, marginLeft: 16 }}>
              {testing ? (
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ display: "inline-block", width: 10, height: 10, border: "2px solid #374151", borderTopColor: "#818cf8", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
                  Waiting…
                </span>
              ) : "▶ Test Connection"}
            </button>
          </div>
          {testResult && (
            <div style={{ padding: "12px 16px", borderRadius: 8, background: testResult.status === "success" ? "#064e3b" : "#450a0a", border: `1px solid ${testResult.status === "success" ? "#059669" : "#991b1b"}` }}>
              <div style={{ color: testResult.status === "success" ? "#34d399" : "#fca5a5", fontWeight: 700, fontSize: 12, marginBottom: 6 }}>
                {testResult.status === "success" ? "✓ CONNECTION OK" : "✗ FAILED"}
              </div>
              <div style={{ color: testResult.status === "success" ? "#a7f3d0" : "#fecaca", fontSize: 12 }}>{testResult.message}</div>
              {testResult.llm_response && (
                <div style={{ marginTop: 12, padding: "10px 14px", background: "#065f46", border: "1px solid #047857", borderRadius: 6, color: "#d1fae5", fontSize: 12, lineHeight: 1.6 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, marginBottom: 6, opacity: 0.7 }}>LLM RESPONSE</div>
                  {testResult.llm_response}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
