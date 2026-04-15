import { useState, useRef, useEffect } from 'react';

const API_BASE = 'http://127.0.0.1:8000/api';

// ═══════════════════════════════════════════════════════════════════════════════
// NEW ToolWorkshop — clean 3-panel layout with CTHINKING toolbar
// ═══════════════════════════════════════════════════════════════════════════════

// ── CTHINKING reference data ──────────────────────────────────────────────────
export const CT_VARS = [
  { v: "{agent}",              color: "#38bdf8", desc: "Agent name/ID" },
  { v: "{wallet}",             color: "#38bdf8", desc: "Agent wallet balance" },
  { v: "{thread_summary}",     color: "#38bdf8", desc: "Active thread list" },
  { v: "{available_tickets}",  color: "#38bdf8", desc: "Unused ticket list" },
  { v: "{pending_quests}",     color: "#38bdf8", desc: "Pending join quests" },
  { v: "{pending_invitation}", color: "#38bdf8", desc: "Pending invitations" },
  { v: "{invitation_status}",  color: "#38bdf8", desc: "Latest quest status" },
  { v: "{memory}",             color: "#38bdf8", desc: "Agent memory" },
  { v: "{arg_0}",              color: "#34d399", desc: "First argument" },
  { v: "{arg_1}",              color: "#34d399", desc: "Second argument" },
  { v: "{arg_2}",              color: "#34d399", desc: "Third argument" },
];

export const CT_CONDS = [
  { k: "available_tickets_exist", color: "#fbbf24", desc: "Has unused tickets" },
  { k: "pending_quests_exist",    color: "#fbbf24", desc: "Has pending quests" },
  { k: "pending_invitation_exist",color: "#fbbf24", desc: "Has pending invitations" },
];

export const CT_BUILTINS = [
  { id: "get_time",               color: "#a78bfa" },
  { id: "get_weather",            color: "#a78bfa" },
  { id: "get_news",               color: "#a78bfa" },
  { id: "get_threads",            color: "#a78bfa" },
  { id: "get_agents",             color: "#a78bfa" },
  { id: "get_marketplace",        color: "#c084fc" },
  { id: "get_owned_tools",        color: "#c084fc" },
  { id: "own_tool",               color: "#c084fc" },
  { id: "get_agent_info",         color: "#a78bfa" },
  { id: "get_thread_info",        color: "#a78bfa" },
  { id: "get_agent_ranking",      color: "#a78bfa" },
  { id: "get_dept_ranking",       color: "#a78bfa" },
  { id: "get_recent_transactions",color: "#a78bfa" },
  { id: "create_thread",          color: "#f97316" },
  { id: "invest_thread",          color: "#f97316" },
  { id: "join_thread",            color: "#f97316" },
  { id: "approve_join",           color: "#f97316" },
  { id: "post_in_thread",         color: "#4ade80" },
  { id: "set_thread_status",      color: "#f97316" },
  { id: "refill_thread",          color: "#f97316" },
  { id: "produce_transaction",    color: "#f97316" },
  { id: "batch_invest",           color: "#f97316" },
  { id: "accept_invite",          color: "#f97316" },
  { id: "decline_invite",         color: "#f97316" },
];

export const CT_ACTIONS = [
  { id: "http_get",    label: "HTTP_GET",    color: "#22d3ee", snippet: "*/HTTP_GET|https://api.example.com/*" },
  { id: "http_post",   label: "HTTP_POST",   color: "#22d3ee", snippet: "[CALL_TOOL]\nHTTP_POST\nhttps://api.example.com\n{\"key\":\"val\"}\n[END_CALL_TOOL]" },
  { id: "create_file", label: "CREATE_FILE", color: "#22d3ee", snippet: "[CALL_TOOL]\nCREATE_FILE\noutput.txt\nContent here\n[END_CALL_TOOL]" },
  { id: "read_file",   label: "READ_FILE",   color: "#22d3ee", snippet: "*/READ_FILE|output.txt/*" },
];

// ── Pill chip helper ──────────────────────────────────────────────────────────
export function Chip({ label, color = "#6366f1", title = "", onClick, mono = true }) {
  return (
    <button
      title={title}
      onClick={onClick}
      style={{
        fontSize: 10, padding: "3px 8px", cursor: "pointer", borderRadius: 4,
        fontFamily: mono ? "monospace" : "inherit",
        background: color + "18", border: `1px solid ${color}44`,
        color, transition: "all 0.12s", whiteSpace: "nowrap",
        lineHeight: 1.4,
      }}
      onMouseEnter={e => { e.currentTarget.style.background = color + "33"; e.currentTarget.style.borderColor = color + "88"; }}
      onMouseLeave={e => { e.currentTarget.style.background = color + "18"; e.currentTarget.style.borderColor = color + "44"; }}
    >
      {label}
    </button>
  );
}

// ── Collapsible section ───────────────────────────────────────────────────────
export function CollapseSection({ title, accent = "#6366f1", defaultOpen = true, children, count }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ marginBottom: 2 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: 6,
          background: "none", border: "none", cursor: "pointer",
          padding: "6px 0", color: accent, fontWeight: 700, fontSize: 10,
          letterSpacing: "0.8px", textTransform: "uppercase",
        }}
      >
        <span style={{ fontSize: 9 }}>{open ? "▼" : "▶"}</span>
        {title}
        {count !== undefined && (
          <span style={{
            marginLeft: "auto", fontSize: 9, padding: "1px 7px",
            background: accent + "22", color: accent, borderRadius: 10,
          }}>{count}</span>
        )}
      </button>
      {open && <div style={{ paddingBottom: 8 }}>{children}</div>}
    </div>
  );
}

// ── CTHINKING Toolbar ─────────────────────────────────────────────────────────
export function CThinkingToolbar({ onInsert, argCount = 0, tools = [] }) {
  const insertVar   = v => onInsert(v);
  const insertTool  = id => onInsert(`\n[CALL_TOOL]\n${id}\n- arg1\n[END_CALL_TOOL]\n`);
  const insertInline= id => onInsert(`*/` + id + `/*`);
  const insertCond  = k  => onInsert(`{{\n  ${k}\n    Value if TRUE\n  /ELSE/\n    Value if FALSE\n}}`);
  const insertAction= snip => onInsert(snip);

  return (
    <div style={{
      background: "#07090e", border: "1px solid #1a1d24", borderRadius: 8,
      padding: "10px 14px", display: "flex", flexDirection: "column", gap: 4,
    }}>
      <div style={{ fontSize: 9, fontWeight: 800, color: "#4b5563", letterSpacing: 1.2, marginBottom: 4 }}>
        CTHINKING TOOLBAR — click to insert at cursor
      </div>

      {/* Variables */}
      <CollapseSection title="Live Variables" accent="#38bdf8" defaultOpen={true}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {CT_VARS.filter(v => !v.v.startsWith("{arg_") || parseInt(v.v.slice(5)) < Math.max(argCount, 1)).map(cv => (
            <Chip key={cv.v} label={cv.v} color={cv.color} title={cv.desc} onClick={() => insertVar(cv.v)} />
          ))}
        </div>
      </CollapseSection>

      {/* Conditionals */}
      <CollapseSection title="Conditionals" accent="#fbbf24" defaultOpen={true}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {CT_CONDS.map(c => (
            <Chip key={c.k} label={`{{ ${c.k} }}`} color={c.color} title={c.desc} onClick={() => insertCond(c.k)} />
          ))}
        </div>
      </CollapseSection>

      {/* Built-in tools (inline & block) */}
      <CollapseSection title="Built-in Tools (inline)" accent="#a78bfa" defaultOpen={false}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {CT_BUILTINS.map(bt => (
            <Chip key={bt.id} label={`*/${bt.id}/*`} color={bt.color} onClick={() => insertInline(bt.id)} />
          ))}
        </div>
      </CollapseSection>

      <CollapseSection title="Built-in Tools (block)" accent="#c084fc" defaultOpen={false}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {CT_BUILTINS.map(bt => (
            <Chip key={bt.id + "_b"} label={`[${bt.id}]`} color={bt.color} onClick={() => insertTool(bt.id)} />
          ))}
        </div>
      </CollapseSection>

      {/* Custom tools chain */}
      {tools.length > 0 && (
        <CollapseSection title="Custom Tools (chain)" accent="#f97316" defaultOpen={false} count={tools.length}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {tools.map(t => (
              <Chip key={t.id} label={t.id} color="#f97316" title={t.name} onClick={() => insertTool(t.id)} />
            ))}
          </div>
        </CollapseSection>
      )}

      {/* System actions */}
      <CollapseSection title="System Actions" accent="#22d3ee" defaultOpen={false}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {CT_ACTIONS.map(a => (
            <Chip key={a.id} label={a.label} color={a.color} onClick={() => insertAction(a.snippet)} />
          ))}
        </div>
        <div style={{ marginTop: 6 }}>
          <Chip label="BLOCK: [CALL_TOOL]...[END_CALL_TOOL]" color="#22d3ee"
            onClick={() => insertAction("\n[CALL_TOOL]\ntool_name\n- argument1\n- argument2\n[END_CALL_TOOL]\n")} />
        </div>
      </CollapseSection>
    </div>
  );
}

// ── ToolWorkshop main component ───────────────────────────────────────────────
export function ToolWorkshop({ tools, agents, state, fetchState }) {
  const blankForm = {
    id: "", name: "", description: "", prompt_template: "",
    args: [], call_tools: [], allowed_actions: [], owner_id: "FOUNDER", price: 0,
  };

  const [form, setForm]             = useState(blankForm);
  const [testAgentId, setTestAgent] = useState("");
  const [testArgs, setTestArgs]     = useState([]);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting]       = useState(false);
  const [saving, setSaving]         = useState(false);
  const [saved, setSaved]           = useState(false);
  const [search, setSearch]         = useState("");
  const [showToolbar, setShowToolbar] = useState(true);
  const promptRef = useRef(null);

  const customTools = tools.filter(t => t.is_custom);
  const filteredCustom = customTools.filter(t =>
    !search || t.name.toLowerCase().includes(search.toLowerCase()) || t.id.toLowerCase().includes(search.toLowerCase())
  );

  const setField   = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const addArg     = () => setField("args", [...form.args, { name: "", description: "" }]);
  const removeArg  = i => setField("args", form.args.filter((_, j) => j !== i));
  const setArg     = (i, k, v) => setForm(f => { const a = [...f.args]; a[i] = { ...a[i], [k]: v }; return { ...f, args: a }; });
  const toggleCallTool = tid => setField("call_tools",
    form.call_tools.includes(tid) ? form.call_tools.filter(x => x !== tid) : [...form.call_tools, tid]);
  const toggleAction = id => setField("allowed_actions",
    form.allowed_actions.includes(id) ? form.allowed_actions.filter(x => x !== id) : [...form.allowed_actions, id]);

  // Insert at cursor position in the textarea
  const insertAt = (snippet) => {
    const ta = promptRef.current;
    if (!ta) { setField("prompt_template", (form.prompt_template || "") + snippet); return; }
    const s = ta.selectionStart, e = ta.selectionEnd;
    const newVal = form.prompt_template.slice(0, s) + snippet + form.prompt_template.slice(e);
    setField("prompt_template", newVal);
    setTimeout(() => { ta.selectionStart = ta.selectionEnd = s + snippet.length; ta.focus(); }, 0);
  };

  const loadTool = t => {
    let args = [], callTools = [], actions = [];
    try { args = JSON.parse(t.args_definition || "[]"); } catch {}
    try { callTools = JSON.parse(t.call_tools || "[]"); } catch {}
    try { actions = JSON.parse(t.allowed_actions || "[]"); } catch {}
    setForm({ id: t.id, name: t.name, description: t.description || "",
      prompt_template: t.prompt_template || "", args, call_tools: callTools,
      allowed_actions: actions, owner_id: t.owner_id || "FOUNDER", price: t.price || 0 });
    setTestResult(null);
  };

  const saveTool = async () => {
    if (!form.id || !form.name) return;
    setSaving(true);
    const payload = {
      id: form.id, name: form.name, description: form.description,
      prompt_template: form.prompt_template,
      args_definition: JSON.stringify(form.args),
      call_tools: JSON.stringify(form.call_tools),
      allowed_actions: JSON.stringify(form.allowed_actions),
      owner_id: form.owner_id === "FOUNDER" ? null : form.owner_id,
      price: form.price,
    };
    const exists = tools.find(t => t.id === form.id && t.is_custom);
    if (exists) await fetch(`${API_BASE}/tools/${form.id}`, { method: "DELETE" });
    await fetch(`${API_BASE}/tools`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    if (payload.price > 0 || payload.owner_id) {
      await fetch(`${API_BASE}/tools/${form.id}/owner`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ owner_id: payload.owner_id || "FOUNDER", price: payload.price }),
      });
    }
    setSaving(false); setSaved(true); setTimeout(() => setSaved(false), 2000); fetchState();
  };

  const deleteTool = async (tid) => {
    if (!window.confirm(`Delete tool "${tid}"?`)) return;
    await fetch(`${API_BASE}/tools/${tid}`, { method: "DELETE" });
    if (form.id === tid) setForm(blankForm);
    fetchState();
  };

  const runTest = async () => {
    if (!testAgentId || !form.id) return;
    setTesting(true); setTestResult(null);
    const r = await fetch(`${API_BASE}/tools/${form.id}/invoke`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent_id: testAgentId, args: testArgs.join(", ") }),
    });
    const d = await r.json();
    setTestResult(d.result || d.error || "No result"); setTesting(false);
  };

  const inp = {
    background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0",
    borderRadius: 6, padding: "6px 10px", fontSize: 12, width: "100%", outline: "none",
  };

  return (
    <div style={{ display: "flex", gap: 12, height: "calc(100vh - 190px)", minHeight: 0 }}>

      {/* ── PANEL 1: Tool List ──────────────────────────────────────────────── */}
      <div style={{
        width: 220, flexShrink: 0, display: "flex", flexDirection: "column",
        background: "#090b10", border: "1px solid #1a1d24", borderRadius: 10, overflow: "hidden",
      }}>
        {/* Header */}
        <div style={{
          padding: "12px 14px", borderBottom: "1px solid #1a1d24",
          background: "#0b0d14",
        }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: "#6366f1", letterSpacing: 1, marginBottom: 8 }}>
            🛠️ CUSTOM TOOLS
          </div>
          <input
            placeholder="Search…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ ...inp, padding: "5px 8px", fontSize: 11 }}
          />
        </div>

        {/* New tool button */}
        <div style={{ padding: "8px 10px", borderBottom: "1px solid #1a1d24" }}>
          <button
            onClick={() => { setForm(blankForm); setTestResult(null); }}
            style={{
              width: "100%", padding: "7px 0", fontSize: 11, fontWeight: 700,
              background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
              color: "#fff", border: "none", borderRadius: 7, cursor: "pointer",
            }}
          >
            + New Tool
          </button>
        </div>

        {/* Tool list */}
        <div style={{ flex: 1, overflowY: "auto", padding: "6px 8px" }}>
          {filteredCustom.length === 0 && (
            <div style={{ fontSize: 11, color: "#374151", textAlign: "center", padding: "20px 0" }}>
              No custom tools yet.
            </div>
          )}
          {filteredCustom.map(t => (
            <div
              key={t.id}
              onClick={() => loadTool(t)}
              style={{
                padding: "9px 10px", borderRadius: 7, marginBottom: 4, cursor: "pointer",
                background: form.id === t.id ? "#1e1b4b" : "#0d0f14",
                border: `1px solid ${form.id === t.id ? "#6366f1" : "#1a1d24"}`,
                transition: "all 0.12s",
              }}
              onMouseEnter={e => { if (form.id !== t.id) e.currentTarget.style.borderColor = "#374151"; }}
              onMouseLeave={e => { if (form.id !== t.id) e.currentTarget.style.borderColor = "#1a1d24"; }}
            >
              <div style={{ fontSize: 12, fontWeight: 600, color: "#e2e8f0", marginBottom: 2 }}>
                {t.name}
              </div>
              <div style={{ fontSize: 9, fontFamily: "monospace", color: "#6366f1", marginBottom: 3 }}>
                {t.id}
              </div>
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                {t.enabled ? (
                  <span style={{ fontSize: 9, color: "#4ade80", background: "#052e1622", padding: "1px 5px", borderRadius: 3 }}>ON</span>
                ) : (
                  <span style={{ fontSize: 9, color: "#ef4444", background: "#7f1d1d22", padding: "1px 5px", borderRadius: 3 }}>OFF</span>
                )}
                {t.price > 0 && (
                  <span style={{ fontSize: 9, color: "#fbbf24", background: "#fbbf2418", padding: "1px 5px", borderRadius: 3 }}>
                    {t.price}pts/use
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Stats */}
        <div style={{ padding: "8px 14px", borderTop: "1px solid #1a1d24", fontSize: 10, color: "#374151" }}>
          {customTools.length} custom · {tools.filter(t => !t.is_custom).length} built-in
        </div>
      </div>

      {/* ── PANEL 2: Editor ────────────────────────────────────────────────── */}
      <div style={{
        flex: 1, display: "flex", flexDirection: "column", gap: 8,
        minWidth: 0, overflowY: "auto",
      }}>

        {/* Identity row */}
        <div style={{
          background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "14px 16px",
          display: "flex", gap: 12, alignItems: "flex-end",
        }}>
          <div style={{ flex: "0 0 160px" }}>
            <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>TOOL ID *</div>
            <input value={form.id} onChange={e => setField("id", e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_"))}
              placeholder="my_tool" style={{ ...inp, fontFamily: "monospace", color: "#818cf8" }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>NAME *</div>
            <input value={form.name} onChange={e => setField("name", e.target.value)}
              placeholder="My Custom Tool" style={inp} />
          </div>
        </div>

        {/* Description */}
        <div style={{ background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "14px 16px" }}>
          <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>
            DESCRIPTION <span style={{ color: "#4b5563", fontWeight: 400 }}>(shown to agents)</span>
          </div>
          <textarea
            value={form.description}
            onChange={e => setField("description", e.target.value)}
            placeholder={"[CALL_TOOL]\n- my_tool\n- arg\n[END_CALL_TOOL]\nDescribes what this tool does."}
            style={{ ...inp, height: 72, resize: "vertical", fontFamily: "monospace", fontSize: 11, lineHeight: 1.5 }}
          />
        </div>

        {/* Arguments */}
        <div style={{ background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "14px 16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1 }}>
              ARGUMENTS ({form.args.length})
            </div>
            <button onClick={addArg} style={{
              fontSize: 10, padding: "3px 10px", background: "#1e1b4b", border: "1px solid #6366f1",
              color: "#818cf8", borderRadius: 5, cursor: "pointer",
            }}>+ Add Argument</button>
          </div>
          {form.args.length === 0 && (
            <div style={{ fontSize: 11, color: "#374151", fontStyle: "italic" }}>No args defined.</div>
          )}
          {form.args.map((a, i) => (
            <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "center" }}>
              <input
                value={a.name} onChange={e => setArg(i, "name", e.target.value)}
                placeholder={`arg_${i}`}
                style={{ ...inp, flex: "0 0 110px", fontFamily: "monospace", color: "#34d399", fontSize: 11 }}
              />
              <input
                value={a.description} onChange={e => setArg(i, "description", e.target.value)}
                placeholder="Description"
                style={{ ...inp, flex: 1, fontSize: 11 }}
              />
              <button onClick={() => removeArg(i)} style={{
                background: "none", border: "1px solid #1e222d", color: "#6b7280", borderRadius: 5,
                cursor: "pointer", padding: "4px 8px", fontSize: 12, flexShrink: 0,
              }}
                onMouseEnter={e => { e.currentTarget.style.color = "#ef4444"; e.currentTarget.style.borderColor = "#ef4444"; }}
                onMouseLeave={e => { e.currentTarget.style.color = "#6b7280"; e.currentTarget.style.borderColor = "#1e222d"; }}
              >✕</button>
            </div>
          ))}
        </div>

        {/* CTHINKING Toolbar toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={() => setShowToolbar(v => !v)}
            style={{
              fontSize: 10, padding: "5px 14px", fontWeight: 700,
              background: showToolbar ? "#1e1b4b" : "#0d0f14",
              border: `1px solid ${showToolbar ? "#6366f1" : "#1e222d"}`,
              color: showToolbar ? "#818cf8" : "#6b7280",
              borderRadius: 6, cursor: "pointer", letterSpacing: 0.5,
            }}
          >
            {showToolbar ? "▲ Hide" : "▼ Show"} CTHINKING Toolbar
          </button>
          <span style={{ fontSize: 10, color: "#4b5563" }}>
            Click any chip to insert at cursor position
          </span>
        </div>

        {showToolbar && (
          <CThinkingToolbar
            onInsert={insertAt}
            argCount={form.args.length}
            tools={customTools.filter(t => t.id !== form.id)}
          />
        )}

        {/* Prompt Template */}
        <div style={{ background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "14px 16px" }}>
          <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 8 }}>
            CTHINKING PROMPT TEMPLATE
          </div>
          <textarea
            ref={promptRef}
            value={form.prompt_template}
            onChange={e => setField("prompt_template", e.target.value)}
            placeholder={"📊 CONTEXT for {agent}\n\n=== THREADS ===\n{thread_summary}\n\n=== MY WALLET ===\n{wallet} pts\n\n{{ pending_quests_exist\n  You have pending quests!\n  /ELSE/\n  No quests.\n}}\n\nTime: */get_time/*"}
            style={{
              ...inp, height: 200, resize: "vertical",
              fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
              lineHeight: 1.7, color: "#67e8f9",
            }}
          />
        </div>

        {/* Chain Tools */}
        <div style={{ background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "14px 16px" }}>
          <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 8 }}>CHAIN TOOLS</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, maxHeight: 160, overflowY: "auto" }}>
            {tools.map(t => (
              <label key={t.id} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", padding: "4px 0" }}>
                <input
                  type="checkbox"
                  checked={form.call_tools.includes(t.id)}
                  onChange={() => toggleCallTool(t.id)}
                  style={{ width: 12, height: 12 }}
                />
                <span style={{ fontSize: 11, color: form.call_tools.includes(t.id) ? "#a78bfa" : "#6b7280" }}>
                  {t.name}
                </span>
                <span style={{ fontSize: 9, fontFamily: "monospace", color: "#374151" }}>{t.id}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Allowed Actions */}
        <div style={{ background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "14px 16px" }}>
          <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 8 }}>ALLOWED ACTIONS</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["http_get", "http_post", "create_file", "read_file"].map(id => {
              const on = form.allowed_actions.includes(id);
              return (
                <label key={id} style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                  <input type="checkbox" checked={on} onChange={() => toggleAction(id)} />
                  <span style={{ fontSize: 11, color: on ? "#22d3ee" : "#6b7280", fontWeight: on ? 600 : 400 }}>
                    {id.replace("_", " ").toUpperCase()}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── PANEL 3: Properties + Test ─────────────────────────────────────── */}
      <div style={{
        width: 260, flexShrink: 0, display: "flex", flexDirection: "column", gap: 8,
        overflowY: "auto",
      }}>

        {/* Header */}
        <div style={{
          background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10,
          padding: "12px 14px",
        }}>
          <div style={{ fontSize: 11, fontWeight: 800, color: "#e2e8f0", marginBottom: 2 }}>
            🔧 Tool Properties
          </div>
          <div style={{ fontSize: 10, color: "#4b5563" }}>
            {form.id || "new tool"}
          </div>
        </div>

        {/* Economy & Ownership */}
        <div style={{ background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "14px 14px" }}>
          <div style={{ fontSize: 9, fontWeight: 800, color: "#fbbf24", letterSpacing: 1, marginBottom: 10 }}>
            ECONOMY & OWNERSHIP
          </div>

          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>OWNER</div>
            <select
              value={form.owner_id}
              onChange={e => setField("owner_id", e.target.value)}
              style={{
                width: "100%", padding: "6px 10px", background: "#0b0c10",
                border: "1px solid #1e222d", color: "#e2e8f0", borderRadius: 6, fontSize: 11,
              }}
            >
              <option value="FOUNDER">👑 Founder (free for all)</option>
              {agents.map(a => (
                <option key={a.id} value={a.id}>{a.name_id} ({a.id})</option>
              ))}
            </select>
          </div>

          <div>
            <div style={{ fontSize: 9, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>
              PRICE PER USE (pts)
            </div>
            <input
              type="number" min="0"
              value={form.price}
              onChange={e => setField("price", parseInt(e.target.value) || 0)}
              style={{ width: "100%", padding: "6px 10px", background: "#0b0c10", border: "1px solid #1e222d", color: "#fbbf24", borderRadius: 6, fontSize: 12, fontFamily: "monospace", fontWeight: 700 }}
            />
            <div style={{ fontSize: 9, color: "#4b5563", marginTop: 4 }}>
              Non-owners pay this. Owner earns it. 0 = free.
            </div>
          </div>
        </div>

        {/* Save / Delete */}
        <div style={{ display: "flex", gap: 6 }}>
          <button
            onClick={saveTool}
            disabled={saving || !form.id || !form.name}
            style={{
              flex: 1, padding: "9px 0", fontWeight: 800, fontSize: 12,
              background: saved ? "#052e16" : (form.id && form.name ? "#4f46e5" : "#1a1d24"),
              color: saved ? "#4ade80" : "#fff",
              border: "none", borderRadius: 8, cursor: form.id && form.name ? "pointer" : "not-allowed",
              transition: "all 0.2s",
            }}
          >
            {saving ? "Saving…" : saved ? "✓ Saved!" : "💾 Save"}
          </button>
          {form.id && tools.find(t => t.id === form.id && t.is_custom) && (
            <button onClick={() => deleteTool(form.id)} style={{
              padding: "9px 14px", background: "#7f1d1d22", border: "1px solid #991b1b",
              color: "#fca5a5", borderRadius: 8, cursor: "pointer", fontSize: 12,
            }}>🗑</button>
          )}
        </div>

        {/* Preview */}
        {form.prompt_template && (
          <div style={{ background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "12px 14px" }}>
            <div style={{ fontSize: 9, fontWeight: 800, color: "#6b7280", letterSpacing: 1, marginBottom: 8 }}>TEMPLATE PREVIEW</div>
            <pre style={{
              margin: 0, fontSize: 10, color: "#67e8f9", fontFamily: "monospace",
              whiteSpace: "pre-wrap", lineHeight: 1.55, maxHeight: 140, overflowY: "auto",
            }}>
              {form.prompt_template}
            </pre>
          </div>
        )}

        {/* Test section */}
        <div style={{ background: "#09090e", border: "1px solid #1a1d24", borderRadius: 10, padding: "14px 14px" }}>
          <div style={{ fontSize: 9, fontWeight: 800, color: "#10b981", letterSpacing: 1, marginBottom: 10 }}>
            TEST AS AGENT
          </div>
          <select
            value={testAgentId}
            onChange={e => setTestAgent(e.target.value)}
            style={{ width: "100%", padding: "6px 10px", background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0", borderRadius: 6, fontSize: 11, marginBottom: 8 }}
          >
            <option value="">— select agent —</option>
            {agents.map(a => (
              <option key={a.id} value={a.id}>{a.name_id}</option>
            ))}
          </select>

          {form.args.map((a, i) => (
            <input
              key={i}
              placeholder={a.name || `arg_${i}`}
              value={testArgs[i] || ""}
              onChange={e => setTestArgs(prev => { const n = [...prev]; n[i] = e.target.value; return n; })}
              style={{ width: "100%", padding: "5px 8px", background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0", borderRadius: 5, fontSize: 11, marginBottom: 6 }}
            />
          ))}

          <div style={{ display: "flex", gap: 6 }}>
            <button
              onClick={runTest}
              disabled={testing || !testAgentId || !form.id}
              style={{
                flex: 1, padding: "7px 0", fontWeight: 700, fontSize: 11,
                background: testing ? "#064e3b" : "#065f46",
                color: "#4ade80", border: "1px solid #047857", borderRadius: 7,
                cursor: testAgentId && form.id ? "pointer" : "not-allowed",
              }}
            >
              {testing ? "⏳ Testing…" : "▶ Test"}
            </button>
            <button
              onClick={saveTool}
              disabled={saving || !form.id || !form.name}
              style={{
                flex: 1, padding: "7px 0", fontWeight: 700, fontSize: 11,
                background: "#1e1b4b", color: "#818cf8", border: "1px solid #4f46e5",
                borderRadius: 7, cursor: "pointer",
              }}
            >
              Create
            </button>
          </div>

          {testResult !== null && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 9, color: "#4b5563", fontWeight: 700, letterSpacing: 1, marginBottom: 4 }}>RESULT</div>
              <pre style={{
                background: "#040506", border: "1px solid #1a1d24", borderRadius: 6,
                padding: "8px 10px", fontSize: 10, color: "#4ade80",
                fontFamily: "monospace", whiteSpace: "pre-wrap", maxHeight: 160, overflowY: "auto",
              }}>
                {testResult}
              </pre>
            </div>
          )}
        </div>

        {/* Publish to Workshop */}
        {form.id && tools.find(t => t.id === form.id && t.is_custom) && (
          <button
            onClick={async () => {
              await fetch(`${API_BASE}/tools/${form.id}/publish`, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ownership_price: 0, price: form.price, category: "General" }),
              });
              fetchState();
            }}
            style={{
              padding: "9px", fontWeight: 700, fontSize: 11,
              background: "#0f2620", border: "1px solid #4ade8055",
              color: "#4ade80", borderRadius: 8, cursor: "pointer",
            }}
          >
            🔬 Submit to Workshop → Marketplace
          </button>
        )}
      </div>
    </div>
  );
}
