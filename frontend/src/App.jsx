import { useState, useEffect, useCallback } from "react";
import './index.css';

const DEPT_META = {
  HF: { name: "Health & Wellness", color: "#4ade80", dim: "#052e16", icon: "🌱" },
  ING: { name: "Engineering", color: "#22d3ee", dim: "#0c2030", icon: "⚙️" },
  STP: { name: "Strategic Planning", color: "#fb923c", dim: "#2d1500", icon: "📊" },
  UIT: { name: "Useful Intelligence", color: "#c084fc", dim: "#1e0a30", icon: "🧠" },
  FIN: { name: "Financing", color: "#fbbf24", dim: "#1c1600", icon: "💰" },
};

const THREAD_COSTS = { Memo: 25, Strategy: 100, Endeavor: 100 };
const DEPT_DAILY = 500;
const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/ws";

const mkId = () => Math.random().toString(36).slice(2, 8).toUpperCase();
const hhmm = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

export default function App() {
  const [state, setState] = useState({ heartbeat: 0, departments: {}, agents: {}, threads: {}, prompts: {}, settings: {} });
  const [feed, setFeed] = useState([]);
  const [view, setView] = useState("dashboard"); // dashboard, agents, threads, founder, prompts, settings

  const fetchState = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/state`);
      const body = await r.json();
      setState(s => ({ ...s, ...body }));
    } catch (e) { console.error('fetch state error', e); }
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
        setFeed(f => [{ id: mkId(), time: hhmm(new Date().toISOString()), agent: item.agent, dept: item.dept, msg: item.msg, type: "action" }, ...f].slice(0, 50));
        fetchState();
      }
    };
    return () => ws.close();
  }, [fetchState]);

  // Actions
  const createThread = useCallback(async (ownerAgentId, topic, aim) => {
    await fetch(`${API_BASE}/threads`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ topic, aim, owner_agent_id: ownerAgentId }) });
    fetchState();
  }, [fetchState]);

  const approveThread = useCallback(async (tid) => {
    await fetch(`${API_BASE}/threads/${tid}/approve`, { method: "POST" });
    fetchState();
  }, [fetchState]);

  const rejectThread = useCallback(async (tid) => {
    await fetch(`${API_BASE}/threads/${tid}/reject`, { method: "POST" });
    fetchState();
  }, [fetchState]);

  const postMessage = useCallback(async (tid, agentId, content) => {
    await fetch(`${API_BASE}/threads/${tid}/messages`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ who: agentId, what: content }) });
    fetchState();
  }, [fetchState]);

  const updatePrompt = useCallback(async (pid, payload) => {
    await fetch(`${API_BASE}/prompts/${pid}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    fetchState();
  }, [fetchState]);

  const updateAgent = useCallback(async (aid, payload) => {
    await fetch(`${API_BASE}/agents/${aid}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
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
    { id: "dashboard", label: "Dashboard", icon: "⊞" },
    { id: "agents", label: "Agents", icon: "👥" },
    { id: "departments", label: "Departments", icon: "🏢" },
    { id: "chats", label: "Agent Chats", icon: "🗯️" },
    { id: "threads", label: "Threads", icon: "💬" },
    { id: "tools", label: "Agent Tools", icon: "🛠️" },
    { id: "founder", label: "Economy", icon: "👑" },
    { id: "prompts", label: "Prompt Design", icon: "✨" },
    { id: "settings", label: "Settings", icon: "⚙️" },
  ];

  return (
    <div className="app-container">
      {/* LEFT SIDEBAR */}
      <div className="sidebar">
        <div className="logo-area">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, background: "linear-gradient(135deg, #6366f1, #a855f7)", borderRadius: 8 }} className="flex-center">
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
            <div key={l.id} className={`nav-link ${view === l.id ? 'active' : ''}`} onClick={() => setView(l.id)}>
              <span style={{ marginRight: 10, fontSize: 14 }}>{l.icon}</span>
              {l.label}
            </div>
          ))}

          <div className="nav-header" style={{ marginTop: 24 }}>DEPARTMENTS</div>
          {Object.entries(DEPT_META).map(([id, meta]) => {
            const d = state.departments[id];
            const pts = d?.ledger?.current || 0;
            return (
              <div key={id} className="nav-link" style={{ justifyContent: "space-between", cursor: "pointer" }}
                onClick={() => setView("departments")}>
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
            <span style={{ color: "#e2e8f0", fontSize: 12, fontWeight: 500 }}>Online & Linked</span>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT CENTER */}
      <div className="main-content">
        <div style={{ height: 60, borderBottom: "1px solid #1a1d24", display: "flex", alignItems: "center", padding: "0 24px", justifyContent: "space-between" }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: "#fff", textTransform: "capitalize" }}>
            {view.replace('-', ' ')}
          </div>
          <div>
            <div className="mono" style={{ background: "#11141a", border: "1px solid #1e222d", padding: "6px 12px", borderRadius: 6, fontSize: 12, color: "#8b92a5" }}>
              Heartbeat: <span style={{ color: "#6366f1", fontWeight: 700 }}>{String(state.heartbeat).padStart(4, '0')}</span>/3600
            </div>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
          {view === "dashboard" && <Dashboard state={state} />}
          {view === "agents" && <Agents state={state} createThread={createThread} updateAgent={updateAgent} setView={setView} />}
          {view === "departments" && <Departments state={state} />}
          {view === "chats" && <Chats state={state} fetchState={fetchState} />}
          {view === "threads" && <Threads state={state} approveThread={approveThread} rejectThread={rejectThread} postMessage={postMessage} />}
          {view === "tools" && <Tools state={state} fetchState={fetchState} />}
          {view === "founder" && <Founder state={state} addDeptPoints={addDeptPoints} approveThread={approveThread} rejectThread={rejectThread} />}
          {view === "prompts" && <Prompts state={state} updatePrompt={updatePrompt} />}
          {view === "settings" && <Settings state={state} updateSetting={updateSetting} />}
        </div>
      </div>

      {/* RIGHT UTILITY PANEL */}
      <div className="right-panel">
        <div style={{ padding: 16, borderBottom: "1px solid #1a1d24", background: "#0b0c10" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#9ca3af", letterSpacing: 1, textTransform: "uppercase" }}>Activity Feed</div>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: 12 }}>
          {feed.length === 0 && <div style={{ fontSize: 12, color: "#4b5563", textAlign: "center", marginTop: 40 }}>Waiting for ticks...</div>}
          {feed.map(f => (
            <div key={f.id} className="pill" style={{ background: "#11141a", border: "1px solid #1a1d24", borderRadius: 8, padding: 10, marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: f.dept ? DEPT_META[f.dept]?.color : "#818cf8" }}>{f.agent}</span>
                <span className="mono" style={{ fontSize: 10, color: "#4b5563" }}>{f.time}</span>
              </div>
              <div style={{ fontSize: 11, color: "#9ca3af", lineHeight: 1.5 }}>{f.msg}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------- VIEWS ----------------

function Dashboard({ state }) {
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 20 }}>
        {Object.entries(DEPT_META).map(([id, meta]) => {
          const dept = state.departments[id];
          if (!dept) return null;
          const ceo = dept.ceo_name_id ? state.agents[dept.ceo_name_id] : null;

          return (
            <div key={id} className="card glow-border" style={{ '--glow': meta.color }}>
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

function Agents({ state, createThread, updateAgent, setView }) {
  const [sel, setSel] = useState(null);
  const agent = sel ? state.agents[sel] : null;

  return (
    <div style={{ display: "flex", gap: 24, height: "100%" }}>
      <div style={{ width: 280, flexShrink: 0, display: "flex", flexDirection: "column", gap: 8 }}>
        <input type="text" placeholder="Search agents..." style={{ marginBottom: 8 }} />
        <div style={{ overflowY: "auto", flex: 1, paddingRight: 4 }}>
          {Object.entries(state.agents).map(([id, a]) => (
            <div key={id} onClick={() => setSel(id)}
              style={{
                padding: "12px 16px", background: sel === id ? "#1e1b4b" : "#11141a",
                border: `1px solid ${sel === id ? "#6366f1" : "#1a1d24"}`, borderRadius: 8, cursor: "pointer", marginBottom: 8,
                transition: "all 0.2s"
              }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: sel === id ? "#fff" : "#e2e8f0" }}>{a.is_ceo ? '★ ' : ''}{a.name_id}</span>
                <span style={{ fontSize: 11, color: "#10b981" }}>{a.wallet?.current || 0}pt</span>
              </div>
              <div style={{ fontSize: 11, color: "#6b7280" }}>
                Dec 12 • {a.department || "Freelance"} • {a.mode}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, background: "#11141a", border: "1px solid #1a1d24", borderRadius: 12, overflowY: "auto", padding: 24 }}>
        {!agent ? <div style={{ color: "#6b7280", textAlign: "center", marginTop: 100 }}>Select an agent to view details</div> : (
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
                <div className="card-body">
                  <label style={{ display: "block", fontSize: 11, marginBottom: 6, color: "#6b7280" }}>Operating Mode</label>
                  <select value={agent.mode} onChange={e => updateAgent(sel, { mode: e.target.value })} style={{ width: "100%", marginBottom: 4 }}>
                    {Object.keys(state.prompts).map(k => <option key={k} value={k}>{k}</option>)}
                  </select>
                  {agent.next_mode && (
                    <div style={{ fontSize: 11, color: "#6366f1", marginBottom: 16, display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ opacity: 0.6 }}>→ Self-selecting next:</span>
                      <span style={{ fontWeight: 600 }}>{agent.next_mode}</span>
                    </div>
                  )}
                  {!agent.next_mode && <div style={{ marginBottom: 16 }} />}

                  <label style={{ display: "block", fontSize: 11, marginBottom: 6, color: "#6b7280" }}>Personal Directives</label>
                  <textarea rows={4} value={agent.custom_prompt || ""} onChange={e => updateAgent(sel, { custom_prompt: e.target.value })} placeholder="Inject specific rules to this agent..." style={{ width: "100%", marginBottom: 16, resize: "vertical" }} />

                  <label style={{ display: "block", fontSize: 11, marginBottom: 6, color: "#6b7280" }}>Memory Scratchpad</label>
                  <textarea rows={3} value={agent.memory || ""} onChange={e => updateAgent(sel, { memory: e.target.value })} placeholder="Agent's short-term memory..." style={{ width: "100%", resize: "vertical" }} />
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
      <input placeholder="Thread topic..." value={f.topic} onChange={e => setF({ ...f, topic: e.target.value })} style={{ width: "100%", marginBottom: 12 }} />
      <select value={f.aim} onChange={e => setF({ ...f, aim: e.target.value })} style={{ width: "100%", marginBottom: 16 }}>
        {Object.entries(THREAD_COSTS).map(([k, v]) => <option key={k} value={k}>{k} — {v} pts</option>)}
      </select>
      <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => { if (f.topic) create(agentId, f.topic, f.aim); setF({ topic: "", aim: "Memo" }); }}>
        Initiate Thread
      </button>
    </div>
  );
}

function Threads({ state, approveThread, rejectThread, postMessage }) {
  const [sel, setSel] = useState(null);
  const tArr = Object.values(state.threads).reverse();
  const thread = sel ? state.threads[sel] : null;

  return (
    <div style={{ display: "flex", gap: 24, height: "100%" }}>
      <div style={{ width: 320, flexShrink: 0, overflowY: "auto" }}>
        {tArr.map(t => (
          <div key={t.id} onClick={() => setSel(t.id)} className="card" style={{ cursor: "pointer", marginBottom: 12, borderColor: sel === t.id ? "#6366f1" : "#1a1d24", background: sel === t.id ? "#1e1b4b" : "#11141a" }}>
            <div className="card-body" style={{ padding: "12px 16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontWeight: 600, color: "#e2e8f0" }}>{t.topic.slice(0, 30)}</span>
                <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: t.status === 'OPEN' ? '#064e3b' : '#1e222d', color: t.status === 'OPEN' ? '#34d399' : '#9ca3af' }}>{t.status}</span>
              </div>
              <div style={{ fontSize: 11, color: "#6b7280" }}>{t.aim} • {t.point_wallet.budget}pt budget</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
        {!thread ? <div style={{ textAlign: "center", color: "#6b7280", marginTop: 100 }}>Select a thread</div> : (
          <>
            <div className="card">
              <div className="card-body">
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <div>
                    <h2 style={{ margin: "0 0 8px 0", color: "#fff" }}>{thread.topic}</h2>
                    <div style={{ fontSize: 12, color: "#9ca3af" }}>Owner: {state.agents[thread.owner_agent]?.name_id} • Dept: {thread.owner_department || "none"}</div>
                  </div>
                  {(thread.status === 'OPEN' || thread.status === 'ACTIVE') && (
                    <div style={{ display: "flex", gap: 8 }}>
                      <button className="btn" style={{ background: "#064e3b", color: "#34d399" }} onClick={() => approveThread(sel)}>Approve</button>
                      <button className="btn" style={{ background: "#7f1d1d", color: "#f87171" }} onClick={() => rejectThread(sel)}>Reject</button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
              <div className="card-header" style={{ fontSize: 12, fontWeight: 600, color: "#9ca3af" }}>MESSAGES</div>
              <div className="card-body" style={{ flex: 1, overflowY: "auto", background: "#0a0b0e" }}>
                {thread.messages_log?.map((m, i) => (
                  <div key={i} style={{ marginBottom: 12 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, color: "#818cf8", fontSize: 12 }}>{state.agents[m.who]?.name_id || m.who}</span>
                      <span className="mono" style={{ fontSize: 10, color: "#4b5563" }}>{hhmm(m.when)}</span>
                    </div>
                    <div style={{ color: "#e2e8f0", backgroundColor: "#11141a", padding: "10px 14px", borderRadius: "0 8px 8px 8px", fontSize: 13, border: "1px solid #1a1d24" }}>
                      {m.what}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Prompts({ state, updatePrompt }) {
  const [sel, setSel] = useState(null);
  const [edit, setEdit] = useState({ name: "", system_prompt: "", user_prompt_template: "", custom_directives: "" });
  const [entries, setEntries] = useState([]);
  const [newEntry, setNewEntry] = useState({ title: "", body: "" });
  const [showEntries, setShowEntries] = useState(false);

  const pArr = Object.values(state.prompts || {});

  useEffect(() => {
    if (sel && state.prompts[sel]) {
      setEdit({
        name: state.prompts[sel].name || state.prompts[sel].id,
        system_prompt: state.prompts[sel].system_prompt || "",
        user_prompt_template: state.prompts[sel].user_prompt_template || "",
        custom_directives: state.prompts[sel].custom_directives || ""
      });
    }
  }, [sel, state.prompts]);

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

  return (
    <div style={{ display: "flex", gap: 20, height: "100%" }}>
      {/* Left: mode list */}
      <div style={{ width: 220, flexShrink: 0, overflowY: "auto" }}>
        <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 600, letterSpacing: 1, marginBottom: 10, textTransform: "uppercase" }}>Modes</div>
        {pArr.map(p => (
          <div key={p.id} onClick={() => setSel(p.id)} className="card" style={{ cursor: "pointer", marginBottom: 10, borderColor: sel === p.id ? "#6366f1" : "#1a1d24", background: sel === p.id ? "#1e1b4b" : "#11141a" }}>
            <div className="card-body" style={{ padding: "12px 14px" }}>
              <div style={{ fontWeight: 600, color: "#e2e8f0", marginBottom: 3 }}>{p.name || p.id}</div>
              <div style={{ fontSize: 11, color: "#6b7280", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{p.system_prompt}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Centre: editor */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {!sel ? <div style={{ textAlign: "center", color: "#6b7280", marginTop: 100 }}>Select a prompt template to edit</div> : (
          <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div className="card-header">
              <span style={{ fontWeight: 600, color: "#fff", fontSize: 15 }}>Edit: {sel}</span>
              <button className="btn btn-primary" onClick={() => updatePrompt(sel, edit)}>Save Changes</button>
            </div>
            <div className="card-body" style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 16 }}>
              <div>
                <label style={{ display: "block", fontSize: 12, marginBottom: 6, color: "#9ca3af", fontWeight: 500 }}>Display Name</label>
                <input value={edit.name} onChange={e => setEdit({ ...edit, name: e.target.value })} style={{ width: "100%" }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, marginBottom: 6, color: "#9ca3af", fontWeight: 500 }}>System Prompt — Identity & Strategy</label>
                <textarea value={edit.system_prompt} onChange={e => setEdit({ ...edit, system_prompt: e.target.value })} rows={5} style={{ width: "100%", resize: "vertical", fontFamily: "inherit" }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#9ca3af", fontWeight: 500 }}>Mode Directives — injected every tick in this mode</label>
                <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 6 }}>Behavioural rules applied whenever any agent is running in this mode.</div>
                <textarea value={edit.custom_directives} onChange={e => setEdit({ ...edit, custom_directives: e.target.value })} rows={4} style={{ width: "100%", resize: "vertical", fontFamily: "inherit", borderColor: "#4f46e5" }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#9ca3af", fontWeight: 500 }}>User Prompt Template — reply format & goals</label>
                <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 6 }}>Appended last to specify exactly how the LLM must reply.</div>
                <textarea value={edit.user_prompt_template} onChange={e => setEdit({ ...edit, user_prompt_template: e.target.value })} rows={5} style={{ width: "100%", resize: "vertical", fontFamily: "inherit" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right: Saved Entries */}
      <div style={{ width: 260, flexShrink: 0, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 600, letterSpacing: 1, textTransform: "uppercase" }}>Saved Entries</div>
          <button className="btn btn-soft" style={{ fontSize: 11, padding: "3px 8px" }} onClick={() => setShowEntries(v => !v)}>{showEntries ? "▲ Hide" : "▼ Add"}</button>
        </div>

        {showEntries && (
          <div className="card">
            <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <input placeholder="Entry title..." value={newEntry.title} onChange={e => setNewEntry({ ...newEntry, title: e.target.value })} style={{ width: "100%" }} />
              <textarea rows={3} placeholder="Prompt text..." value={newEntry.body} onChange={e => setNewEntry({ ...newEntry, body: e.target.value })} style={{ width: "100%", resize: "vertical", fontFamily: "inherit" }} />
              <button className="btn btn-primary" style={{ width: "100%" }} onClick={saveEntry}>Save Entry</button>
            </div>
          </div>
        )}

        <div style={{ flex: 1, overflowY: "auto" }}>
          {entries.length === 0 && <div style={{ fontSize: 12, color: "#4b5563", textAlign: "center", marginTop: 20 }}>No saved entries yet.</div>}
          {entries.map(e => (
            <div key={e.id} style={{ background: "#11141a", border: "1px solid #1a1d24", borderRadius: 8, padding: 10, marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 600, fontSize: 12, color: "#e2e8f0" }}>{e.title}</span>
                <button onClick={() => deleteEntry(e.id)} style={{ background: "none", border: "none", color: "#6b7280", cursor: "pointer", fontSize: 12, padding: 0 }}>✕</button>
              </div>
              <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 8, lineHeight: 1.5, wordBreak: "break-word" }}>{e.body.slice(0, 120)}{e.body.length > 120 ? "..." : ""}</div>
              <button className="btn btn-soft" style={{ fontSize: 11, padding: "3px 10px", width: "100%" }}
                onClick={() => navigator.clipboard.writeText(e.body)}>Copy</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Departments({ state }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 20 }}>
      {Object.entries(DEPT_META).map(([id, meta]) => {
        const dept = state.departments[id];
        if (!dept) return null;
        const allAgents = dept.agents?.map(aid => state.agents[aid]).filter(Boolean) || [];
        const ceo = allAgents.find(a => a.is_ceo);
        const members = allAgents.filter(a => !a.is_ceo);

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
              {/* CEO row */}
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
                    <span>Ticks every: <span style={{ color: "#e2e8f0" }}>{ceo.ticks}s</span></span>
                    {ceo.next_mode && <span style={{ color: "#6366f1" }}>→ {ceo.next_mode}</span>}
                  </div>
                  {ceo.memory && <div style={{ marginTop: 6, fontSize: 11, color: "#4b5563", fontStyle: "italic" }}>💭 {ceo.memory.slice(0, 80)}{ceo.memory.length > 80 ? "..." : ""}</div>}
                </div>
              )}

              {/* Separator */}
              {members.length > 0 && <div style={{ fontSize: 10, color: "#374151", fontWeight: 600, letterSpacing: 1, paddingLeft: 2 }}>MEMBERS</div>}

              {/* Member rows */}
              {members.map(a => (
                <div key={a.name_id} style={{ background: "#0d0f14", border: "1px solid #1a1d24", borderRadius: 6, padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 500, color: "#e2e8f0", fontSize: 12 }}>{a.name_id}</div>
                    <div style={{ display: "flex", gap: 10, fontSize: 11, color: "#6b7280", marginTop: 2 }}>
                      <span>Wallet: <span style={{ color: "#10b981" }}>{a.wallet?.current ?? 0}</span></span>
                      <span>Tick: {a.ticks}s</span>
                    </div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                    <span style={{ fontSize: 11, color: "#9ca3af", background: "#1a1d24", padding: "2px 8px", borderRadius: 4 }}>{a.mode}</span>
                    {a.next_mode && <span style={{ fontSize: 10, color: "#6366f1" }}>→ {a.next_mode}</span>}
                  </div>
                </div>
              ))}

              {/* Ledger recent */}
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

function Settings({ state, updateSetting }) {
  const [ollamaModel, setOllamaModel] = useState("");
  const [ollamaServer, setOllamaServer] = useState("");
  const [availableModels, setAvailableModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (state.settings) {
      if (state.settings.ollama_model !== undefined) setOllamaModel(state.settings.ollama_model);
      if (state.settings.ollama_server !== undefined) setOllamaServer(state.settings.ollama_server);
    }
  }, [state.settings]);

  const fetchModels = async () => {
    setLoadingModels(true);
    try {
      const r = await fetch(`${API_BASE}/ollama-models`);
      const body = await r.json();
      if (body.status === "success") setAvailableModels(body.models);
    } catch (e) { console.error("fetch models", e); }
    setLoadingModels(false);
  };

  useEffect(() => { fetchModels(); }, []);

  const saveSettings = async () => {
    await updateSetting("ollama_model", ollamaModel);
    await updateSetting("ollama_server", ollamaServer);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const r = await fetch(`${API_BASE}/test-ollama`);
      const body = await r.json();
      setTestResult(body);
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
          <div style={{ fontSize: 11, color: "#4b5563", marginTop: 6 }}>Base URL of your Ollama server.</div>
        </div>

        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <label style={{ fontSize: 12, color: "#9ca3af", fontWeight: 500 }}>Active Model</label>
            <button className="btn btn-soft" style={{ fontSize: 11, padding: "3px 10px" }} onClick={fetchModels} disabled={loadingModels}>
              {loadingModels ? "Refreshing..." : "↻ Refresh"}
            </button>
          </div>
          {availableModels.length > 0 ? (
            <select value={ollamaModel} onChange={e => setOllamaModel(e.target.value)} style={{ width: "100%" }}>
              {availableModels.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          ) : (
            <input value={ollamaModel} onChange={e => setOllamaModel(e.target.value)} placeholder="e.g. gemma4:e4b" style={{ width: "100%" }} />
          )}
          <div style={{ fontSize: 11, color: "#4b5563", marginTop: 6 }}>Model used for all agent reasoning loops.</div>
        </div>

        <div>
          <button className="btn btn-primary" onClick={saveSettings} style={{ minWidth: 120 }}>
            {saved ? "✓ Saved!" : "Save Settings"}
          </button>
        </div>

        <div style={{ borderTop: "1px solid #1a1d24", paddingTop: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <div style={{ fontWeight: 500, color: "#e2e8f0", fontSize: 14 }}>Connection Test</div>
              <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>Sends a live prompt to verify the server + model are working. May take 20–60s on cold start.</div>
            </div>
            <button className="btn btn-soft" onClick={testConnection} disabled={testing} style={{ minWidth: 130, flexShrink: 0, marginLeft: 16 }}>
              {testing ? (
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ display: "inline-block", width: 10, height: 10, border: "2px solid #374151", borderTopColor: "#818cf8", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
                  Waiting...
                </span>
              ) : "▶ Test Connection"}
            </button>
          </div>
          {testResult && (
            <div style={{ padding: "12px 16px", borderRadius: 8, background: testResult.status === 'success' ? '#064e3b' : '#450a0a', border: `1px solid ${testResult.status === 'success' ? '#059669' : '#991b1b'}` }}>
              <div style={{ color: testResult.status === 'success' ? '#34d399' : '#fca5a5', fontWeight: 700, fontSize: 12, marginBottom: 6 }}>
                {testResult.status === 'success' ? '✓ CONNECTION OK' : '✗ FAILED'}
              </div>
              <div style={{ color: testResult.status === 'success' ? '#a7f3d0' : '#fecaca', fontSize: 12 }}>{testResult.message}</div>
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
function Chats({ state, fetchState }) {
  const [sel, setSel] = useState(null);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const chatThreads = Object.values(state.threads).filter(t => t.aim === "Chat");
  const agents = Object.values(state.agents);

  const sendChat = async () => {
    if (!sel || !msg.trim() || loading) return;
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/agents/${sel}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });
      await r.json();
      setMsg("");
      fetchState();
    } catch (e) {
      console.error("Chat error", e);
    } finally {
      setLoading(false);
    }
  };

  const selectedAgent = state.agents[sel];
  const activeThread = chatThreads.find(t => t.owner_agent == sel);

  return (
    <div style={{ display: "flex", gap: 20, height: "calc(100vh - 160px)" }}>
      {/* Sidebar: Agents */}
      <div style={{ width: 240, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 600, letterSpacing: 1, textTransform: "uppercase" }}>Direct Message</div>
        {agents.map(a => (
          <div key={a.name_id} 
               onClick={() => setSel(a.id)}
               className="card" 
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

      {/* Chat Area */}
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
              {!activeThread && <div style={{ textAlign: "center", color: "#4b5563", fontSize: 12, marginTop: 40 }}>No previous conversation. Send a message to start.</div>}
              {activeThread?.messages_log.map((m, i) => (
                <div key={i} style={{ 
                  alignSelf: m.who === "FOUNDER" ? "flex-end" : "flex-start",
                  maxWidth: "80%",
                  background: m.who === "FOUNDER" ? "#4f46e5" : "#1a1d24",
                  color: "#fff",
                  padding: "10px 14px",
                  borderRadius: m.who === "FOUNDER" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                  fontSize: 13,
                  lineHeight: 1.5,
                  border: m.who === "FOUNDER" ? "none" : "1px solid #374151"
                }}>
                  <div style={{ fontSize: 10, opacity: 0.6, marginBottom: 4 }}>{m.who === "FOUNDER" ? "YOU (FOUNDER)" : selectedAgent.name_id}</div>
                  {m.what}
                </div>
              ))}
              {loading && (
                <div style={{ alignSelf: "flex-start", background: "#1a1d24", padding: "10px 14px", borderRadius: "12px 12px 12px 2px", fontSize: 12, color: "#6b7280", border: "1px solid #374151" }}>
                  {selectedAgent.name_id} is thinking...
                </div>
              )}
            </div>
            <div style={{ padding: 16, borderTop: "1px solid #1a1d24", display: "flex", gap: 10 }}>
              <input 
                placeholder={`Message ${selectedAgent.name_id}...`} 
                value={msg} 
                onChange={e => setMsg(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendChat()}
                style={{ flex: 1 }}
              />
              <button className="btn btn-primary" onClick={sendChat} disabled={loading || !msg.trim()}>
                {loading ? "..." : "Send"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
function Tools({ state, fetchState }) {
  const tools = Object.values(state.tools || {});
  const [instr, setInstr] = useState(state.settings?.tools_instruction_prefix || "");

  useEffect(() => {
    if (state.settings?.tools_instruction_prefix !== undefined) {
      setInstr(state.settings.tools_instruction_prefix);
    }
  }, [state.settings?.tools_instruction_prefix]);

  const toggleTool = async (tid, current) => {
    await fetch(`${API_BASE}/tools/${tid}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !current })
    });
    fetchState();
  };

  const saveInstr = async () => {
    await fetch(`${API_BASE}/settings/tools_instruction_prefix`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: instr })
    });
    fetchState();
  };

  const enabledTools = tools.filter(t => t.enabled);
  const previewText = `${instr}\n\n${enabledTools.map(t => `- ${t.description}`).join('\n') || 'No tools available.'}`;

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ display: "flex", gap: 32, marginBottom: 40, alignItems: "stretch" }}>
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <h1 style={{ color: "#fff", fontSize: 24, marginBottom: 8 }}>Agent Capabilities</h1>
          <p style={{ color: "#6b7280", fontSize: 13, marginBottom: 24 }}>Define the global instructions and individual tools available to your agents.</p>
          
          <div className="card" style={{ flex: 1, padding: 20 }}>
            <label style={{ display: "block", fontSize: 10, color: "#6366f1", fontWeight: 800, letterSpacing: 1.5, marginBottom: 12, textTransform: "uppercase" }}>Global Tool Instruction Prompt</label>
            <textarea 
              value={instr} 
              onChange={e => setInstr(e.target.value)}
              placeholder="Enter instructions for agents on how to format and use tools..."
              style={{ height: 140, width: "100%", fontSize: 13, padding: 14, marginBottom: 16, background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0", borderRadius: 8, lineHeight: 1.6 }}
            />
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button 
                className="btn btn-primary" 
                onClick={saveInstr} 
                disabled={instr === state.settings?.tools_instruction_prefix}
                style={{ padding: "8px 20px" }}
              >
                Save Global Prompt
              </button>
            </div>
          </div>
        </div>

        <div style={{ width: 440, display: "flex", flexDirection: "column" }}>
          <label style={{ display: "block", fontSize: 10, color: "#9ca3af", fontWeight: 800, letterSpacing: 1.5, marginBottom: 12, textTransform: "uppercase" }}>Agent Context Preview</label>
          <div className="card" style={{ flex: 1, background: "#0b0c10", padding: 20, border: "1px dashed #1e222d", position: "relative" }}>
            <div style={{ position: "absolute", top: 10, right: 10, fontSize: 9, color: "#4b5563", background: "#11141a", padding: "2px 6px", borderRadius: 4 }}>READ ONLY</div>
            <pre style={{ 
              whiteSpace: "pre-wrap", 
              fontSize: 12, 
              color: "#9ca3af",
              lineHeight: 1.6,
              margin: 0,
              fontFamily: "'JetBrains Mono', monospace"
            }}>
              {previewText}
            </pre>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 20 }}>
        {tools.length === 0 && <div style={{ color: "#4b5563", textAlign: "center", gridColumn: "1/-1", padding: 40 }}>No tools registered in database.</div>}
        {tools.map(t => (
          <div key={t.id} className="card" style={{ opacity: t.enabled ? 1 : 0.6, border: t.enabled ? "1px solid #1e222d" : "1px solid #ef444422" }}>
            <div className="card-header" style={{ justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: t.enabled ? "#1e1b4b" : "#1a1d24", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.3s" }}>
                   <span style={{ fontSize: 16 }}>{t.id === "modify_own_tick" ? "⏱️" : "🔧"}</span>
                </div>
                <div>
                  <div style={{ fontWeight: 700, color: "#fff" }}>{t.name}</div>
                  <div className="mono" style={{ fontSize: 10, color: "#6366f1" }}>{t.id}</div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center" }}>
                <div 
                  onClick={() => toggleTool(t.id, t.enabled)}
                  style={{ 
                    width: 44, height: 22, borderRadius: 100, background: t.enabled ? "#6366f1" : "#1a1d24", 
                    position: "relative", cursor: "pointer", transition: "all 0.3s",
                    border: "1px solid #1e222d"
                  }}>
                  <div style={{ 
                    width: 16, height: 16, borderRadius: "50%", background: "#fff",
                    position: "absolute", top: 2, left: t.enabled ? 24 : 3, transition: "all 0.3s"
                  }} />
                </div>
              </div>
            </div>
            <div className="card-body">
              <div style={{ fontSize: 12, color: "#9ca3af", lineHeight: 1.6, marginBottom: 16 }}>
                {t.description}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 16, borderTop: "1px solid #1a1d24" }}>
                <span style={{ fontSize: 11, color: "#4b5563" }}>Status</span>
                <span style={{ fontSize: 11, fontWeight: 600, color: t.enabled ? "#10b981" : "#ef4444" }}>
                   {t.enabled ? "ACTIVE" : "DISABLED"}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
