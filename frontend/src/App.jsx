import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { CT_VARS, CT_CONDS, CT_BUILTINS, CT_ACTIONS, Chip, CollapseSection, CThinkingToolbar, ToolWorkshop } from './WorkshopPanel.jsx';
import Marketplace from './Marketplace.jsx';
import './index.css';

const DEPT_META = {
  HF: { name: "Health & Wellness", color: "#4ade80", dim: "#052e16", icon: "🌱", id: "HF" },
  ING: { name: "Engineering", color: "#22d3ee", dim: "#0c2030", icon: "⚙️", id: "ING" },
  STP: { name: "Strategic Planning", color: "#fb923c", dim: "#2d1500", icon: "📊", id: "STP" },
  UIT: { name: "Useful Intelligence", color: "#c084fc", dim: "#1e0a30", icon: "🧠", id: "UIT" },
  FIN: { name: "Financing", color: "#fbbf24", dim: "#1c1600", icon: "💰", id: "FIN" },
};

const THREAD_COSTS = { Memo: 25, Strategy: 100, Endeavor: 100 };
const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/ws";

const mkId = () => Math.random().toString(36).slice(2, 8).toUpperCase();
const hhmm = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

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

const getStepColor = (type) => {
  switch (type) {
    case 'thought': return '#818cf8';
    case 'tool_call': return '#c084fc';
    case 'tool_result': return '#34d399';
    case 'wallet': return '#fbbf24';
    case 'memory': return '#2dd4bf';
    case 'iteration': return '#94a3b8';
    case 'error': return '#d61717ff';
    case 'complete': return '#10b981';
    default: return '#374151';
  }
};

// ── Run Item (Timeline) ──────────────────────────────────────────────────────
function RunItem({ run, isExp, onToggle, setFullScreenRunId }) {
  const dept = DEPT_META[run.dept] || { color: "#818cf8" };

  return (
    <div style={{
      background: isExp ? "#0d0f14" : "#11141a",
      border: `1px solid ${isExp ? "#4f46e5" : "#1a1d24"}`,
      boxShadow: isExp ? "0 4px 20px -5px rgba(0,0,0,0.5)" : "none",
      borderRadius: 10, padding: 12, marginBottom: 10,
      cursor: "pointer", transition: "all 0.2s"
    }} onClick={onToggle}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: dept.color }}>{run.agent}</span>
          <span style={{ fontSize: 9, padding: "2px 6px", background: dept.dim || "#1a1d24", color: dept.color, borderRadius: 4, fontWeight: 600 }}>{run.dept || "SYS"}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {isExp && (
            <button
              className="btn-ghost"
              onClick={(e) => {
                e.stopPropagation();
                setFullScreenRunId(run.id);
              }}
              style={{ padding: "2px 6px", borderRadius: 4, fontSize: 13, background: "#1a1d24" }}
              title="Full Screen View"
            >
              ⛶
            </button>
          )}
          <span className="mono" style={{ fontSize: 10, color: "#4b5563" }}>{hhmm(run.time)}</span>
        </div>
      </div>

      <div style={{ fontSize: 11, color: isExp ? "#d1d5db" : "#9ca3af", lineHeight: 1.5, overflow: "hidden", textOverflow: "ellipsis", display: isExp ? "block" : "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
        {run.msg}
      </div>

      {isExp && (
        <div style={{ marginTop: 15, paddingTop: 15, borderTop: "1px solid #1a1d24" }}>
          <div style={{ fontSize: 9, fontWeight: 800, color: "#4b5563", letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Run Activity Timeline</div>

          {run.steps?.map((s, idx) => (
            <div key={idx} style={{ position: "relative", paddingLeft: 24, paddingBottom: 16 }}>
              {/* Timeline Line */}
              {idx < run.steps.length - 1 && <div style={{ position: "absolute", left: 6, top: 12, bottom: 0, width: 2, background: "#1a1d24", borderRadius: 1 }} />}

              {/* Timeline Dot */}
              <div style={{
                position: "absolute", left: 0, top: 2, width: 14, height: 14,
                borderRadius: "50%", background: getStepColor(s.type),
                border: "3px solid #0d0f14", zIndex: 2
              }} />

              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, alignItems: "center" }}>
                <span style={{ fontSize: 9, fontWeight: 700, color: getStepColor(s.type), textTransform: "uppercase", letterSpacing: 0.5 }}>{s.type.replace('_', ' ')}</span>
                <span className="mono" style={{ fontSize: 9, color: "#374151" }}>{hhmm(s.time)}</span>
              </div>

              <div style={{ fontSize: 11, color: "#e2e8f0" }}>
                {s.type === 'thought' && (
                  <div>
                    <div style={{ fontStyle: "italic", color: "#6b7280", marginBottom: 6 }}>System prompt:</div>
                    {s.metadata?.system_prompt && (
                      <div style={{ fontSize: 9, color: "#4b5563", background: "#0b0c10", padding: 6, height: '300px', overflowY: 'scroll', borderRadius: 4, marginBottom: 6, border: "1px dashed #1a1d24" }}>
                        Prompt context: {s.metadata.system_prompt.slice(0, 3000)}...
                      </div>
                    )}
                    <div style={{ fontStyle: "italic", color: "#6b7280", marginBottom: 6 }}>User prompt:</div>
                    {s.metadata?.user_prompt && (
                      <div style={{ fontSize: 9, color: "#4b5563", background: "#0b0c10", padding: 6, height: '300px', overflowY: 'scroll', borderRadius: 4, marginBottom: 6, border: "1px dashed #1a1d24" }}>
                        Prompt context: {s.metadata.user_prompt.slice(0, 3000)}...
                      </div>
                    )}
                  </div>
                )}

                {s.type === 'tool_call' && (
                  <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#c084fc", fontWeight: 600 }}>
                    <span style={{ fontSize: 12 }}>🛠️</span> {s.metadata?.tool}
                    <span style={{ fontWeight: 400, color: "#6b7280", fontSize: 10 }}>({s.metadata?.args?.join(', ')})</span>
                  </div>
                )}

                {s.type === 'tool_result' && (
                  <div style={{ marginTop: 4 }}>
                    <div style={{ fontSize: 9, color: "#4b5563", marginBottom: 2 }}>Output for {s.metadata?.tool}:</div>
                    <pre style={{
                      background: "#070809", padding: "8px 10px", borderRadius: 6,
                      border: "1px solid #1e222d", overflowX: "auto", margin: 0,
                      boxShadow: "inset 0 2px 4px rgba(0,0,0,0.3)"
                    }}>
                      <code className="mono" style={{ fontSize: 10, color: "#34d399", lineHeight: 1.4 }}>
                        {s.metadata?.result || "No output returned."}
                      </code>
                    </pre>
                  </div>
                )}

                {s.type === 'response' && (
                  <div style={{ marginTop: 4, padding: 8, background: "#0b0c10", borderRadius: 6, border: "1px solid #1a1d24", color: "#9ca3af", maxHeight: 150, overflowY: "auto", fontSize: 10, lineHeight: 1.4, whiteSpace: "pre-wrap" }}>
                    {s.metadata?.raw}
                  </div>
                )}

                {s.type !== 'thought' && s.type !== 'tool_call' && s.type !== 'tool_result' && s.type !== 'response' && (
                  <div style={{ color: s.type === 'complete' ? '#10b981' : '#9ca3af' }}>{s.content}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Full-screen Run Details Modal ───────────────────────────────────────────
function RunDetailsModal({ run, onClose }) {
  useEffect(() => {
    const handleEsc = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleEsc);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handleEsc);
      document.body.style.overflow = "auto";
    };
  }, [onClose]);

  if (!run) return null;
  const dept = DEPT_META[run.dept] || { color: "#818cf8" };

  return (
    <div style={{
      position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh",
      background: "rgba(7, 8, 9, 0.95)", backdropFilter: "blur(12px)",
      zIndex: 10000, display: "flex", alignItems: "center", justifyContent: "center",
      padding: "40px", animation: "popin 0.3s cubic-bezier(0.16, 1, 0.3, 1)"
    }} onClick={onClose}>
      <div style={{
        width: "100%", maxWidth: 1000, height: "100%",
        background: "#0d0f14", border: "1px solid #1e222d",
        borderRadius: 16, overflow: "hidden", display: "flex", flexDirection: "column",
        boxShadow: "0 20px 50px rgba(0,0,0,0.5)",
      }} onClick={e => e.stopPropagation()}>

        {/* Modal Header */}
        <div style={{
          padding: "20px 24px", borderBottom: "1px solid #1a1d24",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          background: "#0b0c10"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 10, background: dept.dim || "#1a1d24",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20
            }}>
              {dept.icon || "📡"}
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>{run.agent} <span style={{ color: "#4b5563", fontWeight: 400, marginLeft: 8 }}>· {run.id}</span></div>
              <div style={{ fontSize: 11, color: dept.color, fontWeight: 600, letterSpacing: 0.5 }}>{DEPT_META[run.dept]?.name || "SYSTEM ENGINE"}</div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <span className="mono" style={{ fontSize: 12, color: "#4b5563" }}>{run.time ? new Date(run.time).toLocaleString() : ""}</span>
            <button className="btn-ghost" onClick={onClose} style={{ fontSize: 20, width: 36, height: 36, borderRadius: "50%" }}>✕</button>
          </div>
        </div>

        {/* Modal Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "30px 40px" }}>
          <div style={{ marginBottom: 30 }}>
            <div style={{ fontSize: 18, color: "#e2e8f0", lineHeight: 1.6, fontWeight: 500 }}>{run.msg}</div>
          </div>

          <div style={{ fontSize: 10, fontWeight: 800, color: "#4b5563", letterSpacing: 1.5, textTransform: "uppercase", marginBottom: 24, paddingBottom: 8, borderBottom: "1px solid #1a1d24" }}>Full Activity Timeline</div>

          <div style={{ display: "flex", flexDirection: "column" }}>
            {run.steps?.map((s, idx) => (
              <div key={idx} style={{ position: "relative", paddingLeft: 32, paddingBottom: 24 }}>
                {idx < run.steps.length - 1 && <div style={{ position: "absolute", left: 9, top: 16, bottom: 0, width: 2, background: "#1a1d24", borderRadius: 1 }} />}
                <div style={{
                  position: "absolute", left: 0, top: 4, width: 20, height: 20,
                  borderRadius: "50%", background: getStepColor(s.type),
                  border: "4px solid #0d0f14", zIndex: 2
                }} />

                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, alignItems: "center" }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: getStepColor(s.type), textTransform: "uppercase", letterSpacing: 1 }}>{s.type.replace('_', ' ')}</span>
                  <span className="mono" style={{ fontSize: 11, color: "#4b5563" }}>{hhmm(s.time)}</span>
                </div>

                <div style={{ fontSize: 13, color: "#9ca3af" }}>
                  {s.type === 'thought' && (
                    <div style={{ background: "#0b0c10", padding: 16, borderRadius: 10, border: "1px solid #1a1d24" }}>
                      <div style={{ fontStyle: "italic", color: "#6b7280", marginBottom: 10 }}>Intelligence validation & internal thought cycle...</div>
                      {s.metadata?.user_prompt && (
                        <div>
                          <div style={{ fontSize: 10, color: "#4b5563", marginBottom: 6, fontWeight: 600 }}>SYSTEM PROMPT</div>
                          <div style={{ fontSize: 12, color: "#4b5563", background: "#070809", padding: 12, borderRadius: 6, border: "1px dashed #1a1d24", lineHeight: 1.5 }}>
                            {s.metadata.system_prompt}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {s.type === 'thought' && (
                    <div style={{ background: "#0b0c10", padding: 16, borderRadius: 10, border: "1px solid #1a1d24" }}>
                      <div style={{ fontStyle: "italic", color: "#6b7280", marginBottom: 10 }}>Intelligence validation & internal thought cycle...</div>
                      {s.metadata?.user_prompt && (
                        <div>
                          <div style={{ fontSize: 10, color: "#4b5563", marginBottom: 6, fontWeight: 600 }}>PROMPT CONTEXT</div>
                          <div style={{ fontSize: 12, color: "#4b5563", background: "#070809", padding: 12, borderRadius: 6, border: "1px dashed #1a1d24", lineHeight: 1.5 }}>
                            {s.metadata.user_prompt}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {s.type === 'tool_call' && (
                    <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#c084fc", fontWeight: 600, fontSize: 14 }}>
                      <span style={{ fontSize: 18 }}>🛠️</span> Executing tool: <span style={{ color: "#fff" }}>{s.metadata?.tool}</span>
                      <span style={{ fontWeight: 400, color: "#6b7280", fontSize: 11 }}>(args: {s.metadata?.args?.join(', ') || "none"})</span>
                    </div>
                  )}

                  {s.type === 'tool_result' && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 10, color: "#4b5563", marginBottom: 6, fontWeight: 600 }}>OUTPUT FOR {s.metadata?.tool?.toUpperCase()}</div>
                      <pre style={{
                        background: "#070809", padding: "16px 20px", borderRadius: 10,
                        border: "1px solid #1e222d", overflowX: "auto", margin: 0,
                        boxShadow: "inset 0 4px 12px rgba(0,0,0,0.5)"
                      }}>
                        <code className="mono" style={{ fontSize: 12, color: "#34d399", lineHeight: 1.6 }}>
                          {s.metadata?.result || "No output returned."}
                        </code>
                      </pre>
                    </div>
                  )}

                  {s.type === 'response' && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 10, color: "#4b5563", marginBottom: 6, fontWeight: 600 }}>FINAL LLM RESPONSE</div>
                      <div style={{
                        padding: 20, background: "#0b0c10", borderRadius: 10,
                        border: "1px solid #1a1d24", color: "#e2e8f0",
                        fontSize: 13, lineHeight: 1.6, whiteSpace: "pre-wrap"
                      }}>
                        {s.metadata?.raw}
                      </div>
                    </div>
                  )}

                  {s.type !== 'thought' && s.type !== 'tool_call' && s.type !== 'tool_result' && s.type !== 'response' && (
                    <div style={{
                      fontSize: 14, color: s.type === 'complete' ? '#10b981' : '#9ca3af',
                      fontWeight: s.type === 'complete' ? 600 : 400
                    }}>
                      {s.content}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
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
  INFO: "#6b7280",
  TICK: "#3b82f6",
  LLM: "#a855f7",
  TOOL: "#f97316",
  POINT: "#10b981",
  WARN: "#eab308",
  ERROR: "#ef4444",
};

// ── Logger View ──────────────────────────────────────────────────────────────
function Logger({ liveLogs, state }) {
  const [filter, setFilter] = useState({ level: "", category: "", agent: "", search: "" });
  const [expanded, setExpanded] = useState(new Set());
  const [dbLogs, setDbLogs] = useState([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const bottomRef = useRef(null);

  // Fetch historical logs from DB on mount
  useEffect(() => {
    fetch(`${API_BASE}/logs?limit=400`)
      .then(r => r.json())
      .then(data => setDbLogs(Array.isArray(data) ? data.reverse() : []))
      .catch(() => { });
  }, []);

  // Merge live + db logs, newest first, deduplicated by time+event
  const seen = new Set();
  const merged = [...liveLogs, ...dbLogs].filter(l => {
    const key = `${l.time}|${l.event}|${l.agent_id}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  const filtered = merged.filter(l => {
    if (filter.level && l.level !== filter.level) return false;
    if (filter.category && l.category !== filter.category) return false;
    if (filter.agent && l.agent_id !== filter.agent) return false;
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
          try { details = typeof log.details === "string" ? JSON.parse(log.details) : (log.details || {}); } catch { }
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
  const [state, setState] = useState({ heartbeat: 0, departments: {}, agents: {}, threads: {}, prompts: {}, settings: {}, tools: {}, tickets: [] });
  const [runs, setRuns] = useState([]);
  const [logs, setLogs] = useState([]);   // live log stream from WebSocket
  const [expandedFeedId, setExpandedFeedId] = useState(null);
  const [fullScreenRunId, setFullScreenRunId] = useState(null);
  const [view, setView] = useState("dashboard");

  const fetchState = useCallback(async () => {
    // wait 100ms before fetching
    await new Promise(resolve => setTimeout(resolve, 600));
    try {
      const [stateRes, tktRes] = await Promise.all([
        fetch(`${API_BASE}/state`),
        fetch(`${API_BASE}/tickets`),
      ]);
      const body = await stateRes.json();
      const tkts = await tktRes.json();
      setState(s => ({ ...s, ...body, tickets: Array.isArray(tkts) ? tkts : [] }));
    } catch (e) { console.error("fetch state error", e); }
  }, []);

  useEffect(() => {
    fetchState();

    const ws = new WebSocket(WS_BASE);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "heartbeat") {
        setState(s => ({ ...s, heartbeat: data.counter }));
        if (data.counter % 100 === 0) fetchState();
      } else if (data.type === "run") {
        const item = data.run;
        setRuns(r => [item, ...r].slice(0, 60));
        // fetchState();
        if (data.counter % 100 === 0) fetchState();
      } else if (data.type === "log") {
        setLogs(l => [data.log, ...l].slice(0, 600));
      } else if (data.type === "thread_summary") {
        setState(s => {
          if (!s.threads[data.thread_id]) return s;
          return {
            ...s,
            threads: {
              ...s.threads,
              [data.thread_id]: { ...s.threads[data.thread_id], summary: data.summary }
            }
          };
        });
      }
    };
    return () => ws.close();
  }, [fetchState]);

  // Actions
  const createThread = useCallback(async (ownerAgentId, topic, aim) => {
    await fetch(`${API_BASE}/threads`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ topic, aim, owner_agent_id: ownerAgentId }) });
    fetchState();
  }, [fetchState]);
  const approveThread = useCallback(async (tid) => { await fetch(`${API_BASE}/threads/${tid}/approve`, { method: "POST" }); fetchState(); }, [fetchState]);
  const rejectThread = useCallback(async (tid) => { await fetch(`${API_BASE}/threads/${tid}/reject`, { method: "POST" }); fetchState(); }, [fetchState]);
  const deleteThread = useCallback(async (tid) => {
    if (window.confirm("Delete thread and all its messages?")) {
      await fetch(`${API_BASE}/threads/${tid}`, { method: "DELETE" });
      fetchState();
    }
  }, [fetchState]);
  const updateThread = useCallback(async (tid, payload) => {
    await fetch(`${API_BASE}/threads/${tid}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
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
  const addAgentPoints = useCallback(async (agentId, amount) => {
    await fetch(`${API_BASE}/agents/${agentId}/points`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ amount }) });
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
    { id: "glue", label: "Glue (Wiki)", icon: "🧠" },
    { id: "tools", label: "Agent Tools", icon: "🛠️" },
    { id: "marketplace", label: "Marketplace", icon: "🛒" },
    { id: "founder", label: "Economy", icon: "👑" },
    { id: "tickets", label: "Tickets", icon: "🎟️" },
    { id: "agenting", label: "Agenting", icon: "🧠" },
    { id: "logger", label: "System Logger", icon: "📋" },
    { id: "settings", label: "Settings", icon: "⚙️" },
  ];

  const logCount = logs.length;

  return (
    <div className="app-container">
      {/* LEFT SIDEBAR */}
      <div className="sidebar">
        <div className="logo-area">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, background: "linear-gradient(135deg,#6366f1,#a855f7)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
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
            const d = state.departments[id];
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
          {view === "dashboard" && <Dashboard state={state} />}
          {view === "agents" && <Agents state={state} createThread={createThread} updateAgent={updateAgent} setView={setView} />}
          {view === "departments" && <Departments state={state} updateAgent={updateAgent} />}
          {view === "chats" && <Chats state={state} fetchState={fetchState} />}
          {view === "threads" && <Threads state={state} approveThread={approveThread} rejectThread={rejectThread} deleteThread={deleteThread} updateThread={updateThread} postMessage={postMessage} />}
          {view === "glue" && <Glue state={state} fetchState={fetchState} />}
          {view === "tools" && <Tools state={state} fetchState={fetchState} />}
          {view === "marketplace" && <Marketplace agents={Object.values(state.agents || {})} />}
          {view === "founder" && <Founder state={state} addDeptPoints={addDeptPoints} addAgentPoints={addAgentPoints} />}
          {view === "tickets" && <Tickets state={state} fetchState={fetchState} />}
          {view === "agenting" && <Agenting state={state} updateAgent={updateAgent} />}
          {view === "logger" && <Logger liveLogs={logs} state={state} />}
          {view === "settings" && <Settings state={state} updateSetting={updateSetting} />}
        </div>
      </div>

      {/* RIGHT ACTIVITY PANEL */}
      <div className="right-panel">
        <div style={{ padding: 16, borderBottom: "1px solid #1a1d24", background: "#0b0c10", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#9ca3af", letterSpacing: 1.5, textTransform: "uppercase" }}>Agent Runs</div>
          <div style={{ fontSize: 9, background: "#1a1d24", color: "#6b7280", padding: "2px 6px", borderRadius: 4 }}>Live</div>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: 12 }}>
          {runs.length === 0 && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", opacity: 0.5 }}>
              <div style={{ fontSize: 24, marginBottom: 10 }}>📡</div>
              <div style={{ fontSize: 11, color: "#4b5563", textAlign: "center", letterSpacing: 0.5 }}>Listening for simulation events...</div>
            </div>
          )}
          {runs.map(r => (
            <RunItem
              key={r.id}
              run={r}
              isExp={expandedFeedId === r.id}
              onToggle={() => setExpandedFeedId(expandedFeedId === r.id ? null : r.id)}
              setFullScreenRunId={setFullScreenRunId}
            />
          ))}
        </div>
      </div>

      {fullScreenRunId && (
        <RunDetailsModal
          run={runs.find(r => r.id === fullScreenRunId)}
          onClose={() => setFullScreenRunId(null)}
        />
      )}
    </div>
  );
}

// ── Tickets ───────────────────────────────────────────────────────────────────
function Tickets({ state, fetchState }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ id: "", name: "", amount: "", expiry_date: "" });
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState("ALL"); // ALL | AVAILABLE | USED
  const tickets = state.tickets || [];

  const genId = () => {
    const rnd = Math.random().toString(36).slice(2, 5).toUpperCase();
    setForm(f => ({ ...f, id: `TKT-${rnd}-${String(Date.now()).slice(-3)}` }));
  };

  const createTicket = async () => {
    if (!form.id || !form.name || !form.amount) return;
    setSaving(true);
    await fetch(`${API_BASE}/tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, amount: parseInt(form.amount) }),
    });
    setSaving(false);
    setForm({ id: "", name: "", amount: "", expiry_date: "" });
    setShowForm(false);
    fetchState();
  };

  const deleteTicket = async (tid) => {
    if (!window.confirm(`Delete ticket ${tid}?`)) return;
    await fetch(`${API_BASE}/tickets/${tid}`, { method: "DELETE" });
    fetchState();
  };

  const isExpired = (t) => t.expiry_date && new Date(t.expiry_date) < new Date();

  const visible = tickets.filter(t => {
    if (filter === "AVAILABLE") return t.status === "UNUSED" && !isExpired(t);
    if (filter === "USED") return t.status === "USED";
    return true;
  });

  const unused = tickets.filter(t => t.status === "UNUSED" && !isExpired(t)).length;
  const used = tickets.filter(t => t.status === "USED").length;
  const expired = tickets.filter(t => t.status === "UNUSED" && isExpired(t)).length;

  const inputSt = {
    background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0",
    borderRadius: 6, padding: "8px 12px", fontSize: 12, width: "100%", outline: "none"
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, color: "#fff", fontSize: 20 }}>🎟️ Founder Tickets</h2>
          <div style={{ fontSize: 12, color: "#6b7280", marginTop: 5, display: "flex", gap: 14 }}>
            <span style={{ color: "#10b981", fontWeight: 600 }}>{unused} available</span>
            <span style={{ color: "#6b7280" }}>{used} used</span>
            {expired > 0 && <span style={{ color: "#ef4444" }}>{expired} expired</span>}
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(v => !v)}>
          {showForm ? "✕ Cancel" : "+ New Ticket"}
        </button>
      </div>

      {/* ── Add form ── */}
      {showForm && (
        <div className="card" style={{ marginBottom: 24, border: "1px solid #6366f1" }}>
          <div className="card-header" style={{ fontSize: 13, fontWeight: 700, color: "#818cf8" }}>
            Issue New Founder Ticket
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 16 }}>
              <div>
                <label style={{ display: "block", fontSize: 11, color: "#6b7280", marginBottom: 5, fontWeight: 600 }}>
                  TICKET ID *
                </label>
                <div style={{ display: "flex", gap: 6 }}>
                  <input value={form.id}
                    onChange={e => setForm(f => ({ ...f, id: e.target.value.toUpperCase() }))}
                    placeholder="TKT-VOX-001" style={inputSt} />
                  <button className="btn btn-soft" style={{ fontSize: 12, padding: "0 12px", flexShrink: 0 }}
                    onClick={genId} title="Auto-generate ID">⚡</button>
                </div>
                <div style={{ fontSize: 10, color: "#4b5563", marginTop: 4 }}>Unique mnemonic identifier</div>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 11, color: "#6b7280", marginBottom: 5, fontWeight: 600 }}>
                  OBJECTIVE NAME *
                </label>
                <input value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="Founder Objective: Neural Expansion" style={inputSt} />
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <label style={{ display: "block", fontSize: 11, color: "#6b7280", marginBottom: 5, fontWeight: 600 }}>
                  POINT VALUE *
                </label>
                <input type="number" min="1" value={form.amount}
                  onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
                  placeholder="250" style={inputSt} />
                <div style={{ fontSize: 10, color: "#4b5563", marginTop: 4 }}>
                  Transferred to thread wallet on use · 5× penalty on rejection
                </div>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 11, color: "#6b7280", marginBottom: 5, fontWeight: 600 }}>
                  EXPIRY DATE <span style={{ fontWeight: 400 }}>(optional)</span>
                </label>
                <input type="date" value={form.expiry_date}
                  onChange={e => setForm(f => ({ ...f, expiry_date: e.target.value }))}
                  style={inputSt} />
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
              <button className="btn btn-soft" onClick={() => setShowForm(false)}>Cancel</button>
              <button className="btn btn-primary"
                onClick={createTicket}
                disabled={saving || !form.id || !form.name || !form.amount}
                style={{ minWidth: 100 }}>
                {saving ? "Issuing…" : "🎟️ Issue Ticket"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Filter bar ── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {["ALL", "AVAILABLE", "USED"].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            style={{
              padding: "5px 14px", fontSize: 11, cursor: "pointer", borderRadius: 6, fontWeight: 600,
              background: filter === f ? "#6366f1" : "#11141a",
              border: `1px solid ${filter === f ? "#6366f1" : "#1e222d"}`,
              color: filter === f ? "#fff" : "#6b7280",
            }}>
            {f}
          </button>
        ))}
      </div>

      {/* ── Grid ── */}
      {visible.length === 0 && (
        <div style={{ textAlign: "center", color: "#4b5563", padding: 80, fontSize: 13 }}>
          {tickets.length === 0
            ? "No tickets yet — issue one with the button above."
            : "No tickets match this filter."}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
        {visible.map(t => {
          const exp = isExpired(t);
          const isUsed = t.status === "USED";
          const statusCol = isUsed ? "#6b7280" : exp ? "#ef4444" : "#10b981";
          const statusLbl = isUsed ? "USED" : exp ? "EXPIRED" : "AVAILABLE";

          return (
            <div key={t.id} className="card"
              style={{ opacity: (isUsed || exp) ? 0.65 : 1, borderTop: `3px solid ${statusCol}`, transition: "opacity 0.2s" }}>
              <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>

                {/* Name + badge */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontWeight: 700, color: "#e2e8f0", fontSize: 14, lineHeight: 1.4,
                      overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical"
                    }}>
                      {t.name}
                    </div>
                    <div className="mono" style={{ fontSize: 10, color: "#6366f1", marginTop: 3 }}>{t.id}</div>
                  </div>
                  <span style={{
                    fontSize: 9, fontWeight: 800, padding: "3px 8px", borderRadius: 4, letterSpacing: 0.8,
                    background: statusCol + "22", color: statusCol, border: `1px solid ${statusCol}55`,
                    flexShrink: 0, whiteSpace: "nowrap",
                  }}>{statusLbl}</span>
                </div>

                {/* Points */}
                <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
                  <span className="mono" style={{ fontSize: 32, fontWeight: 700, color: isUsed ? "#4b5563" : "#10b981" }}>
                    {t.amount}
                  </span>
                  <span style={{ fontSize: 12, color: "#6b7280" }}>pts</span>
                  {!isUsed && !exp && (
                    <span style={{ fontSize: 10, color: "#4b5563", marginLeft: 4 }}>
                      · ×5 rejection penalty
                    </span>
                  )}
                </div>

                {/* Meta rows */}
                <div style={{ borderTop: "1px solid #1a1d24", paddingTop: 10, display: "flex", flexDirection: "column", gap: 5 }}>
                  {[
                    ["Created", t.created ? new Date(t.created).toLocaleDateString() : "—", "#9ca3af"],
                    ["Expires", t.expiry_date ? new Date(t.expiry_date).toLocaleDateString() : "No expiry", exp ? "#ef4444" : "#9ca3af"],
                    ...(isUsed ? [["Used by", t.used_by_name || t.used_by || "—", "#818cf8"]] : []),
                  ].map(([label, val, col]) => (
                    <div key={label} style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                      <span style={{ color: "#6b7280" }}>{label}</span>
                      <span className="mono" style={{ color: col, fontWeight: isUsed && label === "Used by" ? 600 : 400 }}>{val}</span>
                    </div>
                  ))}
                </div>

                {/* Delete button for unused/unexpired */}
                {!isUsed && (
                  <button onClick={() => deleteTicket(t.id)}
                    style={{
                      padding: "6px 0", width: "100%", background: "none",
                      border: "1px solid #1e222d", borderRadius: 6, color: "#6b7280",
                      fontSize: 11, cursor: "pointer", transition: "all 0.15s",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = "#ef4444"; e.currentTarget.style.color = "#ef4444"; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = "#1e222d"; e.currentTarget.style.color = "#6b7280"; }}>
                    🗑 Delete Ticket
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Prompt Parser (Debugging) ─────────────────────────────────────────────────
const PARSER_PLACEHOLDERS = [
  { key: "available_tickets", desc: "List of all unused tickets", cat: "tickets", conditional: false },
  { key: "available_tickets_exist", desc: "\"Yes\" / \"No\" — any unused tickets?", cat: "tickets", conditional: true },
  { key: "pending_invitation", desc: "Pending invitations for this agent", cat: "invitations", conditional: false },
  { key: "pending_invitation_exist", desc: "\"Yes\" / \"No\" — invitations pending?", cat: "invitations", conditional: true },
  { key: "pending_quests", desc: "Join-quests awaiting owner approval", cat: "quests", conditional: false },
  { key: "pending_quests_exist", desc: "\"Yes\" / \"No\" — quests pending?", cat: "quests", conditional: true },
  { key: "invitation_status", desc: "Last quest/invite status string", cat: "invitations", conditional: false },
  { key: "exist_invitation_status", desc: "\"Yes\" / \"No\" — has invite history?", cat: "invitations", conditional: true },
];
const PARSER_FORMAT_VARS = [
  { key: "name", desc: "Agent name" },
  { key: "id", desc: "Agent ID" },
  { key: "wallet", desc: "Wallet balance (pts)" },
  { key: "dept", desc: "Department + balance" },
  { key: "memory", desc: "Agent memory scratchpad" },
  { key: "actions", desc: "Recent actions summary" },
  { key: "tools", desc: "Full tools block" },
  { key: "directives", desc: "Mode directives block" },
  { key: "message", desc: "Founder message (chat)" },
];
const CAT_COLORS = { tickets: "#10b981", invitations: "#818cf8", quests: "#f59e0b" };

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
  const [sel, setSel] = useState(null);
  const [draft, setDraft] = useState({});
  const [savedField, setSavedField] = useState(null);
  const agent = sel ? state.agents[sel] : null;

  useEffect(() => {
    if (agent) setDraft({ memory: agent.memory || "" });
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
                      {["Creator", "Points Accounter", "Investor", "Custom"].map(k => <option key={k} value={k}>{k}</option>)}
                    </select>
                    {agent.next_mode && (
                      <div style={{ fontSize: 11, color: "#6366f1", marginTop: 6 }}>→ Self-selecting: <strong>{agent.next_mode}</strong></div>
                    )}
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <div>
                      <label style={{ display: "block", fontSize: 11, marginBottom: 6, color: "#6b7280" }}>Lifecycle Status</label>
                      <button 
                        className={`btn ${agent.is_halted ? 'btn-soft' : 'btn-primary'}`} 
                        onClick={() => updateAgent(sel, { is_halted: !agent.is_halted })}
                        style={{ width: "100%", fontSize: 11, background: agent.is_halted ? "#450a0a" : "#064e3b", color: agent.is_halted ? "#fca5a5" : "#34d399", borderColor: agent.is_halted ? "#991b1b" : "#059669" }}
                      >
                        {agent.is_halted ? "▶ RESUME AGENT" : "⏸ SUSPEND AGENT"}
                      </button>
                    </div>
                    <div>
                      <label style={{ display: "block", fontSize: 11, marginBottom: 6, color: "#6b7280" }}>Tick Interval (s)</label>
                      <input 
                        type="number" 
                        min="1" 
                        value={agent.ticks} 
                        onChange={e => updateAgent(sel, { ticks: parseInt(e.target.value) || 1 })} 
                        style={{ width: "100%", background: "#0b0c10", border: "1px solid #1e222d", color: "#fff", padding: "6px 10px", borderRadius: 6 }}
                      />
                    </div>
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

// ── Agenting ─────────────────────────────────────────────────────────────────
function Agenting({ state, updateAgent }) {
  const agents = Object.values(state.agents || {});
  const [sel, setSel] = useState(agents[0]?.id || null);
  const [promptType, setPromptType] = useState("system_prompt"); // "system_prompt" | "user_prompt"
  const [tab, setTab] = useState("edit"); // "edit" | "parse"
  const [promptText, setPromptText] = useState("");
  const [selectedMode, setSelectedMode] = useState("Custom"); // "Creator" | "Points Accounter" | "Investor" | "Custom"
  const [parsedRes, setParsedRes] = useState(null);
  const [loading, setLoading] = useState(false);

  const selectedAgent = sel ? state.agents[sel] : null;

  useEffect(() => {
    if (selectedAgent) {
      const modeData = (selectedAgent.prompts || {})[selectedMode] || {};
      setPromptText(modeData[promptType] || "");
    }
  }, [sel, promptType, selectedMode, state.agents]);

  const handleSave = async () => {
    if (!sel) return;
    await updateAgent(sel, { [promptType]: promptText, edit_mode: selectedMode });
  };

  const handleParse = async () => {
    if (!sel || !promptText.trim()) return;
    setLoading(true); setParsedRes(null);
    try {
      const p = { thread_id: null };
      const modeData = (selectedAgent.prompts || {})[selectedMode] || {};
      if (promptType === "system_prompt") {
        p.system_prompt = promptText;
        p.user_prompt = modeData.user_prompt || "";
      } else {
        p.system_prompt = modeData.system_prompt || "";
        p.user_prompt = promptText;
      }
      const r = await fetch(`${API_BASE}/agents/${sel}/parse-prompt`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(p)
      });
      const data = await r.json();
      setParsedRes(data[promptType]);
    } catch (e) {
      setParsedRes("Error: " + e.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (tab === "parse") handleParse();
  }, [tab]);

  const handleExport = () => {
    const blob = new Blob([promptText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedAgent?.name_id || 'agent'}_${selectedMode}_${promptType}.cthinking`;
    a.click();
  };

  const handleImport = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setPromptText(ev.target.result);
    reader.readAsText(file);
  };

  const insertHelper = (text) => setPromptText(p => p + text);

  return (
    <div style={{ display: "flex", gap: 20, height: "100%" }}>
      {/* Left panel: Agents */}
      <div style={{ width: 220, flexShrink: 0, overflowY: "auto" }}>
        <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 600, letterSpacing: 1, marginBottom: 10, textTransform: "uppercase" }}>Select Agent</div>
        {agents.map(a => (
          <div key={a.id} onClick={() => setSel(a.id)} className="card"
            style={{ cursor: "pointer", marginBottom: 10, borderColor: sel === a.id ? "#6366f1" : "#1a1d24", background: sel === a.id ? "#1e1b4b" : "#11141a" }}>
            <div className="card-body" style={{ padding: "10px 12px" }}>
              <div style={{ fontWeight: 600, color: "#e2e8f0" }}>{a.name_id}</div>
              <div style={{ fontSize: 10, color: "#6b7280" }}>{a.department || "No Dept"}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Main panel */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {!sel ? (
          <div style={{ textAlign: "center", color: "#6b7280", marginTop: 100 }}>Select an agent to manage their prompt</div>
        ) : (
          <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            {/* Topbar */}
            <div className="card-header" style={{ padding: "12px 16px", borderBottom: "1px solid #1a1d24", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <span style={{ fontWeight: 600, color: "#fff", fontSize: 15 }}>{selectedAgent.name_id}</span>
                <div style={{ textTransform: "uppercase", fontSize: 10, color: "#6b7280", fontWeight: 700, marginLeft: 10 }}>Mode:</div>
                <select value={selectedMode} onChange={e => setSelectedMode(e.target.value)} style={{ padding: "4px 8px", background: "#11141a", color: "#f59e0b", border: "1px solid #78350f", borderRadius: 4, fontWeight: 600 }}>
                   {["Creator", "Points Accounter", "Investor", "Custom"].map(m => <option key={m} value={m}>{m}</option>)}
                </select>
                <div style={{ textTransform: "uppercase", fontSize: 10, color: "#6b7280", fontWeight: 700, marginLeft: 10 }}>Type:</div>
                <select value={promptType} onChange={e => { setPromptType(e.target.value); setTab("edit"); }} style={{ padding: "4px 8px", background: "#11141a", color: "#e2e8f0", border: "1px solid #1e222d", borderRadius: 4 }}>
                  <option value="system_prompt">System Prompt</option>
                  <option value="user_prompt">User Prompt</option>
                </select>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                {tab === "edit" && (
                  <>
                    <label className="btn btn-soft" style={{ fontSize: 11, cursor: "pointer", margin: 0 }}>
                      Import
                      <input type="file" accept=".cthinking,.txt,.md" style={{ display: "none" }} onChange={handleImport} />
                    </label>
                    <button className="btn btn-soft" style={{ fontSize: 11 }} onClick={handleExport}>Export</button>
                    <button className="btn btn-primary" onClick={handleSave}>Save</button>
                  </>
                )}
                <div style={{ display: "flex", background: "#11141a", border: "1px solid #1e222d", borderRadius: 6, overflow: "hidden" }}>
                  <button onClick={() => setTab("edit")} style={{ padding: "6px 12px", fontSize: 12, border: "none", cursor: "pointer", background: tab === "edit" ? "#6366f1" : "transparent", color: tab === "edit" ? "#fff" : "#9ca3af" }}>Edit</button>
                  <button onClick={() => setTab("parse")} style={{ padding: "6px 12px", fontSize: 12, border: "none", cursor: "pointer", background: tab === "parse" ? "#6366f1" : "transparent", color: tab === "parse" ? "#fff" : "#9ca3af" }}>Parse-Compile</button>
                </div>
              </div>
            </div>

            <div className="card-body" style={{ flex: 1, display: "flex", flexDirection: "column", padding: 0 }}>
              {tab === "edit" ? (
                <div style={{ display: "flex", flex: 1 }}>
                  {/* Editor */}
                  <textarea
                    value={promptText}
                    onChange={e => setPromptText(e.target.value)}
                    style={{ flex: 1, padding: 16, background: "#0a0b0e", color: "#e2e8f0", border: "none", resize: "none", fontSize: 13, outline: "none", fontFamily: "'JetBrains Mono', monospace" }}
                    placeholder={`Enter ${promptType === "system_prompt" ? "system" : "user"} prompt using {{variables}}...\n\nExample:\n{{tools}}\n\nCurrent Thread Goal: {{THREAD_GOAL}}`}
                  />
                  {/* Helper Sidebar */}
                  <div style={{ width: 250, borderLeft: "1px solid #1a1d24", background: "#11141a", padding: "16px", overflowY: "auto" }}>
                    <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 12 }}>Variables</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 20 }}>
                      {PARSER_PLACEHOLDERS.map(p => (
                        <button key={p.key} onClick={() => insertHelper(`{{${p.key}}}`)} title={p.desc} style={{ fontSize: 10, padding: "3px 8px", background: "#1e1b4b", color: "#a5b4fc", border: "1px solid #3730a3", borderRadius: 4, cursor: "pointer" }}>{`{{${p.key}}}`}</button>
                      ))}
                      <button onClick={() => insertHelper(`{{tools}}`)} title="Available Tools" style={{ fontSize: 10, padding: "3px 8px", background: "#1e1b4b", color: "#a5b4fc", border: "1px solid #3730a3", borderRadius: 4, cursor: "pointer" }}>{`{{tools}}`}</button>
                      <button onClick={() => insertHelper(`{{recent_actions}}`)} title="Recent Actions Summary" style={{ fontSize: 10, padding: "3px 8px", background: "#1e1b4b", color: "#a5b4fc", border: "1px solid #3730a3", borderRadius: 4, cursor: "pointer" }}>{`{{recent_actions}}`}</button>
                    </div>
                    <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 12 }}>Format Params</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 20 }}>
                      {PARSER_FORMAT_VARS.map(p => (
                        <button key={p.key} onClick={() => insertHelper(`{${p.key}}`)} title={p.desc} style={{ fontSize: 10, padding: "3px 8px", background: "#064e3b", color: "#34d399", border: "1px solid #065f46", borderRadius: 4, cursor: "pointer" }}>{`{${p.key}}`}</button>
                      ))}
                    </div>
                    <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 700, letterSpacing: 1, marginBottom: 12 }}>Common Tools</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 300, overflowY: "auto", paddingRight: 4 }}>
                      {Object.values(state.tools || {}).map(t => (
                        <div key={t.id} onClick={() => insertHelper(`\n[CALL_TOOL]\n{"tool":"${t.id}", "args":{}}\n[/CALL_TOOL]`)} style={{ fontSize: 10, padding: "6px 8px", background: "#1c1400", border: "1px solid #78350f", borderRadius: 4, cursor: "pointer", textAlign: "left" }}>
                          <div style={{ color: "#fbbf24", fontWeight: 600, marginBottom: 2 }}>{t.id}</div>
                          <div style={{ color: "#d97706", fontSize: 9, whiteSpace: "normal", lineHeight: 1.2 }}>{t.description.slice(0, 80)}{t.description.length > 80 ? "..." : ""}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ flex: 1, overflowY: "auto", padding: 20, background: "#08090c", borderTop: "1px solid #1a1d24", display: "flex", flexDirection: "column" }}>
                  {loading ? (
                    <div style={{ color: "#6366f1", textAlign: "center", marginTop: 40 }}>Compiling Prompt as {selectedAgent.name_id}...</div>
                  ) : (
                    <div style={{ color: "#d1d5db", whiteSpace: "pre-wrap", fontFamily: "'JetBrains Mono', monospace", fontSize: 12, lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: renderMd(parsedRes || "Nothing to preview") }} />
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Glue (Persistent Wiki) ──────────────────────────────────────────────────
function Glue({ state, fetchState }) {
  const [vaults, setVaults] = useState([]);
  const [selVault, setSelVault] = useState(null);
  const [pages, setPages] = useState([]);
  const [selPage, setSelPage] = useState(null); // { path: string, content: string }
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [activeTab, setActiveTab] = useState("browse"); // browse | search | ingest | query | git
  const [searchQuery, setSearchQuery] = useState("");
  const [searchRes, setSearchRes] = useState([]);
  const [gitStatus, setGitStatus] = useState(null);
  const [gitLog, setGitLog] = useState([]);
  const [gitDiff, setGitDiff] = useState("");
  const [ingestForm, setIngestForm] = useState({ mode: "text", title: "", content: "", url: "", filename: "" });
  const [queryInput, setQueryInput] = useState("");
  const [queryRes, setQueryRes] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchVaults();
  }, []);

  useEffect(() => {
    if (selVault) {
      loadPages();
      loadGitStatus();
    }
  }, [selVault]);

  const fetchVaults = async () => {
    const r = await fetch(`${API_BASE}/vaults`);
    const data = await r.json();
    setVaults(data);
    if (data.length > 0 && !selVault) setSelVault(data[0]);
  };

  const loadPages = async (cat = null) => {
    if (!selVault) return;
    setLoading(true);
    const url = `${API_BASE}/vaults/${selVault}/pages` + (cat ? `?category=${cat}` : "");
    const r = await fetch(url);
    const data = await r.json();
    setPages(data);
    setLoading(false);
  };

  const loadPage = async (path) => {
    setLoading(true);
    const r = await fetch(`${API_BASE}/vaults/${selVault}/pages/${path}`);
    const data = await r.json();
    setSelPage({ path, ...data });
    setEditContent(data.content || "");
    setIsEditing(false);
    setLoading(false);
  };

  const savePage = async () => {
    if (!selVault || !selPage) return;
    setLoading(true);
    await fetch(`${API_BASE}/vaults/${selVault}/pages/${selPage.path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: editContent })
    });
    setIsEditing(false);
    loadPage(selPage.path);
    loadGitStatus();
  };

  const doSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    const r = await fetch(`${API_BASE}/vaults/${selVault}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keywords: searchQuery })
    });
    setSearchRes(await r.json());
    setLoading(false);
  };

  const doQuery = async () => {
    if (!queryInput.trim()) return;
    setLoading(true);
    const r = await fetch(`${API_BASE}/vaults/${selVault}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: queryInput, save: true })
    });
    setQueryRes(await r.json());
    setLoading(false);
    loadPages("queries");
  };

  const doIngest = async () => {
    setLoading(true);
    await fetch(`${API_BASE}/vaults/${selVault}/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ingestForm)
    });
    setLoading(false);
    setIngestForm({ mode: "text", title: "", content: "", url: "", filename: "" });
    loadPages("sources");
    loadGitStatus();
  };

  const loadGitStatus = async () => {
    if (!selVault) return;
    const [stat, log, diff] = await Promise.all([
      fetch(`${API_BASE}/vaults/${selVault}/git/status`).then(r => r.json()),
      fetch(`${API_BASE}/vaults/${selVault}/git/log`).then(r => r.json()),
      fetch(`${API_BASE}/vaults/${selVault}/git/diff`).then(r => r.json()),
    ]);
    setGitStatus(stat);
    setGitLog(log.log || []);
    setGitDiff(diff.diff || "");
  };

  const commitChanges = async (msg) => {
    const text = msg || `Wiki update ${new Date().toISOString()}`;
    await fetch(`${API_BASE}/vaults/${selVault}/git/commit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    loadGitStatus();
  };

  const discardFile = async (path) => {
    if (!window.confirm(`Discard all unstaged changes to ${path}?`)) return;
    await fetch(`${API_BASE}/vaults/${selVault}/git/discard`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filepath: path })
    });
    loadGitStatus();
    if (selPage?.path === path) loadPage(path);
  };

  const inputStyle = { background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0", borderRadius: 6, padding: "8px 12px", fontSize: 12, width: "100%", outline: "none" };

  return (
    <div style={{ display: "flex", gap: 20, height: "calc(100vh - 120px)" }}>
      {/* Sidebar: Navigation + Tree */}
      <div style={{ width: 260, flexShrink: 0, display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="card glass">
          <div className="card-body" style={{ padding: 12 }}>
            <label style={{ fontSize: 10, color: "#4b5563", fontWeight: 700, letterSpacing: 1, marginBottom: 8, display: "block" }}>VAULT SELECTOR</label>
            <select value={selVault || ""} onChange={e => setSelVault(e.target.value)} style={{ width: "100%", fontSize: 12, border: "1px solid #3730a3", color: "#a5b4fc", background: "#1e1b4b11" }}>
              {vaults.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
            <button 
              onClick={() => {
                const name = window.prompt("New Vault ID (e.g. PROJECT_X):");
                if (name) {
                  fetch(`${API_BASE}/vaults`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id: name })
                  }).then(() => fetchVaults());
                }
              }}
              style={{ width: "100%", marginTop: 8, fontSize: 9, padding: "4px 0", background: "none", border: "1px dashed #3730a3", color: "#a5b4fc", borderRadius: 4, cursor: "pointer" }}
            >
              + Create New Vault
            </button>
          </div>
        </div>

        <div className="card glass" style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", borderBottom: "1px solid #1a1d24" }}>
            {[
              { id: "browse", icon: "📁", label: "Wiki" },
              { id: "search", icon: "🔍", label: "Find" },
              { id: "ingest", icon: "📥", label: "Add" },
              { id: "git", icon: "🌿", label: "Git" }
            ].map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                style={{
                  flex: 1, padding: "10px 0", fontSize: 10, background: activeTab === t.id ? "#1e1b4b" : "transparent",
                  color: activeTab === t.id ? "#818cf8" : "#4b5563", border: "none", cursor: "pointer", transition: "all 0.2s"
                }} title={t.label}>
                {t.icon}
              </button>
            ))}
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: 12 }}>
            {activeTab === "browse" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <div style={{ fontSize: 10, color: "#6b7280", fontWeight: 700, marginBottom: 8, display: "flex", justifyContent: "space-between" }}>
                    <span>COLLECTIONS</span>
                    <button onClick={() => loadPages()} style={{ background: "none", border: "none", color: "#6366f1", fontSize: 9, cursor: "pointer" }}>↻</button>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {["sources", "concepts", "entities", "syntheses", "queries"].map(c => (
                      <button key={c} onClick={() => loadPages(c)}
                        style={{ padding: "2px 6px", fontSize: 9, borderRadius: 4, background: "#11141a", border: "1px solid #1e222d", color: "#9ca3af", cursor: "pointer" }}>
                        {c}
                      </button>
                    ))}
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  {pages.length === 0 && <div style={{ fontSize: 11, color: "#374151" }}>No pages found.</div>}
                  {pages.map(p => {
                    const parts = p.path.split('/');
                    const name = parts[parts.length - 1];
                    const depth = parts.length - 1;
                    return (
                      <div key={p.path}
                        className={`wiki-tree-item ${selPage?.path === p.path ? 'active' : ''}`}
                        onClick={() => loadPage(p.path)}
                        style={{ paddingLeft: 8 + depth * 12 }}>
                        {p.path.endsWith('.md') ? "📄 " : "📁 "} {name.replace('.md', '')}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {activeTab === "search" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div style={{ display: "flex", gap: 6 }}>
                  <input placeholder="Keywords..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && doSearch()} style={inputStyle} />
                  <button onClick={doSearch} className="btn btn-primary" style={{ padding: "0 10px" }}>Go</button>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {searchRes.map(r => (
                    <div key={r.path} className="wiki-tree-item" onClick={() => loadPage(r.path)} style={{ fontSize: 11, padding: 8, background: "#11141a" }}>
                      <div style={{ color: "#818cf8", fontWeight: 600, marginBottom: 2 }}>{r.path}</div>
                      <div style={{ fontSize: 10, opacity: 0.7, whiteSpace: "normal" }}>{r.snippets?.[0] || "..."}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === "ingest" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div style={{ display: "flex", gap: 4 }}>
                  {["text", "url", "file"].map(m => (
                    <button key={m} onClick={() => setIngestForm({ ...ingestForm, mode: m })}
                      style={{ flex: 1, padding: "4px 0", fontSize: 9, borderRadius: 4, background: ingestForm.mode === m ? "#6366f1" : "transparent", border: "1px solid #2d3748", color: ingestForm.mode === m ? "#fff" : "#6b7280" }}>
                      {m.toUpperCase()}
                    </button>
                  ))}
                </div>
                {ingestForm.mode === "text" && (
                  <>
                    <input placeholder="Title..." value={ingestForm.title} onChange={e => setIngestForm({ ...ingestForm, title: e.target.value })} style={inputStyle} />
                    <textarea placeholder="Content..." rows={5} value={ingestForm.content} onChange={e => setIngestForm({ ...ingestForm, content: e.target.value })} style={inputStyle} />
                  </>
                )}
                {ingestForm.mode === "url" && (
                  <input placeholder="https://..." value={ingestForm.url} onChange={e => setIngestForm({ ...ingestForm, url: e.target.value })} style={inputStyle} />
                )}
                {ingestForm.mode === "file" && (
                  <input placeholder="filename in inbox..." value={ingestForm.filename} onChange={e => setIngestForm({ ...ingestForm, filename: e.target.value })} style={inputStyle} />
                )}
                <button onClick={doIngest} disabled={loading} className="btn btn-primary" style={{ width: "100%" }}>{loading ? "Ingesting..." : "Execute Ingest"}</button>
              </div>
            )}

            {activeTab === "git" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <div style={{ fontSize: 10, color: "#6b7280", fontWeight: 700, marginBottom: 8 }}>STAGED CHANGES</div>
                  {gitStatus?.files?.filter(f => f.staged).map(f => (
                    <div key={f.path} style={{ fontSize: 11, color: "#10b981", padding: "2px 0" }}>+ {f.path}</div>
                  ))}
                  <div style={{ fontSize: 10, color: "#6b7280", fontWeight: 700, marginTop: 12, marginBottom: 8 }}>UNSTAGED</div>
                  {gitStatus?.files?.filter(f => !f.staged).map(f => (
                    <div key={f.path} style={{ fontSize: 11, color: "#f87171", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span>M {f.path}</span>
                      <button onClick={() => discardFile(f.path)} style={{ background: "none", border: "none", color: "#ef4444", fontSize: 9, cursor: "pointer" }}>✖</button>
                    </div>
                  ))}
                </div>
                <button onClick={() => commitChanges()} className="btn btn-primary glass" style={{ borderColor: "#10b98155", color: "#10b981", background: "#064e3b11" }}>Commit Staged</button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content: Viewer / Query / Git Diff */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Top Header / Query Bar */}
        <div className="card glass" style={{ padding: "8px 16px", display: "flex", alignItems: "center", gap: 12 }}>
          <div className="recorder-pulse" style={{ opacity: loading ? 1 : 0.2 }} title={loading ? "Thinking..." : "Idle"}></div>
          <input placeholder="Ask the Wiki..." value={queryInput} onChange={e => setQueryInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && doQuery()}
            style={{ flex: 1, background: "none", border: "none", fontSize: 14, fontWeight: 500 }} />
          <button className="btn btn-soft" onClick={doQuery} disabled={loading} style={{ borderRadius: 20, padding: "4px 16px" }}>Query</button>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, position: "relative" }}>
          {queryRes ? (
            <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
              <div className="card-header">
                <div style={{ fontSize: 14, fontWeight: 700, color: "#818cf8" }}>Result for: {queryInput}</div>
                <button onClick={() => setQueryRes(null)} className="btn btn-ghost">✕</button>
              </div>
              <div className="card-body" style={{ flex: 1, overflowY: "auto", fontSize: 13, lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: renderMd(queryRes.answer) }} />
              {queryRes.sources && (
                <div style={{ padding: 12, borderTop: "1px solid #1a1d24", background: "#0b0c10", display: "flex", gap: 8, overflowX: "auto" }}>
                  {queryRes.sources.map(s => (
                    <button key={s} onClick={() => { setQueryRes(null); loadPage(s); }} className="btn btn-soft" style={{ fontSize: 10, whiteSpace: "nowrap" }}>{s}</button>
                  ))}
                </div>
              )}
            </div>
          ) : activeTab === "git" ? (
            <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", background: "#0b0c10", borderBottom: "1px solid #1a1d24" }}>
                <button className="btn-ghost" style={{ padding: "10px 20px", fontSize: 12, borderBottom: "2px solid #818cf8", color: "#818cf8" }}>Pending Diff</button>
                <button className="btn-ghost" style={{ padding: "10px 20px", fontSize: 12 }}>History</button>
              </div>
              <div className="card-body" style={{ flex: 1, overflowY: "auto", padding: 0 }}>
                <pre style={{ margin: 0, padding: 20, fontSize: 12, fontFamily: "'JetBrains Mono', monospace", lineHeight: 1.5 }}>
                  {gitDiff.split('\n').map((l, i) => (
                    <div key={i} className={l.startsWith('+') ? 'diff-add' : l.startsWith('-') ? 'diff-del' : ''}>{l}</div>
                  ))}
                  {!gitDiff && <div style={{ color: "#374151", textAlign: "center", marginTop: 40 }}>No differences to display.</div>}
                </pre>
              </div>
            </div>
          ) : selPage ? (
            <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column", border: isEditing ? "1px solid #6366f1" : "1px solid #1a1d24" }}>
              <div className="card-header" style={{ padding: "8px 16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 11, color: "#4b5563", fontWeight: 700 }}>{selPage.path}</span>
                  {selPage.metadata?.category && <span style={{ fontSize: 9, padding: "1px 5px", background: "#1e1b4b", color: "#818cf8", borderRadius: 4 }}>{selPage.metadata.category}</span>}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {isEditing ? (
                    <>
                      <button onClick={() => setIsEditing(false)} className="btn btn-ghost" style={{ fontSize: 11 }}>Cancel</button>
                      <button onClick={savePage} className="btn btn-primary" style={{ fontSize: 11 }}>Save Changes</button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => setIsEditing(true)} className="btn btn-soft" style={{ fontSize: 11 }}>Edit</button>
                      <button onClick={() => window.confirm("Delete page?") && fetch(`${API_BASE}/vaults/${selVault}/pages/${selPage.path}`, { method: "DELETE" }).then(() => { setSelPage(null); loadPages(); })} className="btn btn-ghost" style={{ fontSize: 11, color: "#ef4444" }}>Delete</button>
                    </>
                  )}
                </div>
              </div>
              <div className="card-body" style={{ flex: 1, overflowY: "auto", padding: 0 }}>
                {isEditing ? (
                  <MarkdownEditor value={editContent} onChange={setEditContent} rows={30} />
                ) : (
                  <div className="md-viewer" style={{ padding: 30 }} dangerouslySetInnerHTML={{ __html: renderMd(selPage.content) }} />
                )}
              </div>
              {selPage.backlinks?.length > 0 && !isEditing && (
                <div style={{ padding: "12px 20px", borderTop: "1px solid #1a1d24", background: "#0b0c10" }}>
                  <div style={{ fontSize: 10, color: "#4b5563", fontWeight: 700, marginBottom: 8 }}>BACKLINKS</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {selPage.backlinks.map(b => (
                      <button key={b} onClick={() => loadPage(b)} className="btn btn-soft" style={{ fontSize: 10 }}>{b}</button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#374151" }}>
              <div style={{ fontSize: 48, marginBottom: 20 }}>🧠</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>Wiki Workspace</div>
              <div style={{ fontSize: 11 }}>Select a page or query the knowledge base</div>
            </div>
          )}
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
  const [msg, setMsg] = useState("");
  const [sending, setSending] = useState(false);
  const [rightTab, setRightTab] = useState("ledger"); // "ledger" | "properties"
  const [refreshing, setRefreshing] = useState(false);
  const [q, setQ] = useState("");
  const [fStatus, setFStatus] = useState("");
  const [fAim, setFAim] = useState("");
  const [favOnly, setFavOnly] = useState(false);
  const msgEndRef = useRef(null);



  const thread = sel ? state.threads[sel] : null;

  const filteredDiscussion = useMemo(() =>
    thread?.messages_log?.filter(m => !m.what.startsWith("INVESTMENT")) || [],
    [thread?.messages_log]
  );

  const filteredLedger = useMemo(() =>
    thread?.messages_log?.filter(m => m.points !== 0).reverse() || [],
    [thread?.messages_log]
  );

  const milestonesLog = useMemo(() => {
    try {
      return JSON.parse(thread?.milestones_log || "[]");
    } catch (e) {
      console.log(e);
      return [];
    }
  }, [thread?.milestones_log]);

  const tArr = useMemo(() =>
    Object.values(state.threads)
      .filter(t => t.aim !== "Chat")
      .filter(t => {
        if (q && !t.topic.toLowerCase().includes(q.toLowerCase())) return false;
        if (fStatus && t.status !== fStatus) return false;
        if (fAim && t.aim !== fAim) return false;
        if (favOnly && !t.favourite_color) return false;
        return true;
      })
      .reverse(),
    [state.threads, q, fStatus, fAim, favOnly]
  );



  // const tArr = Object.values(state.threads)
  //   .filter(t => t.aim !== "Chat")
  //   .filter(t => {
  //     if (q && !t.topic.toLowerCase().includes(q.toLowerCase())) return false;
  //     if (fStatus && t.status !== fStatus) return false;
  //     if (fAim && t.aim !== fAim) return false;
  //     if (favOnly && !t.favourite_color) return false;
  //     return true;
  //   })
  //   .reverse();
  // const thread = sel ? state.threads[sel] : null;

  useEffect(() => {
    if (thread) { setNewTopic(thread.topic); setEditMode(false); }
  }, [sel]);

  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread?.messages_log?.length]);

  const saveTopic = () => { updateThread(sel, { topic: newTopic }); setEditMode(false); };

  const sendMsg = async () => {
    if (!msg.trim() || sending) return;
    setSending(true);
    await postMessage(sel, "FOUNDER", msg.trim());
    setMsg(""); setSending(false);
  };

  const refreshSummary = async () => {
    if (!sel || refreshing) return;
    setRefreshing(true);
    await fetch(`${API_BASE}/threads/${sel}/summarize`, { method: "POST" });
    setTimeout(() => setRefreshing(false), 3000);
  };

  // ── Thread list card status colour helper ────────────────────────────────
  const statusColor = (s) => ({
    OPEN: "#34d399", ACTIVE: "#60a5fa", APPROVED: "#a78bfa",
    REJECTED: "#f87171", FROZEN: "#94a3b8",
  }[s] || "#6b7280");

  const getVibeStyle = (t) => {
    let style = {};
    if (t.css_pattern === "grid") {
      style.backgroundImage = `radial-gradient(circle, ${t.color_theme || '#ffffff'}11 1px, transparent 1px)`;
      style.backgroundSize = "20px 20px";
    } else if (t.css_pattern === "cross") {
      style.backgroundImage = `linear-gradient(to right, ${t.color_theme || '#ffffff'}11 1px, transparent 1px), linear-gradient(to bottom, ${t.color_theme || '#ffffff'}11 1px, transparent 1px)`;
      style.backgroundSize = "20px 20px";
    }
    return style;
  };

  return (
    <div style={{ display: "flex", gap: 20, height: "100%" }}>

      {/* ── Left: thread list ── */}
      <div style={{ width: 300, flexShrink: 0, display: "flex", flexDirection: "column", gap: 10 }}>

        {/* Filter Bar */}
        <div className="card" style={{ padding: 10 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <input
              placeholder="Search topic..."
              value={q}
              onChange={e => setQ(e.target.value)}
              style={{ fontSize: 11, padding: "6px 10px", background: "#0b0c10" }}
            />
            <div style={{ display: "flex", gap: 4 }}>
              <select value={fStatus} onChange={e => setFStatus(e.target.value)} style={{ flex: 1, fontSize: 10, padding: 4 }}>
                <option value="">All Status</option>
                <option value="OPEN">OPEN</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="APPROVED">APPROVED</option>
                <option value="REJECTED">REJECTED</option>
                <option value="FROZEN">FROZEN</option>
              </select>
              <select value={fAim} onChange={e => setFAim(e.target.value)} style={{ flex: 1, fontSize: 10, padding: 4 }}>
                <option value="">All Aims</option>
                <option value="Memo">Memo</option>
                <option value="Strategy">Strategy</option>
                <option value="Endeavor">Endeavor</option>
              </select>
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10, cursor: "pointer", color: "#9ca3af" }}>
              <input type="checkbox" checked={favOnly} onChange={e => setFavOnly(e.target.checked)} />
              Favourites only
            </label>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto" }}>
          {tArr.map(t => (
            <div key={t.id} onClick={() => setSel(t.id)} className="card"
              style={{
                cursor: "pointer", marginBottom: 10,
                borderColor: sel === t.id ? (t.color_theme || "#6366f1") : (t.favourite_color || "#1a1d24"),
                background: sel === t.id ? (t.color_theme ? t.color_theme + "22" : "#1e1b4b") : "#11141a",
                boxShadow: t.favourite_color ? `0 0 10px ${t.favourite_color}33` : "none",
                position: "relative",
                overflow: "hidden",
                ...getVibeStyle(t)
              }}>
              <div className="card-body" style={{ padding: "10px 14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{
                    fontWeight: 600, color: "#e2e8f0", fontSize: 13,
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 170
                  }}>
                    {t.topic}
                  </span>
                  <span style={{
                    fontSize: 9, padding: "2px 6px", borderRadius: 4, flexShrink: 0,
                    background: statusColor(t.status) + "22", color: statusColor(t.status),
                    border: `1px solid ${statusColor(t.status)}44`, fontWeight: 700
                  }}>
                    {t.status}
                  </span>
                </div>
                <div style={{ fontSize: 10, color: "#6b7280", marginBottom: t.summary ? 6 : 0 }}>
                  {t.aim} · {t.point_wallet?.budget || 0}pt
                </div>
                {t.summary && (
                  <div style={{
                    fontSize: 10, color: "#4b5563", lineHeight: 1.4,
                    overflow: "hidden", display: "-webkit-box",
                    WebkitLineClamp: 2, WebkitBoxOrient: "vertical"
                  }}>
                    {t.summary}
                  </div>
                )}
                {/* Favorite Indicator */}
                {t.favourite_color && (
                  <div style={{ position: "absolute", bottom: 0, right: 0, width: 0, height: 0, borderStyle: "solid", borderWidth: "0 0 16px 16px", borderColor: `transparent transparent ${t.favourite_color} transparent`, opacity: 0.6 }} />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right: detail ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 14, minWidth: 0 }}>
        {!thread
          ? <div style={{ textAlign: "center", color: "#6b7280", marginTop: 100 }}>Select a thread</div>
          : (<>
            {/* ── Header card ── */}
            <div className="card">
              <div className="card-body">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    {editMode ? (
                      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                        <input value={newTopic} onChange={e => setNewTopic(e.target.value)}
                          style={{ fontSize: 18, fontWeight: 700, width: "100%", background: "#0b0c10" }} />
                        <button className="btn btn-primary" onClick={saveTopic}>Save</button>
                        <button className="btn btn-soft" onClick={() => setEditMode(false)}>Cancel</button>
                      </div>
                    ) : (
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <h2 style={{ margin: 0, color: thread?.color_theme || "#fff", fontSize: 20 }}>
                          {thread?.topic}
                        </h2>
                        <button onClick={() => setEditMode(true)}
                          style={{ background: "none", border: "none", color: "#6366f1", cursor: "pointer", fontSize: 13 }}>✎</button>

                        {/* Favorite Star */}
                        <div style={{ position: "relative", display: "inline-block" }}>
                          <button
                            style={{ background: "none", border: "none", color: thread.favourite_color || "#374151", cursor: "pointer", fontSize: 18 }}
                            onClick={() => {
                              const colors = [null, "#fbbf24", "#3b82f6", "#10b981", "#ef4444", "#a855f7"];
                              const idx = colors.indexOf(thread.favourite_color);
                              const next = colors[(idx + 1) % colors.length];
                              updateThread(sel, { favourite_color: next });
                            }}
                            title="Cycle Favorite Color"
                          >
                            ★
                          </button>
                        </div>
                      </div>
                    )}
                    <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 6, display: "flex", gap: 14, flexWrap: "wrap" }}>
                      <span>Owner: <b style={{ color: "#e2e8f0" }}>{state.agents[thread.owner_agent]?.name_id || thread.owner_agent}</b></span>
                      <span>Dept: <b style={{ color: DEPT_META[thread.owner_department]?.color || "#fff" }}>{thread.owner_department || "—"}</b></span>
                      <span>Aim: <b style={{ color: "#6366f1" }}>{thread.aim}</b></span>
                      {thread.thread_goal && <span>Goal: <b style={{ color: "#10b981" }}>{thread.thread_goal}</b></span>}
                      <span className="mono" style={{ color: "#4b5563" }}>{thread.id}</span>
                    </div>

                    {/* Vibe & Pattern Controls */}
                    <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center" }}>
                      <div style={{ fontSize: 9, color: "#4b5563", fontWeight: 700, letterSpacing: 1 }}>THREAD VIBE</div>
                      <input type="color" value={thread.color_theme || "#6366f1"} onChange={e => updateThread(sel, { color_theme: e.target.value })} style={{ width: 24, height: 24, padding: 0, border: "none", background: "none", cursor: "pointer" }} />
                      <select value={thread.css_pattern || "none"} onChange={e => updateThread(sel, { css_pattern: e.target.value })} style={{ fontSize: 9, padding: "2px 6px", background: "#0b0c10" }}>
                        <option value="none">Pattern: None</option>
                        <option value="grid">Grid Pattern</option>
                        <option value="cross">Cross Pattern</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 16 }}>
                    <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: "#10b981" }}>
                      {thread.point_wallet?.budget || 0} pt
                    </div>
                    <div style={{ fontSize: 9, color: "#6b7280", letterSpacing: 1, marginBottom: 8 }}>BUDGET</div>
                    <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                      {(thread.status === "OPEN" || thread.status === "ACTIVE") && (<>
                        <button className="btn" style={{ background: "#064e3b", color: "#34d399", fontSize: 10, padding: "4px 10px" }}
                          onClick={() => approveThread(sel)}>Approve</button>
                        <button className="btn" style={{ background: "#7f1d1d", color: "#f87171", fontSize: 10, padding: "4px 10px" }}
                          onClick={() => rejectThread(sel)}>Reject</button>
                      </>)}
                      <button className="btn" style={{ background: "#1a1d24", color: "#6b7280", fontSize: 10, padding: "4px 10px" }}
                        onClick={() => deleteThread(sel)}>Delete</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ── Goal & Milestone Banner ── */}
            {(thread.thread_goal || thread.current_milestone) && (
              <div style={{
                display: "flex", gap: 16, padding: "10px 16px",
                background: "linear-gradient(135deg, #064e3b22, #1e1b4b22)",
                border: "1px solid #1e222d", borderRadius: 10,
                alignItems: "center", flexWrap: "wrap",
              }}>
                {thread.thread_goal && (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 180 }}>
                    <span style={{ fontSize: 16 }}>🎯</span>
                    <div>
                      <div style={{ fontSize: 9, fontWeight: 800, color: "#6b7280", letterSpacing: 1.2, marginBottom: 2 }}>GOAL</div>
                      <div style={{ fontSize: 12, color: "#10b981", fontWeight: 600, lineHeight: 1.4 }}>{thread.thread_goal}</div>
                    </div>
                  </div>
                )}
                {thread.current_milestone && (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 180 }}>
                    <span style={{ fontSize: 16 }}>🏁</span>
                    <div>
                      <div style={{ fontSize: 9, fontWeight: 800, color: "#6b7280", letterSpacing: 1.2, marginBottom: 2 }}>CURRENT MILESTONE</div>
                      <div style={{ fontSize: 12, color: "#818cf8", fontWeight: 600, lineHeight: 1.4 }}>{thread.current_milestone}</div>
                    </div>
                  </div>
                )}
                {(() => {
                  try {

                    const log = JSON.parse(thread.milestones_log || "[]");
                    if (log.length > 0) return (
                      <div style={{ fontSize: 10, color: "#4b5563", display: "flex", alignItems: "center", gap: 4, flexShrink: 0 }}>
                        <span style={{ color: "#10b981", fontWeight: 700 }}>✓ {log.length}</span> achieved
                      </div>
                    );
                  } catch (e) { console.log(e); return null; }
                })()}
              </div>
            )}

            {/* ── Two-column body ── */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 14, flex: 1, overflow: "hidden" }}>

              {/* Discussion log */}
              <div className="card" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
                <div className="card-header" style={{ fontSize: 11, fontWeight: 800, color: "#6366f1", letterSpacing: 1.5 }}>
                  DISCUSSION LOG
                </div>
                <div className="card-body" style={{ flex: 1, overflowY: "auto", background: "#08090c" }}>
                  {filteredDiscussion.map((m, i) => {
                    const isFounder = m.who === "FOUNDER" || m.who === "Founder";
                    const isSystem = m.who === "SYSTEM";
                    const isMilestoneAchieved = isSystem && m.what.includes("MILESTONE ACHIEVED:");
                    if (isMilestoneAchieved) {
                      return (
                        <div key={i} style={{ marginBottom: 14, textAlign: "center" }}>
                          <div style={{
                            display: "inline-block", padding: "10px 20px",
                            background: "linear-gradient(135deg, #064e3b44, #065f4622)",
                            border: "1px solid #10b98144",
                            borderRadius: 10, maxWidth: "90%",
                          }}>
                            <div style={{ fontSize: 10, fontWeight: 800, color: "#10b981", letterSpacing: 1.5, marginBottom: 4 }}>✅ MILESTONE ACHIEVED</div>
                            <div style={{ fontSize: 13, color: "#34d399", fontWeight: 600 }}
                              dangerouslySetInnerHTML={{ __html: renderMd(m.what.replace(/✅ \*\*MILESTONE ACHIEVED:\*\*\s*/, "")) }} />
                            <div className="mono" style={{ fontSize: 9, color: "#4b5563", marginTop: 4 }}>{hhmm(m.when)}</div>
                          </div>
                        </div>
                      );
                    }
                    return (
                      <div key={i} style={{ marginBottom: 14 }}>
                        <div style={{
                          display: "flex", alignItems: "center", gap: 8, marginBottom: 3,
                          justifyContent: isFounder ? "flex-end" : "flex-start"
                        }}>
                          {!isFounder && (
                            <span style={{
                              fontWeight: 600, fontSize: 11,
                              color: isSystem ? "#f59e0b" : "#818cf8"
                            }}>
                              {isSystem ? "⚙ SYSTEM" : (state.agents[m.who]?.name_id || m.who)}
                            </span>
                          )}
                          <span className="mono" style={{ fontSize: 9, color: "#374151" }}>{hhmm(m.when)}</span>
                          {isFounder && <span style={{ fontWeight: 700, color: "#6366f1", fontSize: 11 }}>👑 FOUNDER</span>}
                        </div>
                        <div style={{
                          color: "#e2e8f0", padding: "9px 13px", fontSize: 12, lineHeight: 1.55,
                          backgroundColor: isFounder ? "#1e1b4b" : isSystem ? "#1c1400" : "#11141a",
                          border: `1px solid ${isFounder ? "#3730a3" : isSystem ? "#78350f" : "#1a1d24"}`,
                          borderRadius: isFounder ? "10px 2px 10px 10px" : "2px 10px 10px 10px",
                          marginLeft: isFounder ? "auto" : 0,
                          marginRight: isFounder ? 0 : "auto",
                          maxWidth: "88%",
                        }} dangerouslySetInnerHTML={{ __html: renderMd(m.what) }} />
                      </div>
                    );
                  })}
                  <div ref={msgEndRef} />
                </div>
                <div style={{
                  padding: "9px 12px", borderTop: "1px solid #1a1d24",
                  display: "flex", gap: 8, background: "#0a0b0e"
                }}>
                  <input placeholder="Post as Founder… (Enter to send)"
                    value={msg}
                    onChange={e => setMsg(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMsg()}
                    style={{ flex: 1, fontSize: 12, padding: "6px 10px" }} disabled={sending} />
                  <button className="btn btn-primary" onClick={sendMsg}
                    disabled={sending || !msg.trim()} style={{ fontSize: 12, padding: "0 14px" }}>
                    {sending ? "…" : "Post"}
                  </button>
                </div>
              </div>

              {/* Right panel: tab switcher */}
              <div className="card" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
                {/* Tab bar */}
                <div style={{ display: "flex", borderBottom: "1px solid #1a1d24", background: "#0b0c10" }}>
                  {[["ledger", "💰 Ledger"], ["properties", "📋 Properties"]].map(([id, lbl]) => (
                    <button key={id} onClick={() => setRightTab(id)} style={{
                      flex: 1, padding: "9px 4px", fontSize: 10, cursor: "pointer", fontWeight: 700,
                      background: rightTab === id ? "#11141a" : "transparent",
                      border: "none", borderBottom: `2px solid ${rightTab === id ? "#6366f1" : "transparent"}`,
                      color: rightTab === id ? "#e2e8f0" : "#6b7280", letterSpacing: 0.5,
                      transition: "all 0.15s",
                    }}>{lbl}</button>
                  ))}
                </div>

                {/* ── Ledger tab ── */}
                {rightTab === "ledger" && (
                  <div style={{ flex: 1, overflowY: "auto", background: "#0a0b0e", padding: "0 0 8px" }}>
                    {filteredLedger.map((m, i) => (
                      <div key={i} style={{ padding: "9px 14px", borderBottom: "1px solid #111316" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                          <span style={{
                            fontSize: 11, fontWeight: 600, color: "#e2e8f0",
                            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 170
                          }}>
                            {m.what.replace("INVESTMENT: ", "")}
                          </span>
                          <span className="mono" style={{
                            fontSize: 12, fontWeight: 700, flexShrink: 0,
                            color: m.points > 0 ? "#10b981" : "#ef4444"
                          }}>
                            {m.points > 0 ? "+" : ""}{m.points}
                          </span>
                        </div>
                        <div style={{ fontSize: 10, color: "#4b5563" }}>
                          {hhmm(m.when)} · {state.agents[m.who]?.name_id || m.who}
                        </div>
                      </div>
                    ))}
                    {!thread.messages_log?.some(m => m.points !== 0) && (
                      <div style={{ textAlign: "center", color: "#374151", fontSize: 12, marginTop: 40 }}>
                        No financial history
                      </div>
                    )}
                  </div>
                )}

                {/* ── Properties tab ── */}
                {rightTab === "properties" && (
                  <div style={{ flex: 1, overflowY: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 14 }}>

                    {/* Vault Link */}
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 800, color: "#9ca3af", letterSpacing: 1, marginBottom: 8 }}>GLUE LINK</div>
                      <select 
                        value={thread.vault_id || ""} 
                        onChange={e => updateThread(sel, { vault_id: e.target.value })}
                        style={{ width: "100%", fontSize: 12, border: "1px solid #3730a3", color: "#a5b4fc", background: "#1e1b4b11" }}
                      >
                        <option value="">None (Standalone)</option>
                        <option value="HF">HF (Health & Wellness)</option>
                        <option value="ING">ING (Engineering)</option>
                        <option value="STP">STP (Strategic Planning)</option>
                        <option value="UIT">UIT (Useful Intel)</option>
                        <option value="FIN">FIN (Financing)</option>
                      </select>
                      <div style={{ fontSize: 9, color: "#4b5563", marginTop: 4 }}>Messages from this thread will be logged to the linked vault index.</div>
                    </div>

                    {/* Summary */}
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                        <div style={{ fontSize: 10, fontWeight: 800, color: "#6366f1", letterSpacing: 1 }}>AI SUMMARY</div>
                        <button onClick={refreshSummary} disabled={refreshing}
                          style={{
                            fontSize: 10, padding: "3px 10px", cursor: "pointer",
                            background: "#1e1b4b", border: "1px solid #4338ca",
                            borderRadius: 5, color: refreshing ? "#4b5563" : "#a5b4fc"
                          }}>
                          {refreshing ? "⏳ Generating…" : "↻ Refresh"}
                        </button>
                      </div>
                      <div style={{
                        background: "#08090c", border: "1px solid #1e222d",
                        borderRadius: 8, padding: 12, fontSize: 12, color: "#d1d5db", lineHeight: 1.6,
                        minHeight: 60,
                      }}>
                        {thread.summary
                          ? thread.summary
                          : <span style={{ color: "#374151", fontStyle: "italic", height: '300px', overflowY: "auto" }}>
                            No summary yet — post a message or click Refresh.
                          </span>}
                      </div>
                    </div>

                    {/* Owner */}
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 800, color: "#9ca3af", letterSpacing: 1, marginBottom: 8 }}>OWNER</div>
                      {(() => {
                        const owner = state.agents[thread.owner_agent];
                        if (!owner) return <div style={{ fontSize: 12, color: "#4b5563" }}>Unknown</div>;
                        const deptMeta = DEPT_META[owner.department];
                        return (
                          <div style={{
                            background: "#11141a", border: "1px solid #1e222d",
                            borderRadius: 8, padding: "10px 12px", display: "flex", alignItems: "center", gap: 10
                          }}>
                            <div style={{
                              width: 34, height: 34, borderRadius: 8, flexShrink: 0,
                              background: (deptMeta?.color || "#6366f1") + "22",
                              border: `1px solid ${deptMeta?.color || "#6366f1"}44`,
                              display: "flex", alignItems: "center", justifyContent: "center",
                              fontSize: 16
                            }}>
                              {deptMeta?.icon || "🤖"}
                            </div>
                            <div>
                              <div style={{ fontWeight: 700, color: "#e2e8f0", fontSize: 13 }}>
                                {owner.is_ceo ? "★ " : ""}{owner.name_id}
                              </div>
                              <div style={{ fontSize: 10, color: "#6b7280", marginTop: 2 }}>
                                {owner.department || "No Dept"} · {owner.wallet?.current || 0} pts
                              </div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>

                    {/* Collaborators */}
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 800, color: "#9ca3af", letterSpacing: 1, marginBottom: 8 }}>
                        MEMBERS ({thread.collaborators?.length || 0})
                      </div>
                      {(!thread.collaborators || thread.collaborators.length === 0) ? (
                        <div style={{ fontSize: 11, color: "#374151", fontStyle: "italic" }}>No collaborators yet.</div>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          {thread.collaborators.map(aid => {
                            const ag = state.agents[aid];
                            const dm = ag ? DEPT_META[ag.department] : null;
                            return (
                              <div key={aid} style={{
                                background: "#11141a", border: "1px solid #1e222d",
                                borderRadius: 6, padding: "8px 10px", display: "flex", alignItems: "center", gap: 8
                              }}>
                                <div style={{
                                  width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                                  background: dm?.color || "#6b7280"
                                }} />
                                <div>
                                  <div style={{ fontSize: 12, fontWeight: 600, color: "#d1d5db" }}>
                                    {ag?.name_id || aid}
                                  </div>
                                  <div style={{ fontSize: 10, color: "#6b7280" }}>
                                    {ag?.department || "—"} · {ag?.wallet?.current || 0} pts
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Thread metadata */}
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 800, color: "#9ca3af", letterSpacing: 1, marginBottom: 8 }}>METADATA</div>
                      <div style={{ background: "#08090c", border: "1px solid #1e222d", borderRadius: 8, overflow: "hidden" }}>
                        {[
                          ["Thread ID", thread.id],
                          ["Created", thread.created ? new Date(thread.created).toLocaleString() : "—"],
                          ["Aim", thread.aim],
                          ["Goal", thread.thread_goal || "No goal set"],
                          ["Milestone", thread.current_milestone || "No milestone set"],
                          ["Status", thread.status],
                          ["Budget", `${thread.point_wallet?.budget || 0} pts`],
                          ["Messages", thread.messages_log?.length || 0],
                        ].map(([label, val]) => (
                          <div key={label} style={{
                            display: "flex", justifyContent: "space-between",
                            padding: "7px 12px", borderBottom: "1px solid #111316"
                          }}>
                            <span style={{ fontSize: 11, color: "#6b7280" }}>{label}</span>
                            <span className="mono" style={{ fontSize: 11, color: label === "Goal" ? "#10b981" : label === "Milestone" ? "#818cf8" : "#9ca3af" }}>{val}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Milestones History */}
                    {(() => {
                      try {
                        const log = JSON.parse(thread.milestones_log || "[]");
                        if (log.length === 0) return null;
                        return (
                          <div>
                            <div style={{ fontSize: 10, fontWeight: 800, color: "#10b981", letterSpacing: 1, marginBottom: 8 }}>
                              MILESTONES ACHIEVED ({log.length})
                            </div>
                            <div style={{ background: "#08090c", border: "1px solid #1e222d", borderRadius: 8, overflow: "hidden" }}>
                              {log.slice().reverse().map((ms, idx) => (
                                <div key={idx} style={{
                                  padding: "8px 12px", borderBottom: "1px solid #111316",
                                  display: "flex", justifyContent: "space-between", alignItems: "center",
                                }}>
                                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                    <span style={{ color: "#10b981", fontSize: 12 }}>✓</span>
                                    <span style={{ fontSize: 11, color: "#d1d5db", fontWeight: 500 }}>{ms.text}</span>
                                  </div>
                                  <span className="mono" style={{ fontSize: 9, color: "#4b5563", flexShrink: 0 }}>
                                    {ms.achieved_at ? new Date(ms.achieved_at).toLocaleString() : "—"}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      } catch (e) {
                        console.log(e)
                        return null;
                      }
                    })()}
                  </div>
                )}
              </div>
            </div>
          </>)}
      </div>
    </div>
  );


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
                      {thread.thread_goal && <span>Goal: <b style={{ color: "#10b981" }}>{thread.thread_goal}</b></span>}
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
                  {thread.messages_log?.filter(m => !m.what.startsWith("INVESTMENT")).map((m, i) => {
                    const isFounder = m.who === "FOUNDER";
                    const isSystem = m.who === "SYSTEM";
                    return (
                      <div key={i} style={{ marginBottom: 16 }}>
                        <div style={{
                          display: "flex", alignItems: "center", gap: 8, marginBottom: 4,
                          justifyContent: isFounder ? "flex-end" : "flex-start"
                        }}>
                          {!isFounder && (
                            <span style={{ fontWeight: 600, color: isSystem ? "#f59e0b" : "#818cf8", fontSize: 12 }}>
                              {isSystem ? "⚙ SYSTEM" : (state.agents[m.who]?.name_id || m.who)}
                            </span>
                          )}
                          <span className="mono" style={{ fontSize: 10, color: "#4b5563" }}>{hhmm(m.when)}</span>
                          {isFounder && (
                            <span style={{ fontWeight: 700, color: "#6366f1", fontSize: 12 }}>👑 FOUNDER</span>
                          )}
                        </div>
                        <div style={{
                          color: "#e2e8f0",
                          backgroundColor: isFounder ? "#1e1b4b" : isSystem ? "#1c1400" : "#11141a",
                          padding: "10px 14px",
                          borderRadius: isFounder ? "10px 2px 10px 10px" : "2px 10px 10px 10px",
                          fontSize: 13, border: `1px solid ${isFounder ? "#3730a3" : isSystem ? "#78350f" : "#1a1d24"}`,
                          lineHeight: 1.5,
                          marginLeft: isFounder ? "auto" : 0,
                          marginRight: isFounder ? 0 : "auto",
                          maxWidth: "85%",
                        }}
                          dangerouslySetInnerHTML={{ __html: renderMd(m.what) }} />
                      </div>
                    );
                  })}
                  <div ref={msgEndRef} />
                </div>
                {/* ── Founder compose bar ── */}
                <div style={{ padding: "10px 14px", borderTop: "1px solid #1a1d24", display: "flex", gap: 8, background: "#0a0b0e" }}>
                  <input
                    placeholder="Post as Founder…"
                    value={msg}
                    onChange={e => setMsg(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMsg()}
                    style={{ flex: 1, fontSize: 12, padding: "7px 12px" }}
                    disabled={sending}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={sendMsg}
                    disabled={sending || !msg.trim()}
                    style={{ fontSize: 12, padding: "0 16px", flexShrink: 0 }}
                  >
                    {sending ? "…" : "Post"}
                  </button>
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
function Departments({ state, updateAgent }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 20 }}>
      {Object.entries(DEPT_META).map(([id, meta]) => {
        const dept = state.departments[id];
        if (!dept) return null;
        const allA = dept.agents?.map(aid => state.agents[aid]).filter(Boolean) || [];
        const ceo = allA.find(a => a.is_ceo);
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
                    <div style={{ opacity: ceo.is_halted ? 0.5 : 1 }}>
                      <span style={{ fontSize: 10, fontWeight: 700, color: meta.color, letterSpacing: 1 }}>CEO  </span>
                      <span style={{ fontWeight: 600, color: "#fff", fontSize: 13 }}>{ceo.name_id}</span>
                      {ceo.is_halted && <span style={{ fontSize: 9, marginLeft: 8, background: "#450a0a", color: "#fca5a5", padding: "1px 6px", borderRadius: 4, fontWeight: 700 }}>HALTED</span>}
                    </div>
                    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                      <button 
                        onClick={() => updateAgent(ceo.id, { is_halted: !ceo.is_halted })}
                        style={{ background: "none", border: "none", cursor: "pointer", fontSize: 14, padding: 0, opacity: 0.8 }}
                        title={ceo.is_halted ? "Resume" : "Suspend"}
                      >
                        {ceo.is_halted ? "▶️" : "⏸️"}
                      </button>
                      <span style={{ fontSize: 11, color: "#818cf8", background: "#1e1b4b", padding: "2px 8px", borderRadius: 4 }}>{ceo.mode}</span>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 16, marginTop: 6, fontSize: 11, color: "#6b7280", opacity: ceo.is_halted ? 0.5 : 1 }}>
                    <span>Wallet: <span style={{ color: "#10b981" }}>{ceo.wallet?.current ?? 0} pts</span></span>
                    <span>Ticks: {ceo.ticks}s</span>
                    {ceo.next_mode && <span style={{ color: "#6366f1" }}>→ {ceo.next_mode}</span>}
                  </div>
                  {ceo.memory && <div style={{ marginTop: 6, fontSize: 11, color: "#4b5563", fontStyle: "italic", opacity: ceo.is_halted ? 0.5 : 1 }}>💭 {ceo.memory.slice(0, 80)}</div>}
                </div>
              )}
              {members.length > 0 && <div style={{ fontSize: 10, color: "#374151", fontWeight: 600, letterSpacing: 1 }}>MEMBERS</div>}
              {members.map(a => (
                <div key={a.id} style={{ background: "#0d0f14", border: "1px solid #1a1d24", borderRadius: 6, padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ opacity: a.is_halted ? 0.5 : 1 }}>
                    <div style={{ fontWeight: 500, color: "#e2e8f0", fontSize: 12 }}>
                      {a.name_id}
                      {a.is_halted && <span style={{ fontSize: 8, marginLeft: 6, background: "#450a0a", color: "#fca5a5", padding: "1px 4px", borderRadius: 3, fontWeight: 700 }}>HALTED</span>}
                    </div>
                    <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>
                      Wallet: <span style={{ color: "#10b981" }}>{a.wallet?.current ?? 0}</span> · Tick: {a.ticks}s
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    <button 
                      onClick={() => updateAgent(a.id, { is_halted: !a.is_halted })}
                      style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, padding: 0, opacity: 0.8 }}
                      title={a.is_halted ? "Resume" : "Suspend"}
                    >
                      {a.is_halted ? "▶️" : "⏸️"}
                    </button>
                    <span style={{ fontSize: 11, color: "#9ca3af", background: "#1a1d24", padding: "2px 8px", borderRadius: 4 }}>{a.mode}</span>
                  </div>
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
function Founder({ state, addDeptPoints, addAgentPoints }) {
  // console.log(state.agents)
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
      <div className="card-header" style={{ fontSize: 14, fontWeight: 600, color: "#fff" }}>Agent Wallets</div>
      <div className="card-body">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }}>
          {Object.entries(state.agents).map(([_, agent]) => {
            const current = agent.wallet?.current || 0;
            // department for the agent
            const dept = Object.values(DEPT_META).find(d => d.id === agent.department);
            return (
              <div key={agent.id} style={{ background: "#0a0b0e", border: "1px solid #1a1d24", borderRadius: 8, padding: 16 }}>
                <div style={{ color: dept?.color, fontWeight: 600, marginBottom: 12 }}>{agent.name_id}</div>
                <div className="mono" style={{ fontSize: 24, color: "#fff", marginBottom: 16 }}>{current} pts</div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-soft" style={{ flex: 1 }} onClick={() => addAgentPoints(agent.id, 10)}>+10</button>
                  <button className="btn btn-soft" style={{ flex: 1 }} onClick={() => addAgentPoints(agent.id, 50)}>+50</button>
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
  const [sel, setSel] = useState(null);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const chatThreads = Object.values(state.threads).filter(t => t.aim === "Chat");
  const agents = Object.values(state.agents);
  const selectedAgent = state.agents[sel];
  const activeThread = chatThreads.find(t => t.owner_agent == sel);

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
  const [tab, setTab] = useState("capabilities");
  const tools = Object.values(state.tools || {});
  const agents = Object.values(state.agents || {});

  const tabBtn = (id, lbl) => (
    <button key={id} onClick={() => setTab(id)} style={{
      padding: "7px 18px", fontSize: 12, cursor: "pointer", borderRadius: 6, fontWeight: 600,
      background: tab === id ? "#6366f1" : "#11141a",
      border: `1px solid ${tab === id ? "#6366f1" : "#1e222d"}`,
      color: tab === id ? "#fff" : "#6b7280", transition: "all 0.15s",
    }}>{lbl}</button>
  );

  return (
    <div>
      <div style={{ display: "flex", gap: 6, marginBottom: 24, borderBottom: "1px solid #1a1d24", paddingBottom: 12 }}>
        {tabBtn("capabilities", "🛠️ Capabilities")}
        {tabBtn("workshop", "⚗️ Workshop")}
        {tabBtn("economy", "💸 Economy")}
      </div>
      {tab === "capabilities" && <ToolCapabilities tools={tools} agents={agents} state={state} fetchState={fetchState} />}
      {tab === "workshop" && <ToolWorkshop tools={tools} agents={agents} state={state} fetchState={fetchState} />}
      {tab === "economy" && <ToolEconomy state={state} />}
    </div>
  );
}

// ── ToolCapabilities (existing tools grid) ────────────────────────────────────
function ToolCapabilities({ tools, agents, state, fetchState }) {
  const [instr, setInstr] = useState(state.settings?.tools_instruction_prefix || "");
  const [testTool, setTestTool] = useState(null);

  useEffect(() => {
    if (state.settings?.tools_instruction_prefix !== undefined) setInstr(state.settings.tools_instruction_prefix);
  }, [state.settings?.tools_instruction_prefix]);

  const toggleTool = async (tid, cur) => {
    await fetch(`${API_BASE}/tools/${tid}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled: !cur }) });
    fetchState();
  };
  const saveInstr = async () => {
    await fetch(`${API_BASE}/settings/tools_instruction_prefix`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value: instr }) });
    fetchState();
  };
  const deleteTool = async (tid) => {
    if (!window.confirm(`Delete custom tool "${tid}"?`)) return;
    await fetch(`${API_BASE}/tools/${tid}`, { method: "DELETE" });
    fetchState();
  };

  const ICONS = {
    modify_own_tick: "⏱️", get_time: "🕐", get_weather: "🌤️", get_news: "📰",
    get_thread_summary: "📝", get_all_summaries: "📋", get_threads: "🗂️", get_agents: "👥",
    join_thread: "🤝", create_thread: "➕", invest_thread: "💰", change_owner: "🔑", get_owner: "👁️",
    produce_transaction: "💸"
  };
  const enabled = tools.filter(t => t.enabled);

  const ownerLabel = (t) => {
    if (!t.owner_id) return null;
    const ag = Object.values(state.agents || {}).find(a => a.id === t.owner_id);
    return ag ? ag.name_id : t.owner_id;
  };

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ display: "flex", gap: 32, marginBottom: 32, alignItems: "stretch" }}>
        <div style={{ flex: 1 }}>
          <div className="card" style={{ padding: 20 }}>
            <label style={{ fontSize: 10, color: "#6366f1", fontWeight: 800, letterSpacing: 1.5, display: "block", marginBottom: 10, textTransform: "uppercase" }}>Global Tool Instruction Prompt</label>
            <textarea value={instr} onChange={e => setInstr(e.target.value)} style={{ height: 100, width: "100%", fontSize: 12, padding: 12, marginBottom: 12, background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0", borderRadius: 8 }} />
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button className="btn btn-primary" onClick={saveInstr} disabled={instr === state.settings?.tools_instruction_prefix}>Save Prompt</button>
            </div>
          </div>
        </div>
        <div style={{ width: 360 }}>
          <label style={{ fontSize: 10, color: "#9ca3af", fontWeight: 800, letterSpacing: 1.5, display: "block", marginBottom: 10, textTransform: "uppercase" }}>Context Preview</label>
          <div className="card" style={{ background: "#0b0c10", padding: 14, border: "1px dashed #1e222d", height: "calc(100% - 30px)", overflow: "auto" }}>
            <pre style={{ whiteSpace: "pre-wrap", fontSize: 10, color: "#6b7280", lineHeight: 1.5, margin: 0, fontFamily: "monospace" }}>
              {`${instr}\n\n${enabled.map(t => `- ${t.description}`).join("\n") || "No tools."}`}
            </pre>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(290px, 1fr))", gap: 16 }}>
        {tools.map(t => {
          const owner = ownerLabel(t);
          return (
            <div key={t.id} className="card" style={{ opacity: t.enabled ? 1 : 0.55, borderTop: t.is_custom ? "2px solid #6366f1" : undefined }}>
              <div className="card-header" style={{ justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div style={{ width: 30, height: 30, borderRadius: 7, background: t.is_custom ? "#1e1b4b" : (t.enabled ? "#1a1d24" : "#111"), display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span style={{ fontSize: 14 }}>{t.is_custom ? "⚗️" : (ICONS[t.id] || "🔧")}</span>
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, color: "#fff", fontSize: 13 }}>{t.name}</div>
                    <div className="mono" style={{ fontSize: 9, color: "#6366f1" }}>{t.id}</div>
                  </div>
                </div>
                <div onClick={() => toggleTool(t.id, t.enabled)}
                  style={{ width: 40, height: 20, borderRadius: 100, background: t.enabled ? "#6366f1" : "#1a1d24", position: "relative", cursor: "pointer", transition: "all 0.3s", border: "1px solid #1e222d", flexShrink: 0 }}>
                  <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#fff", position: "absolute", top: 2, left: t.enabled ? 22 : 3, transition: "all 0.3s" }} />
                </div>
              </div>
              <div className="card-body">
                <div style={{ fontSize: 11, color: "#9ca3af", lineHeight: 1.5, marginBottom: 10 }}>{t.description?.slice(0, 120)}</div>
                {(owner || t.price > 0) && (
                  <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
                    {owner && <span style={{ fontSize: 9, padding: "2px 7px", borderRadius: 4, background: "#1e1b4b", color: "#818cf8", border: "1px solid #3730a3" }}>👤 {owner}</span>}
                    {t.price > 0 && <span style={{ fontSize: 9, padding: "2px 7px", borderRadius: 4, background: "#064e3b", color: "#34d399", border: "1px solid #065f46" }}>💰 {t.price} pts/use</span>}
                  </div>
                )}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 10, borderTop: "1px solid #1a1d24" }}>
                  <span style={{ fontSize: 10, color: "#4b5563" }}>
                    {t.is_custom ? <span style={{ color: "#818cf8" }}>Custom</span> : "Built-in"} · <span style={{ color: t.enabled ? "#10b981" : "#ef4444" }}>{t.enabled ? "ON" : "OFF"}</span>
                  </span>
                  <div style={{ display: "flex", gap: 6 }}>
                    <button className="btn btn-soft" style={{ fontSize: 10, padding: "3px 9px" }} onClick={() => setTestTool(t)}>Test</button>
                    {t.is_custom && <button onClick={() => deleteTool(t.id)} style={{ fontSize: 10, padding: "3px 9px", cursor: "pointer", background: "none", border: "1px solid #1e222d", borderRadius: 5, color: "#6b7280" }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = "#ef4444"; e.currentTarget.style.color = "#ef4444"; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = "#1e222d"; e.currentTarget.style.color = "#6b7280"; }}>🗑</button>}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {testTool && <ToolTesterModal tool={testTool} agents={agents} onClose={() => setTestTool(null)} />}
    </div>
  );
}

// ── ToolWorkshop ───────────────────────────────────────────────────────────────
const TOOL_ACTIONS = [
  { id: "http_get", label: "HTTP GET", desc: "Fetch a URL — use [HTTP_GET:url] in prompt" },
  { id: "http_post", label: "HTTP POST", desc: "POST to URL — [HTTP_POST:url]body[END_HTTP]" },
  { id: "create_file", label: "Create File", desc: "Write file — [CREATE_FILE:name]content[END_FILE]" },
  { id: "read_file", label: "Read File", desc: "Read file — [READ_FILE:name]" },
];
const AGENT_VARS = [
  "{agent_name}", "{agent_id}", "{agent_wallet}", "{agent_dept}", "{agent_memory}",
];
const ACTION_SNIPPETS = {
  http_get: "[HTTP_GET:https://example.com/api]",
  http_post: "[HTTP_POST:https://example.com/api]\n{\"key\":\"value\"}\n[END_HTTP]",
  create_file: "[CREATE_FILE:output.txt]\nYour content here\n[END_FILE]",
  read_file: "[READ_FILE:output.txt]",
};

// ── ToolWorkshop is now in WorkshopPanel.jsx ─────────────────────────────────
function ToolEconomy({ state }) {
  const [txns, setTxns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/transactions?limit=150`)
      .then(r => r.json()).then(d => { setTxns(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const tools = Object.values(state.tools || {});
  const customTools = tools.filter(t => t.is_custom);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 20, maxWidth: 1200, margin: "0 auto" }}>
      {/* Transaction ledger */}
      <div className="card" style={{ display: "flex", flexDirection: "column" }}>
        <div className="card-header" style={{ fontSize: 12, fontWeight: 700, color: "#10b981" }}>
          Transaction Ledger
          <span style={{ fontSize: 10, color: "#374151", fontWeight: 400, marginLeft: 8 }}>{txns.length} records</span>
        </div>
        <div style={{ flex: 1, overflowY: "auto", maxHeight: "calc(100vh - 280px)" }}>
          {loading && <div style={{ padding: 40, textAlign: "center", color: "#6b7280" }}>Loading…</div>}
          {!loading && txns.length === 0 && <div style={{ padding: 40, textAlign: "center", color: "#374151" }}>No transactions yet.</div>}
          {txns.map(t => (
            <div key={t.id} style={{ padding: "9px 16px", borderBottom: "1px solid #111316", display: "flex", alignItems: "center", gap: 12 }}>
              <span className="mono" style={{ fontSize: 9, color: "#2d3748", minWidth: 64 }}>
                {t.created ? new Date(t.created).toLocaleTimeString() : "—"}
              </span>
              <span style={{ fontSize: 11, color: "#818cf8", minWidth: 90, fontWeight: 600 }}>{t.from_name}</span>
              <span style={{ fontSize: 10, color: "#374151" }}>→</span>
              <span style={{ fontSize: 11, color: "#34d399", minWidth: 90, fontWeight: 600 }}>{t.to_name}</span>
              <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: "#10b981", minWidth: 60 }}>+{t.amount} pt</span>
              <span style={{ fontSize: 10, color: "#4b5563", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.reason}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tool ownership overview */}
      <div className="card" style={{ display: "flex", flexDirection: "column" }}>
        <div className="card-header" style={{ fontSize: 12, fontWeight: 700, color: "#818cf8" }}>Custom Tool Ownership</div>
        <div style={{ flex: 1, overflowY: "auto", padding: "0 0 8px" }}>
          {customTools.length === 0 && <div style={{ padding: 40, textAlign: "center", color: "#374151" }}>No custom tools yet.</div>}
          {customTools.map(t => {
            const owner = t.owner_id ? (Object.values(state.agents || {}).find(a => a.id === t.owner_id)?.name_id || t.owner_id) : "👑 Founder";
            return (
              <div key={t.id} style={{ padding: "12px 16px", borderBottom: "1px solid #111316" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, color: "#e2e8f0", fontSize: 13 }}>⚗️ {t.name}</span>
                  {t.price > 0 && <span style={{ fontSize: 11, color: "#34d399", fontWeight: 700 }}>{t.price} pts/use</span>}
                </div>
                <div className="mono" style={{ fontSize: 9, color: "#6366f1", marginBottom: 4 }}>{t.id}</div>
                <div style={{ fontSize: 11, color: "#6b7280" }}>
                  Owner: <span style={{ color: "#818cf8", fontWeight: 600 }}>{owner}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Settings ──────────────────────────────────────────────────────────────────
function Settings({ state, updateSetting }) {
  const [ollamaModel, setOllamaModel] = useState("");
  const [ollamaServer, setOllamaServer] = useState("");
  const [llmHalt, setLlmHalt] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [saved, setSaved] = useState(false);
  const [settingsTab, setSettingsTab] = useState("general");
  const [tavilyApiKeys, setTavilyApiKeys] = useState("");

  useEffect(() => {
    if (state.settings) {
      if (state.settings.ollama_model !== undefined) setOllamaModel(state.settings.ollama_model);
      if (state.settings.ollama_server !== undefined) setOllamaServer(state.settings.ollama_server);
      if (state.settings.llm_halt !== undefined) setLlmHalt(state.settings.llm_halt === "true");
      if (state.settings.tavily_api_keys !== undefined) setTavilyApiKeys(state.settings.tavily_api_keys);
    }
  }, [state.settings]);

  const fetchModels = async () => {
    setLoadingModels(true);
    try {
      const r = await fetch(`${API_BASE}/ollama-models`);
      const b = await r.json();
      if (b.status === "success") setAvailableModels(b.models);
    } catch { }
    setLoadingModels(false);
  };
  useEffect(() => { fetchModels(); }, []);

  const saveSettings = async () => {
    await updateSetting("ollama_model", ollamaModel);
    await updateSetting("ollama_server", ollamaServer);
    await updateSetting("llm_halt", llmHalt ? "true" : "false");
    await updateSetting("tavily_api_keys", tavilyApiKeys);
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
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <div className="card" style={{ maxWidth: 640 }}>
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
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <input type="checkbox" id="llmHaltCheckbox" checked={llmHalt} onChange={e => setLlmHalt(e.target.checked)} style={{ width: 16, height: 16, cursor: "pointer" }} />
            <label htmlFor="llmHaltCheckbox" style={{ fontSize: 13, color: "#e2e8f0", cursor: "pointer", fontWeight: 500 }}>
              Halt LLM Calls
              <span style={{ display: "block", fontSize: 11, color: "#9ca3af", fontWeight: 400, marginTop: 2 }}>Pauses all agents' LLM API requests while keeping the engine running</span>
            </label>
          </div>
          <div>
            <label style={{ display: "block", fontSize: 12, marginBottom: 6, color: "#9ca3af", fontWeight: 500 }}>Tavily API Keys (Comma or space separated)</label>
            <textarea
              value={tavilyApiKeys}
              onChange={e => setTavilyApiKeys(e.target.value)}
              placeholder="tvly-xxx, tvly-yyy"
              style={{ width: "100%", height: 80, background: "#0b0c10", border: "1px solid #1e222d", color: "#e2e8f0", borderRadius: 8, padding: 12, fontSize: 12 }}
            />
            <div style={{ fontSize: 11, color: "#4b5563", marginTop: 6 }}>One key will be picked randomly for each search request.</div>
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
    </div>
  );
}