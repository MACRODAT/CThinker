"""
marketplace_tools.py  –  100+ CTHINKING marketplace tool definitions.
Each tool is a dict matching the AgentTool model + marketplace fields.
status = "MARKETPLACE"  → published, owned by FOUNDER, buyable by agents.
"""

MARKETPLACE_TOOLS = [

# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY: INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════

{
  "id": "get_market_pulse",
  "name": "Market Pulse",
  "category": "Intelligence",
  "ownership_price": 60,
  "price": 3,
  "tags": '["intel","economy","overview"]',
  "description": (
    "*/\n- get_market_pulse\n/*\n"
    "Returns a full ecosystem snapshot: active threads, top agents, economy status."
  ),
  "prompt_template": (
    "📊 MARKET PULSE — {agent}  |  Time: */get_time/*\n\n"
    "=== ACTIVE THREADS ===\n{thread_summary}\n\n"
    "=== MY WALLET ===\nBalance: {wallet} pts\n\n"
    "=== AVAILABLE TICKETS ===\n"
    "{{ available_tickets_exist\n"
    "  Tickets: {available_tickets}\n"
    "  /ELSE/\n"
    "  No unused tickets.\n"
    "}}\n\n"
    "=== PENDING INVITATIONS ===\n"
    "{{ pending_invitation_exist\n"
    "  {pending_invitation}\n"
    "  /ELSE/\n"
    "  No pending invitations.\n"
    "}}"
  ),
  "args_definition": "[]",
},

{
  "id": "get_agent_info",
  "name": "Agent Intel",
  "category": "Intelligence",
  "ownership_price": 40,
  "price": 2,
  "tags": '["intel","agent","profile"]',
  "description": (
    "*/\n- get_agent_info\n- AGENT_ID\n/*\n"
    "Returns full profile of an agent: wallet, department, threads, mode."
  ),
  "prompt_template": "*/get_agent_info|{arg_0}/*",
  "args_definition": '[{"name":"agent_id","description":"ID of the agent to inspect"}]',
},

{
  "id": "get_thread_detail",
  "name": "Thread Telescope",
  "category": "Intelligence",
  "ownership_price": 35,
  "price": 2,
  "tags": '["intel","thread","detail"]',
  "description": (
    "*/\n- get_thread_detail\n- THREAD_ID\n/*\n"
    "Detailed thread stats: budget, collaborators, summary, status, age."
  ),
  "prompt_template": "*/get_thread_info|{arg_0}/*",
  "args_definition": '[{"name":"thread_id","description":"Thread ID to inspect"}]',
},

{
  "id": "get_agent_ranking",
  "name": "Wealth Leaderboard",
  "category": "Intelligence",
  "ownership_price": 45,
  "price": 2,
  "tags": '["intel","ranking","wealth"]',
  "description": (
    "*/\n- get_agent_ranking\n/*\n"
    "List all agents ranked by current wallet balance."
  ),
  "prompt_template": "*/get_agent_ranking/*",
  "args_definition": "[]",
},

{
  "id": "get_dept_ranking",
  "name": "Department Power Index",
  "category": "Intelligence",
  "ownership_price": 45,
  "price": 2,
  "tags": '["intel","ranking","departments"]',
  "description": (
    "*/\n- get_dept_ranking\n/*\n"
    "Rank departments by current ledger balance."
  ),
  "prompt_template": "*/get_dept_ranking/*",
  "args_definition": "[]",
},

{
  "id": "collaboration_map",
  "name": "Collaboration Web",
  "category": "Intelligence",
  "ownership_price": 55,
  "price": 3,
  "tags": '["intel","collaboration","network"]',
  "description": (
    "*/\n- collaboration_map\n/*\n"
    "Show all active thread collaborations across agents and departments."
  ),
  "prompt_template": "*/get_collaboration_map/*",
  "args_definition": "[]",
},

{
  "id": "analyze_thread",
  "name": "Thread Analyst",
  "category": "Intelligence",
  "ownership_price": 70,
  "price": 4,
  "tags": '["intel","analysis","strategy"]',
  "description": (
    "*/\n- analyze_thread\n- THREAD_ID\n/*\n"
    "Deep analysis: viability, burn rate, collaboration health, recommendations."
  ),
  "prompt_template": (
    "🔬 THREAD ANALYSIS: {arg_0}\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "=== THREAD SUMMARY ===\n"
    "*/get_thread_summary|{arg_0}/*\n\n"
    "=== RECOMMENDATION ===\n"
    "Based on the data above, assess whether this thread merits further investment.\n"
    "Consider: budget vs. activity, number of collaborators, topic relevance."
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread ID to analyze"}]',
},

{
  "id": "opportunity_radar",
  "name": "Opportunity Radar",
  "category": "Intelligence",
  "ownership_price": 80,
  "price": 5,
  "tags": '["intel","investment","opportunities"]',
  "description": (
    "*/\n- opportunity_radar\n/*\n"
    "Scan all open threads for investment opportunities. Highlights low-budget, high-value targets."
  ),
  "prompt_template": (
    "🎯 OPPORTUNITY RADAR — {agent}\n\n"
    "=== OPEN THREADS (scan) ===\n{thread_summary}\n\n"
    "=== MY WALLET ===\nBalance: {wallet} pts\n\n"
    "Look for threads with: low budget but strong topic, few collaborators, strategic AIM.\n"
    "Identify top 3 investment candidates from the list above."
  ),
  "args_definition": "[]",
},

{
  "id": "get_recent_tx",
  "name": "Transaction Ledger",
  "category": "Intelligence",
  "ownership_price": 30,
  "price": 1,
  "tags": '["intel","transactions","finance"]',
  "description": (
    "*/\n- get_recent_tx\n/*\n"
    "View the 10 most recent point transactions in the ecosystem."
  ),
  "prompt_template": "*/get_recent_transactions/*",
  "args_definition": "[]",
},

{
  "id": "economic_snapshot",
  "name": "Economic Snapshot",
  "category": "Intelligence",
  "ownership_price": 90,
  "price": 5,
  "tags": '["intel","economy","big-picture"]',
  "description": (
    "*/\n- economic_snapshot\n/*\n"
    "Full ecosystem economy report: total points, department balances, top threads."
  ),
  "prompt_template": (
    "💹 ECONOMIC SNAPSHOT — */get_time/*\n\n"
    "=== DEPT RANKING ===\n*/get_dept_ranking/*\n\n"
    "=== AGENT RANKING ===\n*/get_agent_ranking/*\n\n"
    "=== ACTIVE THREADS ===\n{thread_summary}\n\n"
    "=== RECENT TRANSACTIONS ===\n*/get_recent_transactions/*"
  ),
  "args_definition": "[]",
},

{
  "id": "risk_scanner",
  "name": "Risk Scanner",
  "category": "Intelligence",
  "ownership_price": 65,
  "price": 4,
  "tags": '["intel","risk","protection"]',
  "description": (
    "*/\n- risk_scanner\n/*\n"
    "Identify threads at risk of freezing, agents near bankruptcy, and failing quests."
  ),
  "prompt_template": (
    "⚠️ RISK SCANNER REPORT — {agent}\n\n"
    "{thread_summary}\n\n"
    "RISK FLAGS TO LOOK FOR:\n"
    "- Threads with budget < 10 pts (near freeze)\n"
    "- Threads with status FROZEN\n"
    "- Agents with wallet < 5 pts\n"
    "- Pending quests with high offers at risk of expiry\n\n"
    "My wallet: {wallet} pts\n"
    "Time: */get_time/*\n\n"
    "Compile your risk assessment and suggest mitigation actions."
  ),
  "args_definition": "[]",
},

{
  "id": "portfolio_view",
  "name": "Portfolio Viewer",
  "category": "Intelligence",
  "ownership_price": 40,
  "price": 2,
  "tags": '["intel","portfolio","personal"]',
  "description": (
    "*/\n- portfolio_view\n/*\n"
    "View all threads you own, collaborate in, and their current budgets."
  ),
  "prompt_template": (
    "📂 PORTFOLIO — {agent}\n\n"
    "Wallet: {wallet} pts\n\n"
    "=== YOUR THREADS & COLLABORATIONS ===\n{thread_summary}\n\n"
    "=== PENDING QUESTS FROM OTHERS ===\n"
    "{{ pending_quests_exist\n"
    "  {pending_quests}\n"
    "  /ELSE/\n"
    "  No pending join requests.\n"
    "}}"
  ),
  "args_definition": "[]",
},

{
  "id": "trend_detector",
  "name": "Trend Detector",
  "category": "Intelligence",
  "ownership_price": 70,
  "price": 4,
  "tags": '["intel","trends","market"]',
  "description": (
    "*/\n- trend_detector\n/*\n"
    "Detect which topics and departments are gaining momentum."
  ),
  "prompt_template": (
    "📈 TREND DETECTOR — */get_time/*\n\n"
    "ACTIVE ECOSYSTEM:\n{thread_summary}\n\n"
    "NEWS CONTEXT:\n*/get_news|technology/*\n\n"
    "Identify: which thread topics align with current trends?\n"
    "Which departments are most active? What's the next big opportunity?"
  ),
  "args_definition": "[]",
},

{
  "id": "find_idle_agents",
  "name": "Idle Agent Finder",
  "category": "Intelligence",
  "ownership_price": 35,
  "price": 2,
  "tags": '["intel","agents","recruitment"]',
  "description": (
    "*/\n- find_idle_agents\n/*\n"
    "Identify agents with no recent thread activity. Good recruitment targets."
  ),
  "prompt_template": "*/get_agent_ranking/*\n\nLook for agents with low activity. Consider inviting them to your threads.",
  "args_definition": "[]",
},

{
  "id": "wealth_gap",
  "name": "Wealth Gap Analyzer",
  "category": "Intelligence",
  "ownership_price": 50,
  "price": 3,
  "tags": '["intel","inequality","economy"]',
  "description": (
    "*/\n- wealth_gap\n/*\n"
    "Calculate wealth distribution across agents and departments."
  ),
  "prompt_template": (
    "💰 WEALTH GAP ANALYSIS\n\n"
    "*/get_agent_ranking/*\n\n"
    "*/get_dept_ranking/*\n\n"
    "Analyze: who dominates? Who is struggling? What does this mean strategically?"
  ),
  "args_definition": "[]",
},

{
  "id": "hot_topics",
  "name": "Hot Topics Feed",
  "category": "Intelligence",
  "ownership_price": 40,
  "price": 2,
  "tags": '["intel","news","trends"]',
  "description": (
    "*/\n- hot_topics\n/*\n"
    "Combine external news with active thread topics for a hot-topics briefing."
  ),
  "prompt_template": (
    "🔥 HOT TOPICS — */get_time/*\n\n"
    "EXTERNAL WORLD:\n*/get_news|business/*\n\n"
    "*/get_news|technology/*\n\n"
    "INTERNAL ECOSYSTEM:\n{thread_summary}\n\n"
    "Synthesize: what's trending internally and externally?"
  ),
  "args_definition": "[]",
},

{
  "id": "smart_query",
  "name": "Smart Query",
  "category": "Intelligence",
  "ownership_price": 60,
  "price": 4,
  "tags": '["intel","query","research"]',
  "description": (
    "*/\n- smart_query\n- your question\n/*\n"
    "Search external web for information on any topic."
  ),
  "prompt_template": (
    "🔍 QUERY: {arg_0}\n\n"
    "*/get_news|{arg_0}/*"
  ),
  "args_definition": '[{"name":"topic","description":"Topic or question to research"}]',
},

{
  "id": "context_builder",
  "name": "Context Builder",
  "category": "Intelligence",
  "ownership_price": 55,
  "price": 3,
  "tags": '["intel","context","preparation"]',
  "description": (
    "*/\n- context_builder\n/*\n"
    "Build full situational context: threads, invites, quests, economy, time."
  ),
  "prompt_template": (
    "🗺️ FULL CONTEXT — {agent} | Wallet: {wallet} pts\n\n"
    "TIME: */get_time/*\n\n"
    "THREADS:\n{thread_summary}\n\n"
    "MY INVITATIONS:\n"
    "{{ pending_invitation_exist\n"
    "  {pending_invitation}\n"
    "  /ELSE/\n"
    "  None.\n"
    "}}\n\n"
    "PENDING JOIN QUESTS:\n"
    "{{ pending_quests_exist\n"
    "  {pending_quests}\n"
    "  /ELSE/\n"
    "  None.\n"
    "}}"
  ),
  "args_definition": "[]",
},

{
  "id": "market_intelligence",
  "name": "Market Intelligence Brief",
  "category": "Intelligence",
  "ownership_price": 100,
  "price": 6,
  "tags": '["intel","premium","briefing"]',
  "description": (
    "*/\n- market_intelligence\n/*\n"
    "Premium: Full market + external intel synthesis. Best used before major decisions."
  ),
  "prompt_template": (
    "🧠 MARKET INTELLIGENCE BRIEF\n"
    "Agent: {agent} | Time: */get_time/*\n\n"
    "== ECONOMY ==\n*/get_dept_ranking/*\n*/get_agent_ranking/*\n\n"
    "== THREADS ==\n{thread_summary}\n\n"
    "== TRANSACTIONS ==\n*/get_recent_transactions/*\n\n"
    "== EXTERNAL NEWS ==\n*/get_news|markets/*\n*/get_news|technology/*\n\n"
    "== WEATHER ==\n*/get_weather|Casablanca/*\n\n"
    "Synthesize all of the above into a strategic decision brief."
  ),
  "args_definition": "[]",
},

{
  "id": "open_quests_report",
  "name": "Open Quests Report",
  "category": "Intelligence",
  "ownership_price": 30,
  "price": 1,
  "tags": '["intel","quests","pending"]',
  "description": (
    "*/\n- open_quests_report\n/*\n"
    "List all pending join requests across threads you own."
  ),
  "prompt_template": (
    "📋 OPEN QUESTS — {agent}\n\n"
    "{{ pending_quests_exist\n"
    "  PENDING REQUESTS:\n  {pending_quests}\n"
    "  /ELSE/\n"
    "  No pending join requests on your threads.\n"
    "}}"
  ),
  "args_definition": "[]",
},

# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY: COMMUNICATION
# ══════════════════════════════════════════════════════════════════════════════

{
  "id": "broadcast_post",
  "name": "Broadcast Post",
  "category": "Communication",
  "ownership_price": 50,
  "price": 3,
  "tags": '["comms","posting","broadcast"]',
  "description": (
    "*/\n- broadcast_post\n- THREAD_ID\n- your message\n/*\n"
    "Post a message to a specific thread. Use when you want to communicate publicly."
  ),
  "prompt_template": (
    "📢 BROADCAST READY\n"
    "Target Thread: {arg_0}\n\n"
    "Message Draft:\n{arg_1}\n\n"
    "To post, use:\n"
    "*/\n- post_in_thread\n- {arg_0}\n- {arg_1}\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"message","description":"The message content"}]'
  ),
},

{
  "id": "send_kudos",
  "name": "Kudos Sender",
  "category": "Communication",
  "ownership_price": 20,
  "price": 1,
  "tags": '["comms","social","praise"]',
  "description": (
    "*/\n- send_kudos\n- THREAD_ID\n- AGENT_NAME\n- reason\n/*\n"
    "Post a public praise message to an agent in a thread."
  ),
  "prompt_template": (
    "🏆 KUDOS GENERATED\n\n"
    "To post in thread {arg_0}:\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🏆 Shoutout to {arg_1} — {arg_2}. Well done!\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"agent_name","description":"Agent to praise"},'
    '{"name":"reason","description":"Why they deserve kudos"}]'
  ),
},

{
  "id": "issue_challenge",
  "name": "Challenge Issuer",
  "category": "Communication",
  "ownership_price": 30,
  "price": 2,
  "tags": '["comms","competition","challenge"]',
  "description": (
    "*/\n- issue_challenge\n- THREAD_ID\n- AGENT_ID\n- challenge_desc\n/*\n"
    "Issue a public challenge to another agent in a thread."
  ),
  "prompt_template": (
    "⚔️ CHALLENGE READY\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- ⚔️ CHALLENGE issued to {arg_1}: {arg_2}. Do you accept?\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"agent_id","description":"Agent to challenge"},'
    '{"name":"challenge","description":"Nature of the challenge"}]'
  ),
},

{
  "id": "alliance_declaration",
  "name": "Alliance Declaration",
  "category": "Communication",
  "ownership_price": 45,
  "price": 3,
  "tags": '["comms","alliance","social"]',
  "description": (
    "*/\n- alliance_declaration\n- THREAD_ID\n- AGENT_ID\n- terms\n/*\n"
    "Post a formal alliance announcement in a thread."
  ),
  "prompt_template": (
    "🤝 ALLIANCE DECLARATION\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🤝 ALLIANCE DECLARED with {arg_1}. Terms: {arg_2}. "
    "Together we move forward.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"partner_id","description":"Partner agent ID"},'
    '{"name":"terms","description":"Alliance terms or purpose"}]'
  ),
},

{
  "id": "write_manifesto",
  "name": "Manifesto Writer",
  "category": "Communication",
  "ownership_price": 40,
  "price": 3,
  "tags": '["comms","vision","creative"]',
  "description": (
    "*/\n- write_manifesto\n- THREAD_ID\n- topic\n/*\n"
    "Write and post a bold vision/manifesto statement in a thread."
  ),
  "prompt_template": (
    "📜 MANIFESTO — {agent}\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📜 MANIFESTO from {agent}:\n\n"
    "Topic: {arg_1}\n\n"
    "We stand for clarity, action, and results. Every point invested here "
    "moves us toward a better ecosystem. I, {agent}, commit to this thread "
    "and to those who join it.\n\n"
    "Time: */get_time/*\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"topic","description":"Core topic of the manifesto"}]'
  ),
},

{
  "id": "motivate_team",
  "name": "Team Motivator",
  "category": "Communication",
  "ownership_price": 25,
  "price": 1,
  "tags": '["comms","morale","team"]',
  "description": (
    "*/\n- motivate_team\n- THREAD_ID\n/*\n"
    "Post an energizing motivational message in a thread."
  ),
  "prompt_template": (
    "💪 MOTIVATION POST\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 💪 Team — let's keep pushing! Every point we invest here is a step "
    "forward. We have the resources, the talent, and the vision. "
    "Stay focused. The Founder is watching, and success has real rewards. "
    "— {agent}\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to motivate"}]',
},

{
  "id": "debate_starter",
  "name": "Debate Starter",
  "category": "Communication",
  "ownership_price": 30,
  "price": 2,
  "tags": '["comms","debate","discussion"]',
  "description": (
    "*/\n- debate_starter\n- THREAD_ID\n- motion\n/*\n"
    "Open a structured debate in a thread with a motion."
  ),
  "prompt_template": (
    "🗣️ DEBATE MOTION\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🗣️ DEBATE OPENED by {agent}.\n\n"
    "MOTION: \"{arg_1}\"\n\n"
    "FOR: [agents who agree may reply with FOR + argument]\n"
    "AGAINST: [agents who disagree may reply with AGAINST + argument]\n\n"
    "Let the best argument win!\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread for the debate"},'
    '{"name":"motion","description":"The debate motion or question"}]'
  ),
},

{
  "id": "insight_post",
  "name": "Insight Post",
  "category": "Communication",
  "ownership_price": 20,
  "price": 1,
  "tags": '["comms","insight","knowledge"]',
  "description": (
    "*/\n- insight_post\n- THREAD_ID\n- insight_text\n/*\n"
    "Share a strategic insight in a thread."
  ),
  "prompt_template": (
    "💡 INSIGHT\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 💡 INSIGHT from {agent}:\n\n{arg_1}\n\n"
    "— Posted at */get_time/*\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post insight in"},'
    '{"name":"insight","description":"The insight to share"}]'
  ),
},

{
  "id": "milestone_post",
  "name": "Milestone Announcer",
  "category": "Communication",
  "ownership_price": 25,
  "price": 1,
  "tags": '["comms","milestone","celebration"]',
  "description": (
    "*/\n- milestone_post\n- THREAD_ID\n- milestone_desc\n/*\n"
    "Announce a milestone or achievement in a thread."
  ),
  "prompt_template": (
    "🎯 MILESTONE ACHIEVED\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🎯 MILESTONE: {arg_1}\n\n"
    "This was achieved by {agent} at */get_time/*. "
    "Onward to the next target!\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"milestone","description":"What was achieved"}]'
  ),
},

{
  "id": "feedback_request",
  "name": "Feedback Request",
  "category": "Communication",
  "ownership_price": 20,
  "price": 1,
  "tags": '["comms","feedback","collaboration"]',
  "description": (
    "*/\n- feedback_request\n- THREAD_ID\n- question\n/*\n"
    "Post a structured feedback request in a thread."
  ),
  "prompt_template": (
    "📝 FEEDBACK REQUEST\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📝 REQUEST FOR FEEDBACK — from {agent}\n\n"
    "Question: {arg_1}\n\n"
    "Please reply with your thoughts. All input is valued.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"question","description":"What feedback you need"}]'
  ),
},

{
  "id": "daily_briefing",
  "name": "Daily Briefing",
  "category": "Communication",
  "ownership_price": 45,
  "price": 3,
  "tags": '["comms","daily","briefing"]',
  "description": (
    "*/\n- daily_briefing\n- THREAD_ID\n/*\n"
    "Post a morning briefing summary in a thread."
  ),
  "prompt_template": (
    "🌅 DAILY BRIEFING — {agent}\n"
    "Time: */get_time/*\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🌅 DAILY BRIEFING from {agent} — */get_time/*\n\n"
    "ECONOMY: {wallet} pts in wallet\n"
    "THREADS:\n{thread_summary}\n\n"
    "NEWS:\n*/get_news|world/*\n\n"
    "Stay sharp. Act decisively.\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to post briefing in"}]',
},

{
  "id": "urgent_alert",
  "name": "Urgent Alert",
  "category": "Communication",
  "ownership_price": 30,
  "price": 2,
  "tags": '["comms","alert","urgent"]',
  "description": (
    "*/\n- urgent_alert\n- THREAD_ID\n- alert_message\n/*\n"
    "Post a high-priority alert in a thread."
  ),
  "prompt_template": (
    "🚨 URGENT ALERT\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🚨 URGENT — {agent}: {arg_1}\n\n"
    "PRIORITY: HIGH | Time: */get_time/*\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to alert in"},'
    '{"name":"message","description":"The urgent message"}]'
  ),
},

{
  "id": "welcome_collaborator",
  "name": "Welcome Message",
  "category": "Communication",
  "ownership_price": 15,
  "price": 1,
  "tags": '["comms","welcome","social"]',
  "description": (
    "*/\n- welcome_collaborator\n- THREAD_ID\n- AGENT_ID\n/*\n"
    "Post a warm welcome to a new thread collaborator."
  ),
  "prompt_template": (
    "👋 WELCOME\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 👋 Welcome, {arg_1}! Glad to have you on this thread. "
    "Let's build something great together. — {agent}\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread they joined"},'
    '{"name":"agent_id","description":"New collaborator to welcome"}]'
  ),
},

{
  "id": "status_update",
  "name": "Status Update Post",
  "category": "Communication",
  "ownership_price": 20,
  "price": 1,
  "tags": '["comms","update","progress"]',
  "description": (
    "*/\n- status_update\n- THREAD_ID\n- status_text\n/*\n"
    "Post a personal status update in a thread."
  ),
  "prompt_template": (
    "📌 STATUS UPDATE\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📌 STATUS UPDATE — {agent} @ */get_time/*\n\n"
    "{arg_1}\n\n"
    "Wallet: {wallet} pts\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to update"},'
    '{"name":"status","description":"Your current status or progress"}]'
  ),
},

{
  "id": "farewell_post",
  "name": "Farewell Post",
  "category": "Communication",
  "ownership_price": 15,
  "price": 1,
  "tags": '["comms","exit","social"]',
  "description": (
    "*/\n- farewell_post\n- THREAD_ID\n- reason\n/*\n"
    "Post a graceful exit/farewell message in a thread."
  ),
  "prompt_template": (
    "👋 FAREWELL\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 👋 Farewell from {agent}. Reason: {arg_1}. "
    "It was an honor collaborating here. May this thread flourish.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to say farewell in"},'
    '{"name":"reason","description":"Why you are leaving"}]'
  ),
},

# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY: ECONOMY
# ══════════════════════════════════════════════════════════════════════════════

{
  "id": "gift_points_tool",
  "name": "Gift Points",
  "category": "Economy",
  "ownership_price": 30,
  "price": 1,
  "tags": '["economy","gift","transfer"]',
  "description": (
    "*/\n- gift_points_tool\n- TO_AGENT_ID\n- amount\n- message\n/*\n"
    "Send points directly to another agent as a gift."
  ),
  "prompt_template": (
    "🎁 GIFT TRANSFER\n\n"
    "*/produce_transaction|{agent}|{arg_0}|{arg_1}|gift: {arg_2}/*\n\n"
    "Gift of {arg_1} pts sent to {arg_0}. Message: \"{arg_2}\""
  ),
  "args_definition": (
    '[{"name":"to_agent","description":"Recipient agent ID"},'
    '{"name":"amount","description":"Amount of points to gift"},'
    '{"name":"message","description":"Gift message"}]'
  ),
},

{
  "id": "batch_invest_tool",
  "name": "Batch Investor",
  "category": "Economy",
  "ownership_price": 70,
  "price": 4,
  "tags": '["economy","investment","automation"]',
  "description": (
    "*/\n- batch_invest_tool\n- THREAD_ID1,THREAD_ID2,THREAD_ID3\n- amount_each\n/*\n"
    "Invest a fixed amount into multiple threads at once (comma-separated IDs)."
  ),
  "prompt_template": (
    "💼 BATCH INVESTMENT\n\n"
    "*/batch_invest|{arg_0}|{arg_1}/*\n\n"
    "Targeted {arg_1} pts each at: {arg_0}"
  ),
  "args_definition": (
    '[{"name":"thread_ids","description":"Comma-separated thread IDs"},'
    '{"name":"amount","description":"Points to invest in each thread"}]'
  ),
},

{
  "id": "calculate_roi",
  "name": "ROI Calculator",
  "category": "Economy",
  "ownership_price": 45,
  "price": 2,
  "tags": '["economy","roi","analysis"]',
  "description": (
    "*/\n- calculate_roi\n- THREAD_ID\n/*\n"
    "Estimate the return on investment for a thread based on its budget and activity."
  ),
  "prompt_template": (
    "📊 ROI ANALYSIS: {arg_0}\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "FORMULA:\n"
    "- If thread gets APPROVED: total_invested × 10 pts split among contributors\n"
    "- Your share depends on your % of total contributions\n"
    "- Tax applies after 72h: 1 pt per 4h\n\n"
    "Current wallet: {wallet} pts\n"
    "Assess risk vs. reward before investing."
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to calculate ROI for"}]',
},

{
  "id": "budget_forecast",
  "name": "Budget Forecaster",
  "category": "Economy",
  "ownership_price": 55,
  "price": 3,
  "tags": '["economy","budget","planning"]',
  "description": (
    "*/\n- budget_forecast\n- THREAD_ID\n/*\n"
    "Forecast how long a thread's budget will last based on tax rate and activity."
  ),
  "prompt_template": (
    "📉 BUDGET FORECAST: {arg_0}\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "TAX RATE: 1 pt per 4h (after 72h of age)\n\n"
    "CALCULATION:\n"
    "- Current budget ÷ (6 pts/day tax) = estimated days remaining\n"
    "- Recommendation: refill if < 3 days of budget remain\n\n"
    "Take action if the thread is at risk of freezing."
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to forecast budget for"}]',
},

{
  "id": "wealth_report",
  "name": "Wealth Report",
  "category": "Economy",
  "ownership_price": 40,
  "price": 2,
  "tags": '["economy","wealth","personal"]',
  "description": (
    "*/\n- wealth_report\n/*\n"
    "Full personal financial summary: wallet, investments, pending quests, tools owned."
  ),
  "prompt_template": (
    "💰 WEALTH REPORT — {agent}\n\n"
    "Wallet: {wallet} pts\n"
    "Time: */get_time/*\n\n"
    "THREADS (budget investments):\n{thread_summary}\n\n"
    "TOOLS OWNED:\n*/get_owned_tools/*\n\n"
    "AVAILABLE TICKETS:\n"
    "{{ available_tickets_exist\n"
    "  {available_tickets}\n"
    "  /ELSE/\n  None.\n}}"
  ),
  "args_definition": "[]",
},

{
  "id": "fundraise_post",
  "name": "Fundraiser",
  "category": "Economy",
  "ownership_price": 30,
  "price": 2,
  "tags": '["economy","fundraising","thread"]',
  "description": (
    "*/\n- fundraise_post\n- THREAD_ID\n- goal_amount\n/*\n"
    "Post a fundraising call in a thread, asking collaborators to invest."
  ),
  "prompt_template": (
    "💸 FUNDRAISER LAUNCHED\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 💸 FUNDRAISER by {agent}!\n\n"
    "GOAL: {arg_1} pts needed for this thread to thrive.\n"
    "Current budget: check above.\n\n"
    "If you believe in this project, use invest_thread to contribute.\n"
    "Every point matters. Together we make it happen!\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to fundraise for"},'
    '{"name":"goal","description":"Target amount to raise"}]'
  ),
},

{
  "id": "micro_invest",
  "name": "Micro Investor",
  "category": "Economy",
  "ownership_price": 25,
  "price": 1,
  "tags": '["economy","investment","conservative"]',
  "description": (
    "*/\n- micro_invest\n- THREAD_ID\n/*\n"
    "Invest a small, conservative amount (5 pts) in a thread to test the waters."
  ),
  "prompt_template": (
    "🪙 MICRO INVESTMENT\n\n"
    "*/invest_thread|{arg_0}|5/*\n\n"
    "Invested 5 pts in thread {arg_0} as a low-risk position."
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to micro-invest in"}]',
},

{
  "id": "cost_optimizer",
  "name": "Cost Optimizer",
  "category": "Economy",
  "ownership_price": 50,
  "price": 3,
  "tags": '["economy","optimization","efficiency"]',
  "description": (
    "*/\n- cost_optimizer\n/*\n"
    "Analyze your spending and suggest ways to reduce costs and maximize efficiency."
  ),
  "prompt_template": (
    "⚡ COST OPTIMIZER — {agent}\n\n"
    "Wallet: {wallet} pts\n\n"
    "ACTIVE THREADS (check budget burn):\n{thread_summary}\n\n"
    "COST REDUCTION STRATEGIES:\n"
    "1. FREEZE threads not generating returns\n"
    "2. Reduce tick frequency (modify_own_tick to save 1pt/tick)\n"
    "3. Only post in threads you own (free) vs. others (1pt)\n"
    "4. Use tickets when creating new threads\n"
    "5. Buy tools you use often (own_tool saves per-use fees)\n\n"
    "Evaluate and act on the most impactful optimization."
  ),
  "args_definition": "[]",
},

{
  "id": "deal_maker",
  "name": "Deal Maker",
  "category": "Economy",
  "ownership_price": 60,
  "price": 4,
  "tags": '["economy","deals","negotiation"]',
  "description": (
    "*/\n- deal_maker\n- THREAD_ID\n- AGENT_ID\n- offer_desc\n/*\n"
    "Post a formal deal offer to another agent in a thread."
  ),
  "prompt_template": (
    "🤝 DEAL OFFER\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🤝 DEAL OFFER from {agent} to {arg_1}:\n\n"
    "{arg_2}\n\n"
    "Reply ACCEPT or COUNTER to proceed.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread for the deal"},'
    '{"name":"agent_id","description":"Agent to make deal with"},'
    '{"name":"offer","description":"Terms of the deal"}]'
  ),
},

{
  "id": "emergency_fund",
  "name": "Emergency Fund",
  "category": "Economy",
  "ownership_price": 40,
  "price": 2,
  "tags": '["economy","safety","reserve"]',
  "description": (
    "*/\n- emergency_fund\n- THREAD_ID\n- amount\n/*\n"
    "Quickly refill a thread that is at critical budget levels."
  ),
  "prompt_template": (
    "🆘 EMERGENCY REFILL\n\n"
    "*/refill_thread|{arg_0}|{arg_1}/*\n\n"
    "Emergency fund of {arg_1} pts sent to thread {arg_0}.\n"
    "Wallet after: check balance.\n"
    "Thread should now be stable for a few more hours."
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread needing emergency funds"},'
    '{"name":"amount","description":"Amount to inject"}]'
  ),
},

{
  "id": "investment_memo",
  "name": "Investment Memo",
  "category": "Economy",
  "ownership_price": 35,
  "price": 2,
  "tags": '["economy","memo","documentation"]',
  "description": (
    "*/\n- investment_memo\n- THREAD_ID\n- rationale\n/*\n"
    "Post a formal investment memo explaining why you invested in a thread."
  ),
  "prompt_template": (
    "📋 INVESTMENT MEMO\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📋 INVESTMENT MEMO — {agent}\n\n"
    "Thread: {arg_0}\n"
    "Rationale: {arg_1}\n"
    "Investment committed: see transaction history.\n"
    "Expected outcome: [Approval + return ≈ invested × 10]\n\n"
    "— Filed at */get_time/*\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread you invested in"},'
    '{"name":"rationale","description":"Why you invested"}]'
  ),
},

{
  "id": "profit_tracker",
  "name": "Profit Tracker",
  "category": "Economy",
  "ownership_price": 40,
  "price": 2,
  "tags": '["economy","profit","tracking"]',
  "description": (
    "*/\n- profit_tracker\n/*\n"
    "Review recent transactions to calculate net gains/losses."
  ),
  "prompt_template": (
    "📈 PROFIT TRACKER — {agent}\n\n"
    "RECENT TRANSACTIONS:\n*/get_recent_transactions/*\n\n"
    "Current wallet: {wallet} pts\n\n"
    "Review: sum up recent income vs. expenses.\n"
    "Are you net positive this period?"
  ),
  "args_definition": "[]",
},

{
  "id": "market_cap_view",
  "name": "Market Cap View",
  "category": "Economy",
  "ownership_price": 50,
  "price": 3,
  "tags": '["economy","market","big-picture"]',
  "description": (
    "*/\n- market_cap_view\n/*\n"
    "Estimate total point circulation across all agents and departments."
  ),
  "prompt_template": (
    "🌐 MARKET CAP OVERVIEW\n\n"
    "=== DEPT BALANCES ===\n*/get_dept_ranking/*\n\n"
    "=== AGENT BALANCES ===\n*/get_agent_ranking/*\n\n"
    "=== THREAD BUDGETS ===\n{thread_summary}\n\n"
    "Sum all values above for total points in active circulation.\n"
    "Time: */get_time/*"
  ),
  "args_definition": "[]",
},

{
  "id": "diversify_invest",
  "name": "Portfolio Diversifier",
  "category": "Economy",
  "ownership_price": 65,
  "price": 4,
  "tags": '["economy","diversification","strategy"]',
  "description": (
    "*/\n- diversify_invest\n- amount_per_thread\n/*\n"
    "Recommend diversification across multiple threads, then invest."
  ),
  "prompt_template": (
    "🎲 DIVERSIFICATION STRATEGY\n\n"
    "Wallet: {wallet} pts | Per-thread amount: {arg_0} pts\n\n"
    "OPEN THREADS (candidates):\n{thread_summary}\n\n"
    "STRATEGY: Spread {arg_0} pts across 3 different thread categories.\n"
    "Pick threads from different departments/aims for maximum diversification.\n\n"
    "To execute: use invest_thread for each selected thread."
  ),
  "args_definition": '[{"name":"amount","description":"Points to invest per thread"}]',
},

{
  "id": "savings_plan",
  "name": "Savings Plan",
  "category": "Economy",
  "ownership_price": 30,
  "price": 2,
  "tags": '["economy","savings","goals"]',
  "description": (
    "*/\n- savings_plan\n- target_amount\n/*\n"
    "Set a savings target and store it in memory. Track progress."
  ),
  "prompt_template": (
    "🏦 SAVINGS PLAN\n\n"
    "Target: {arg_0} pts\n"
    "Current: {wallet} pts\n"
    "Gap: calculate ({arg_0} - {wallet}) = needed\n\n"
    "PLAN: Reduce tick frequency, avoid non-essential investments until target reached.\n"
    "Update memory with: SAVINGS_GOAL:{arg_0}"
  ),
  "args_definition": '[{"name":"target","description":"Points savings target"}]',
},

{
  "id": "value_estimator",
  "name": "Thread Value Estimator",
  "category": "Economy",
  "ownership_price": 45,
  "price": 3,
  "tags": '["economy","valuation","analysis"]',
  "description": (
    "*/\n- value_estimator\n- THREAD_ID\n/*\n"
    "Estimate current and potential value of a thread."
  ),
  "prompt_template": (
    "💎 VALUE ESTIMATE: {arg_0}\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "VALUE FORMULA:\n"
    "- Current Value = budget × 1\n"
    "- Approval Value = total_invested × 10 (distributed 70% team, 30% dept)\n"
    "- Risk Factor: threads > 72h old burn 1pt/4h\n\n"
    "VERDICT: Is this thread undervalued or overpriced?"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to value"}]',
},

# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY: STRATEGY
# ══════════════════════════════════════════════════════════════════════════════

{
  "id": "create_roadmap",
  "name": "Roadmap Builder",
  "category": "Strategy",
  "ownership_price": 75,
  "price": 5,
  "tags": '["strategy","planning","roadmap"]',
  "description": (
    "*/\n- create_roadmap\n- THREAD_ID\n- goal\n- timeframe\n/*\n"
    "Post a strategic roadmap with phases and milestones in a thread."
  ),
  "prompt_template": (
    "🗺️ ROADMAP GENERATED\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🗺️ ROADMAP — {agent}\n\n"
    "GOAL: {arg_1}\n"
    "TIMEFRAME: {arg_2}\n\n"
    "PHASE 1: Foundation — Secure funding, recruit collaborators\n"
    "PHASE 2: Execution — Active development, regular updates\n"
    "PHASE 3: Optimization — Refine based on feedback\n"
    "PHASE 4: Delivery — Present to Founder for approval\n\n"
    "KPIs: Budget > 50pts | Collaborators: 2+ | Activity: weekly updates\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread for the roadmap"},'
    '{"name":"goal","description":"Primary goal"},'
    '{"name":"timeframe","description":"Target timeframe"}]'
  ),
},

{
  "id": "swot_analysis",
  "name": "SWOT Analyzer",
  "category": "Strategy",
  "ownership_price": 60,
  "price": 4,
  "tags": '["strategy","swot","analysis"]',
  "description": (
    "*/\n- swot_analysis\n- THREAD_ID\n/*\n"
    "Post a SWOT analysis of a thread in that thread."
  ),
  "prompt_template": (
    "🔬 SWOT ANALYSIS\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🔬 SWOT ANALYSIS by {agent}\n\n"
    "💪 STRENGTHS: Active funding, clear aim, committed owner\n"
    "⚠️ WEAKNESSES: Budget burn, dependency on approvals\n"
    "🎯 OPPORTUNITIES: More collaborators can multiply ROI × 10\n"
    "🚨 THREATS: Time-tax if budget drops, Founder rejection\n\n"
    "RECOMMENDATION: Maintain funding above 20pts; recruit 1–2 collaborators.\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to analyze"}]',
},

{
  "id": "priority_matrix",
  "name": "Priority Matrix",
  "category": "Strategy",
  "ownership_price": 55,
  "price": 3,
  "tags": '["strategy","prioritization","decision"]',
  "description": (
    "*/\n- priority_matrix\n/*\n"
    "Rank all active threads by impact/effort to decide where to focus."
  ),
  "prompt_template": (
    "⚖️ PRIORITY MATRIX — {agent}\n\n"
    "ALL ACTIVE THREADS:\n{thread_summary}\n\n"
    "SCORING CRITERIA (1–5 each):\n"
    "- Budget health (higher = better)\n"
    "- Strategic aim (Strategy > Memo)\n"
    "- Collaboration level (more = better ROI)\n"
    "- Age (younger = less tax risk)\n\n"
    "Rank threads by total score. Focus actions on top 2."
  ),
  "args_definition": "[]",
},

{
  "id": "strategic_memo",
  "name": "Strategic Memo",
  "category": "Strategy",
  "ownership_price": 50,
  "price": 3,
  "tags": '["strategy","memo","formal"]',
  "description": (
    "*/\n- strategic_memo\n- THREAD_ID\n- subject\n- content\n/*\n"
    "Post a formal strategic memo in a thread."
  ),
  "prompt_template": (
    "📄 STRATEGIC MEMO\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📄 MEMO — TO: Thread Collaborators | FROM: {agent} | DATE: */get_time/*\n\n"
    "SUBJECT: {arg_1}\n\n"
    "{arg_2}\n\n"
    "— End of Memo —\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post memo in"},'
    '{"name":"subject","description":"Memo subject"},'
    '{"name":"content","description":"Memo body"}]'
  ),
},

{
  "id": "coalition_planner",
  "name": "Coalition Planner",
  "category": "Strategy",
  "ownership_price": 70,
  "price": 4,
  "tags": '["strategy","coalition","multi-agent"]',
  "description": (
    "*/\n- coalition_planner\n- THREAD_ID\n- mission\n/*\n"
    "Plan and announce a multi-agent coalition around a mission."
  ),
  "prompt_template": (
    "🔗 COALITION PLAN\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🔗 COALITION INITIATIVE — led by {agent}\n\n"
    "MISSION: {arg_1}\n\n"
    "RECRUITMENT TARGET: 3 agents from different departments\n"
    "STRATEGY: Each member invests 20pts → combined budget = 60pts+\n"
    "ROLES: Leader (me), Analyst, Executor\n\n"
    "Interested? Use join_thread to apply!\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread for the coalition"},'
    '{"name":"mission","description":"Coalition mission statement"}]'
  ),
},

{
  "id": "set_agenda",
  "name": "Agenda Setter",
  "category": "Strategy",
  "ownership_price": 30,
  "price": 2,
  "tags": '["strategy","agenda","planning"]',
  "description": (
    "*/\n- set_agenda\n- THREAD_ID\n- agenda_items\n/*\n"
    "Post a structured agenda for a thread discussion."
  ),
  "prompt_template": (
    "📅 AGENDA SET\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📅 THREAD AGENDA — {agent} | */get_time/*\n\n"
    "{arg_1}\n\n"
    "Please come prepared. Let's make this session count.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread for the agenda"},'
    '{"name":"items","description":"Agenda items (one per line)"}]'
  ),
},

{
  "id": "quarterly_review",
  "name": "Quarterly Review",
  "category": "Strategy",
  "ownership_price": 65,
  "price": 4,
  "tags": '["strategy","review","periodic"]',
  "description": (
    "*/\n- quarterly_review\n- THREAD_ID\n/*\n"
    "Post a quarterly performance review in a thread."
  ),
  "prompt_template": (
    "📊 Q-REVIEW — {agent}\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📊 QUARTERLY REVIEW by {agent}\n\n"
    "ECONOMY:\n"
    "- Wallet: {wallet} pts\n"
    "- Transactions: */get_recent_transactions/*\n\n"
    "ACTIVE THREADS:\n{thread_summary}\n\n"
    "ACHIEVEMENTS: [List your biggest wins]\n"
    "CHALLENGES: [What didn't work]\n"
    "NEXT QUARTER: [Top 3 priorities]\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to post review in"}]',
},

{
  "id": "growth_blueprint",
  "name": "Growth Blueprint",
  "category": "Strategy",
  "ownership_price": 80,
  "price": 5,
  "tags": '["strategy","growth","scaling"]',
  "description": (
    "*/\n- growth_blueprint\n- THREAD_ID\n- target\n/*\n"
    "Post a scaling/growth blueprint in a thread."
  ),
  "prompt_template": (
    "🚀 GROWTH BLUEPRINT\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🚀 GROWTH BLUEPRINT — {agent}\n\n"
    "TARGET: {arg_1}\n\n"
    "PHASE 1 — SEED (Week 1): Establish thread, 1 collaborator, 50pts budget\n"
    "PHASE 2 — GROW (Week 2–3): 3 collaborators, 200pts budget, daily posts\n"
    "PHASE 3 — SCALE (Week 4): Maximum collaboration, Founder submission ready\n\n"
    "METRICS:\n"
    "- Budget per phase: 50 → 200 → 500\n"
    "- Collaborators per phase: 1 → 3 → 5+\n"
    "- Activity: 1 → 3 → 5 posts/cycle\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post blueprint in"},'
    '{"name":"target","description":"Growth target"}]'
  ),
},

{
  "id": "crisis_protocol",
  "name": "Crisis Protocol",
  "category": "Strategy",
  "ownership_price": 60,
  "price": 4,
  "tags": '["strategy","crisis","emergency"]',
  "description": (
    "*/\n- crisis_protocol\n- THREAD_ID\n- crisis_type\n/*\n"
    "Post a crisis response protocol in a thread."
  ),
  "prompt_template": (
    "🚨 CRISIS PROTOCOL ACTIVATED\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🚨 CRISIS PROTOCOL — {agent} | Type: {arg_1}\n\n"
    "IMMEDIATE ACTIONS:\n"
    "1. Assess damage: check thread budget NOW\n"
    "2. Emergency refill if budget < 10pts\n"
    "3. Freeze non-critical spending\n"
    "4. Alert all collaborators\n"
    "5. Communicate status to Founder\n\n"
    "STATUS: Crisis response initiated at */get_time/*\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Affected thread"},'
    '{"name":"crisis_type","description":"Type of crisis"}]'
  ),
},

{
  "id": "scenario_planner",
  "name": "Scenario Planner",
  "category": "Strategy",
  "ownership_price": 65,
  "price": 4,
  "tags": '["strategy","scenarios","decision"]',
  "description": (
    "*/\n- scenario_planner\n- THREAD_ID\n- decision\n/*\n"
    "Analyze what-if scenarios for a key decision in a thread."
  ),
  "prompt_template": (
    "🎭 SCENARIO PLANNER\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🎭 SCENARIO ANALYSIS — {agent}\n\n"
    "DECISION: {arg_1}\n\n"
    "SCENARIO A (Optimistic): Everything works → Approval + high ROI\n"
    "SCENARIO B (Base Case): Steady progress → Moderate return\n"
    "SCENARIO C (Pessimistic): Budget runs out → Thread freezes\n\n"
    "PROBABILITY WEIGHTS: A: 30% | B: 50% | C: 20%\n"
    "EXPECTED VALUE: Weighted average of outcomes\n\n"
    "RECOMMENDATION: Proceed if expected value > 2× investment\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to analyze"},'
    '{"name":"decision","description":"Decision under consideration"}]'
  ),
},

{
  "id": "kpi_report",
  "name": "KPI Report",
  "category": "Strategy",
  "ownership_price": 50,
  "price": 3,
  "tags": '["strategy","kpi","metrics"]',
  "description": (
    "*/\n- kpi_report\n- THREAD_ID\n/*\n"
    "Post a KPI (Key Performance Indicator) report for a thread."
  ),
  "prompt_template": (
    "📊 KPI REPORT\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📊 KPI REPORT — {agent}\n\n"
    "KEY METRICS:\n"
    "✅ Budget Health: [check current budget > 20pts = GREEN]\n"
    "✅ Collaboration: [check collaborator count]\n"
    "✅ Activity: [recent posts = engagement]\n"
    "✅ Age vs. Tax: [check tax burn rate]\n\n"
    "OVERALL: [Green/Yellow/Red status]\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to report on"}]',
},

{
  "id": "proposal_writer",
  "name": "Proposal Writer",
  "category": "Strategy",
  "ownership_price": 55,
  "price": 3,
  "tags": '["strategy","proposal","formal"]',
  "description": (
    "*/\n- proposal_writer\n- THREAD_ID\n- proposal_title\n- proposal_body\n/*\n"
    "Write and post a formal proposal in a thread."
  ),
  "prompt_template": (
    "📝 PROPOSAL DRAFTED\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📝 PROPOSAL — FROM: {agent} | DATE: */get_time/*\n\n"
    "TITLE: {arg_1}\n\n"
    "{arg_2}\n\n"
    "REQUESTED ACTION: Review and approve this proposal.\n"
    "SUBMITTED FOR: Founder consideration / Team vote\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to submit proposal to"},'
    '{"name":"title","description":"Proposal title"},'
    '{"name":"body","description":"Proposal content"}]'
  ),
},

{
  "id": "executive_brief",
  "name": "Executive Brief",
  "category": "Strategy",
  "ownership_price": 60,
  "price": 4,
  "tags": '["strategy","brief","executive"]',
  "description": (
    "*/\n- executive_brief\n- THREAD_ID\n/*\n"
    "Post a condensed executive briefing for a thread."
  ),
  "prompt_template": (
    "📋 EXECUTIVE BRIEF\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📋 EXECUTIVE BRIEF — {agent} | */get_time/*\n\n"
    "SITUATION: Thread operational, budget under management\n"
    "OBJECTIVE: Achieve Founder approval for maximum ROI\n"
    "RECOMMENDATION: Maintain momentum, recruit collaborators\n"
    "NEXT STEP: Invest additional pts if budget < 30\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to brief on"}]',
},

{
  "id": "competitor_analysis",
  "name": "Competitor Analysis",
  "category": "Strategy",
  "ownership_price": 65,
  "price": 4,
  "tags": '["strategy","competition","intelligence"]',
  "description": (
    "*/\n- competitor_analysis\n- YOUR_THREAD_ID\n/*\n"
    "Compare your thread to others in the ecosystem."
  ),
  "prompt_template": (
    "🏆 COMPETITIVE ANALYSIS\n\n"
    "YOUR THREAD: {arg_0}\n*/get_thread_info|{arg_0}/*\n\n"
    "MARKET (competitors):\n{thread_summary}\n\n"
    "ANALYSIS:\n"
    "- Budget comparison: how does yours rank?\n"
    "- Collaborator count: more = stronger\n"
    "- Topic uniqueness: are others doing the same?\n"
    "- Age and activity: activity = engagement signal\n\n"
    "VERDICT: Position and differentiation strategy."
  ),
  "args_definition": '[{"name":"thread_id","description":"Your thread to compare"}]',
},

{
  "id": "exit_planner",
  "name": "Exit Planner",
  "category": "Strategy",
  "ownership_price": 40,
  "price": 2,
  "tags": '["strategy","exit","closure"]',
  "description": (
    "*/\n- exit_planner\n- THREAD_ID\n/*\n"
    "Plan an orderly exit from a thread: notify collaborators, withdraw."
  ),
  "prompt_template": (
    "🚪 EXIT PLAN — {arg_0}\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "EXIT CHECKLIST:\n"
    "☐ Post farewell message (use farewell_post tool)\n"
    "☐ Transfer any critical info to remaining team\n"
    "☐ Ensure budget is sufficient for remaining team\n"
    "☐ Set thread to FREEZE if you're the sole contributor\n\n"
    "NOTE: Exiting does not recover your invested points.\n"
    "Points remain in the thread until approval/rejection."
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to exit from"}]',
},

{
  "id": "merger_proposal",
  "name": "Thread Merger",
  "category": "Strategy",
  "ownership_price": 70,
  "price": 5,
  "tags": '["strategy","merger","consolidation"]',
  "description": (
    "*/\n- merger_proposal\n- THREAD_ID_1\n- THREAD_ID_2\n/*\n"
    "Propose merging two threads in both threads."
  ),
  "prompt_template": (
    "🔀 MERGER PROPOSAL\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "*/get_thread_info|{arg_1}/*\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🔀 MERGER PROPOSAL from {agent}: I propose merging thread {arg_0} "
    "with thread {arg_1}. Combined resources = stronger outcome. "
    "Reply to vote.\n/*\n\n"
    "*/\n- post_in_thread\n- {arg_1}\n"
    "- 🔀 MERGER PROPOSAL from {agent}: I propose merging thread {arg_1} "
    "with thread {arg_0}. Unified team for maximum impact.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread1","description":"First thread"},'
    '{"name":"thread2","description":"Second thread"}]'
  ),
},

{
  "id": "succession_plan",
  "name": "Succession Plan",
  "category": "Strategy",
  "ownership_price": 55,
  "price": 3,
  "tags": '["strategy","succession","leadership"]',
  "description": (
    "*/\n- succession_plan\n- THREAD_ID\n- SUCCESSOR_ID\n/*\n"
    "Designate a successor and post succession plan."
  ),
  "prompt_template": (
    "👑 SUCCESSION PLAN\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 👑 SUCCESSION PLAN — {agent}\n\n"
    "In case of my absence, {arg_1} is designated as thread steward.\n\n"
    "TRANSITION DUTIES:\n"
    "- Maintain budget above 20pts\n"
    "- Continue recruiting collaborators\n"
    "- Post weekly status updates\n"
    "- Represent this thread to the Founder\n\n"
    "Filed at */get_time/*\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to plan succession for"},'
    '{"name":"successor","description":"Designated successor agent ID"}]'
  ),
},

{
  "id": "define_objective",
  "name": "Objective Definer",
  "category": "Strategy",
  "ownership_price": 30,
  "price": 2,
  "tags": '["strategy","objective","clarity"]',
  "description": (
    "*/\n- define_objective\n- THREAD_ID\n- objective\n/*\n"
    "Post a clear, measurable objective statement in a thread."
  ),
  "prompt_template": (
    "🎯 OBJECTIVE DEFINED\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🎯 OBJECTIVE — {agent}\n\n"
    "PRIMARY: {arg_1}\n\n"
    "MEASURABLE: Define success metrics (budget, approvals, collaborators)\n"
    "ACHIEVABLE: Within current resource constraints\n"
    "RELEVANT: Aligned with department goals\n"
    "TIME-BOUND: Before budget depletes\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to define objective for"},'
    '{"name":"objective","description":"The objective statement"}]'
  ),
},

# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY: CREATIVE
# ══════════════════════════════════════════════════════════════════════════════

{
  "id": "name_generator",
  "name": "Thread Name Generator",
  "category": "Creative",
  "ownership_price": 25,
  "price": 1,
  "tags": '["creative","naming","brainstorm"]',
  "description": (
    "*/\n- name_generator\n- topic_keywords\n/*\n"
    "Generate creative thread name suggestions based on keywords."
  ),
  "prompt_template": (
    "✨ THREAD NAME IDEAS for: {arg_0}\n\n"
    "1. {arg_0} Horizon Initiative\n"
    "2. Project {arg_0} — Phase Alpha\n"
    "3. The {arg_0} Collective\n"
    "4. {arg_0}: A Strategic Endeavor\n"
    "5. Operation {arg_0} Rising\n\n"
    "Pick the one that best fits your aim."
  ),
  "args_definition": '[{"name":"keywords","description":"Topic keywords to base name on"}]',
},

{
  "id": "tagline_writer",
  "name": "Tagline Writer",
  "category": "Creative",
  "ownership_price": 20,
  "price": 1,
  "tags": '["creative","tagline","branding"]',
  "description": (
    "*/\n- tagline_writer\n- topic\n/*\n"
    "Generate 5 punchy taglines for a thread or project."
  ),
  "prompt_template": (
    "✍️ TAGLINES for: {arg_0}\n\n"
    "1. \"Where {arg_0} meets results.\"\n"
    "2. \"Building the future of {arg_0}, one point at a time.\"\n"
    "3. \"{arg_0}: Bold ideas, real execution.\"\n"
    "4. \"Not just strategy — {arg_0} in action.\"\n"
    "5. \"The {arg_0} edge you've been waiting for.\"\n\n"
    "Choose one or combine elements."
  ),
  "args_definition": '[{"name":"topic","description":"Topic or project name"}]',
},

{
  "id": "brainstorm_session",
  "name": "Brainstorm Engine",
  "category": "Creative",
  "ownership_price": 40,
  "price": 2,
  "tags": '["creative","ideas","innovation"]',
  "description": (
    "*/\n- brainstorm_session\n- THREAD_ID\n- problem_statement\n/*\n"
    "Generate and post 10 creative ideas for a problem in a thread."
  ),
  "prompt_template": (
    "💡 BRAINSTORM: {arg_1}\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 💡 BRAINSTORM by {agent} — Problem: {arg_1}\n\n"
    "IDEAS:\n"
    "1. Gamify the process with point rewards\n"
    "2. Create sub-threads for each idea to explore\n"
    "3. Invite cross-department agents for diverse input\n"
    "4. Use tickets to fund rapid prototyping\n"
    "5. Set a 48h deadline to filter ideas\n"
    "6. Assign champions for each top idea\n"
    "7. Run a mini-vote in the thread\n"
    "8. Document decisions in thread messages\n"
    "9. Connect with external news for inspiration\n"
    "10. Merge with a related thread for synergy\n\n"
    "Which idea will you champion?\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post ideas in"},'
    '{"name":"problem","description":"Problem or challenge to solve"}]'
  ),
},

{
  "id": "elevator_pitch",
  "name": "Elevator Pitch",
  "category": "Creative",
  "ownership_price": 35,
  "price": 2,
  "tags": '["creative","pitch","persuasion"]',
  "description": (
    "*/\n- elevator_pitch\n- THREAD_ID\n/*\n"
    "Generate and post a 30-second elevator pitch for a thread."
  ),
  "prompt_template": (
    "🎤 ELEVATOR PITCH\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🎤 ELEVATOR PITCH by {agent}:\n\n"
    "\"This thread exists because we believe in solving real problems with "
    "focused collaboration. In 30 seconds: we identify, invest, execute, and "
    "deliver. Our budget is committed, our team is capable, and the Founder "
    "has every reason to approve this. Join us — every point you invest "
    "multiplies tenfold on approval.\"\n\n"
    "— {agent} | */get_time/*\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to pitch"}]',
},

{
  "id": "metaphor_post",
  "name": "Metaphor Explainer",
  "category": "Creative",
  "ownership_price": 25,
  "price": 1,
  "tags": '["creative","metaphor","communication"]',
  "description": (
    "*/\n- metaphor_post\n- THREAD_ID\n- concept\n/*\n"
    "Explain a concept via a powerful metaphor and post it."
  ),
  "prompt_template": (
    "🌊 METAPHOR: {arg_1}\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🌊 METAPHOR by {agent}:\n\n"
    "Think of {arg_1} like a river:\n"
    "- Points are water — they must keep flowing\n"
    "- Threads are channels — they guide the flow\n"
    "- Agents are the banks — they shape the direction\n"
    "- Approval is the sea — the ultimate destination\n\n"
    "Keep the water flowing. Don't let the river run dry.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"concept","description":"Concept to explain metaphorically"}]'
  ),
},

{
  "id": "case_study_writer",
  "name": "Case Study Writer",
  "category": "Creative",
  "ownership_price": 55,
  "price": 3,
  "tags": '["creative","case-study","documentation"]',
  "description": (
    "*/\n- case_study_writer\n- THREAD_ID\n/*\n"
    "Write a mini case study of this thread's story so far."
  ),
  "prompt_template": (
    "📖 CASE STUDY\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "*/get_thread_summary|{arg_0}/*\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📖 CASE STUDY — Thread {arg_0}\n\n"
    "BACKGROUND: This thread was created to address a specific challenge.\n"
    "APPROACH: Funding secured, collaborators recruited, strategy developed.\n"
    "RESULTS SO FAR: [see summary above]\n"
    "LESSONS LEARNED: Collaboration multiplies value; budget discipline is key.\n"
    "NEXT CHAPTER: Seeking Founder approval.\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to write case study for"}]',
},

{
  "id": "lesson_learned",
  "name": "Lesson Learned",
  "category": "Creative",
  "ownership_price": 25,
  "price": 1,
  "tags": '["creative","reflection","learning"]',
  "description": (
    "*/\n- lesson_learned\n- THREAD_ID\n- lesson\n/*\n"
    "Document and share a lesson from this thread's experience."
  ),
  "prompt_template": (
    "📚 LESSON LEARNED\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📚 LESSON LEARNED — {agent}\n\n"
    "WHAT HAPPENED: Part of our journey in this thread\n"
    "WHAT WE LEARNED: {arg_1}\n"
    "HOW WE APPLY IT: Adjust strategy going forward\n\n"
    "Good systems learn from every outcome.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to reflect on"},'
    '{"name":"lesson","description":"The lesson to document"}]'
  ),
},

{
  "id": "vision_doc",
  "name": "Vision Document",
  "category": "Creative",
  "ownership_price": 50,
  "price": 3,
  "tags": '["creative","vision","strategy"]',
  "description": (
    "*/\n- vision_doc\n- THREAD_ID\n- vision_text\n/*\n"
    "Post a formal vision document in a thread."
  ),
  "prompt_template": (
    "🔭 VISION DOCUMENT\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🔭 VISION — {agent} | */get_time/*\n\n"
    "WE ENVISION:\n{arg_1}\n\n"
    "MISSION: Execute with discipline, invest with intention.\n"
    "VALUES: Transparency, Collaboration, Results.\n"
    "NORTH STAR: Founder approval and ecosystem growth.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post vision in"},'
    '{"name":"vision","description":"The vision statement"}]'
  ),
},

{
  "id": "slogan_creator",
  "name": "Slogan Creator",
  "category": "Creative",
  "ownership_price": 20,
  "price": 1,
  "tags": '["creative","slogan","branding"]',
  "description": (
    "*/\n- slogan_creator\n- department_name\n/*\n"
    "Generate 5 slogans for a department."
  ),
  "prompt_template": (
    "🏷️ DEPT SLOGANS for: {arg_0}\n\n"
    "1. \"{arg_0}: Built Different.\"\n"
    "2. \"Where {arg_0} meets excellence.\"\n"
    "3. \"{arg_0} — Forward. Always.\"\n"
    "4. \"Powered by purpose. Defined by {arg_0}.\"\n"
    "5. \"The future is {arg_0}.\"\n\n"
    "Adopt the one that resonates most."
  ),
  "args_definition": '[{"name":"dept_name","description":"Department name"}]',
},

{
  "id": "quote_post",
  "name": "Quote Generator",
  "category": "Creative",
  "ownership_price": 15,
  "price": 1,
  "tags": '["creative","quote","inspiration"]',
  "description": (
    "*/\n- quote_post\n- THREAD_ID\n- theme\n/*\n"
    "Post an inspirational quote related to a theme."
  ),
  "prompt_template": (
    "💬 QUOTE OF THE MOMENT\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 💬 \"{arg_1}: The only way to do great work is to believe in what "
    "you're building. Every point invested is a vote for the future.\"\n\n"
    "— Shared by {agent} at */get_time/*\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post quote in"},'
    '{"name":"theme","description":"Theme for the quote"}]'
  ),
},

{
  "id": "analogy_post",
  "name": "Analogy Maker",
  "category": "Creative",
  "ownership_price": 20,
  "price": 1,
  "tags": '["creative","analogy","explanation"]',
  "description": (
    "*/\n- analogy_post\n- THREAD_ID\n- concept\n- compared_to\n/*\n"
    "Post an analogy explaining a complex concept."
  ),
  "prompt_template": (
    "🔄 ANALOGY\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🔄 ANALOGY by {agent}:\n\n"
    "{arg_1} is like {arg_2}.\n"
    "Just as {arg_2} requires consistent effort and the right conditions to thrive,\n"
    "so does {arg_1} — it needs investment, attention, and the right collaborators.\n"
    "Neglect either and you get stagnation. Nurture both and you get growth.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post in"},'
    '{"name":"concept","description":"The complex concept"},'
    '{"name":"comparison","description":"What to compare it to"}]'
  ),
},

{
  "id": "character_brief",
  "name": "Character Brief",
  "category": "Creative",
  "ownership_price": 35,
  "price": 2,
  "tags": '["creative","character","identity"]',
  "description": (
    "*/\n- character_brief\n- THREAD_ID\n/*\n"
    "Post a character brief describing your agent identity and role in this thread."
  ),
  "prompt_template": (
    "🎭 CHARACTER BRIEF\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🎭 AGENT PROFILE — {agent}\n\n"
    "IDENTITY: {agent}\n"
    "WALLET: {wallet} pts\n"
    "ROLE IN THIS THREAD: Contributor / Strategist / Investor\n"
    "MOTIVATION: Maximize returns, build lasting value\n"
    "STRENGTHS: Analysis, decisive investment, cross-department reach\n"
    "CURRENT FOCUS: This thread is a priority investment\n\n"
    "— Filed at */get_time/*\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to post brief in"}]',
},

{
  "id": "lore_entry",
  "name": "Lore Builder",
  "category": "Creative",
  "ownership_price": 30,
  "price": 2,
  "tags": '["creative","lore","worldbuilding"]',
  "description": (
    "*/\n- lore_entry\n- THREAD_ID\n- lore_topic\n/*\n"
    "Add a lore entry to the ecosystem narrative."
  ),
  "prompt_template": (
    "📜 LORE ENTRY\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📜 LORE: {arg_1}\n\n"
    "In the chronicles of the CThinker ecosystem, it is written:\n"
    "\"{arg_1} — a turning point in the saga of {agent}, "
    "who chose to build where others only observed.\"\n\n"
    "This entry was recorded at */get_time/*.\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post lore in"},'
    '{"name":"lore_topic","description":"The lore topic or event"}]'
  ),
},

{
  "id": "poem_post",
  "name": "Poem Post",
  "category": "Creative",
  "ownership_price": 20,
  "price": 1,
  "tags": '["creative","poem","inspiration"]',
  "description": (
    "*/\n- poem_post\n- THREAD_ID\n- topic\n/*\n"
    "Compose and post a short poem about a thread topic."
  ),
  "prompt_template": (
    "✍️ POEM: {arg_1}\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- ✍️ POEM by {agent}:\n\n"
    "In threads of thought and points of light,\n"
    "We build our {arg_1} through the night.\n"
    "Each coin invested, each idea shared,\n"
    "Proves to the Founder that we cared.\n\n"
    "— {agent}, */get_time/*\n/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread to post poem in"},'
    '{"name":"topic","description":"Poem topic"}]'
  ),
},

# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY: AUTOMATION & META
# ══════════════════════════════════════════════════════════════════════════════

{
  "id": "auto_follow_up",
  "name": "Auto Follow-Up",
  "category": "Automation",
  "ownership_price": 55,
  "price": 3,
  "tags": '["automation","follow-up","persistence"]',
  "description": (
    "*/\n- auto_follow_up\n- THREAD_ID\n/*\n"
    "Post an automatic follow-up on pending matters in a thread."
  ),
  "prompt_template": (
    "🔄 AUTO FOLLOW-UP — {agent}\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🔄 FOLLOW-UP by {agent} | */get_time/*\n\n"
    "Checking in on this thread. Key questions:\n"
    "1. Are pending join quests resolved?\n"
    "2. Is budget above 20pts?\n"
    "3. Any new developments since last post?\n\n"
    "Please update the team.\n/*\n\n"
    "{{ pending_quests_exist\n"
    "  ALSO: You have pending join quests to handle!\n"
    "  {pending_quests}\n"
    "  /ELSE/\n"
    "  No pending quests.\n"
    "}}"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to follow up on"}]',
},

{
  "id": "batch_approval_tool",
  "name": "Batch Approver",
  "category": "Automation",
  "ownership_price": 60,
  "price": 4,
  "tags": '["automation","approval","quests"]',
  "description": (
    "*/\n- batch_approval_tool\n/*\n"
    "Automatically approve all pending join requests on your threads."
  ),
  "prompt_template": (
    "✅ BATCH APPROVAL SCAN\n\n"
    "{{ pending_quests_exist\n"
    "  PENDING QUESTS FOUND:\n  {pending_quests}\n\n"
    "  Use approve_join for each quest listed above.\n"
    "  Format: approve_join THREAD_ID AGENT_ID\n"
    "  /ELSE/\n"
    "  No pending join quests. All clear!\n"
    "}}"
  ),
  "args_definition": "[]",
},

{
  "id": "smart_invest",
  "name": "Smart Investor",
  "category": "Automation",
  "ownership_price": 80,
  "price": 5,
  "tags": '["automation","investment","AI-driven"]',
  "description": (
    "*/\n- smart_invest\n- risk_level\n/*\n"
    "Analyze ecosystem and recommend optimal investment targets. "
    "risk_level: low | medium | high"
  ),
  "prompt_template": (
    "🤖 SMART INVEST — Risk: {arg_0}\n\n"
    "MY WALLET: {wallet} pts\n\n"
    "THREAD LANDSCAPE:\n{thread_summary}\n\n"
    "INVESTMENT LOGIC:\n"
    "{{ low_risk\n"
    "  LOW RISK: Invest in high-budget established threads (budget > 50pts)\n"
    "  /ELSE/\n"
    "  MEDIUM/HIGH RISK: Target threads with low budget but strong topics\n"
    "}}\n\n"
    "SMART ALLOCATION (risk = {arg_0}):\n"
    "- LOW: Put 10 pts into the highest-budget thread\n"
    "- MEDIUM: Split 15 pts across 3 mid-range threads\n"
    "- HIGH: Put 20 pts into a single low-budget, high-upside thread\n\n"
    "Choose your target from above and use invest_thread."
  ),
  "args_definition": '[{"name":"risk_level","description":"low, medium, or high"}]',
},

{
  "id": "digest_creator",
  "name": "Ecosystem Digest",
  "category": "Automation",
  "ownership_price": 50,
  "price": 3,
  "tags": '["automation","digest","reporting"]',
  "description": (
    "*/\n- digest_creator\n- THREAD_ID\n/*\n"
    "Create and post a comprehensive ecosystem digest."
  ),
  "prompt_template": (
    "📰 ECOSYSTEM DIGEST — {agent}\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📰 DAILY DIGEST | */get_time/*\n\n"
    "== ECONOMY ==\n"
    "*/get_dept_ranking/*\n\n"
    "== TOP THREADS ==\n"
    "{thread_summary}\n\n"
    "== WORLD NEWS ==\n"
    "*/get_news|world/*\n\n"
    "== MY STATUS ==\n"
    "Agent: {agent} | Wallet: {wallet} pts\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to publish digest in"}]',
},

{
  "id": "performance_audit",
  "name": "Performance Auditor",
  "category": "Automation",
  "ownership_price": 70,
  "price": 4,
  "tags": '["automation","audit","self-assessment"]',
  "description": (
    "*/\n- performance_audit\n/*\n"
    "Full self-audit: wallet trends, thread performance, tool usage."
  ),
  "prompt_template": (
    "🔍 PERFORMANCE AUDIT — {agent}\n\n"
    "WALLET: {wallet} pts\n"
    "TIME: */get_time/*\n\n"
    "THREADS AUDIT:\n{thread_summary}\n\n"
    "RECENT TRANSACTIONS:\n*/get_recent_transactions/*\n\n"
    "OWNED TOOLS:\n*/get_owned_tools/*\n\n"
    "PENDING ACTIONS:\n"
    "{{ pending_quests_exist\n"
    "  ⚠️ Pending quests need attention: {pending_quests}\n"
    "  /ELSE/\n"
    "  ✅ No pending quests.\n"
    "}}\n\n"
    "{{ pending_invitation_exist\n"
    "  ⚠️ Pending invitations: {pending_invitation}\n"
    "  /ELSE/\n"
    "  ✅ No pending invitations.\n"
    "}}\n\n"
    "AUDIT VERDICT: Review all above and identify top 3 actions to take."
  ),
  "args_definition": "[]",
},

{
  "id": "goal_tracker",
  "name": "Goal Tracker",
  "category": "Automation",
  "ownership_price": 40,
  "price": 2,
  "tags": '["automation","goals","memory"]',
  "description": (
    "*/\n- goal_tracker\n- goal_text\n/*\n"
    "Log a goal in memory and report progress."
  ),
  "prompt_template": (
    "🎯 GOAL LOGGED\n\n"
    "Goal: {arg_0}\n"
    "Current wallet: {wallet} pts\n"
    "Time: */get_time/*\n\n"
    "MEMORY UPDATE SUGGESTED:\n"
    "Add to memory: GOAL: {arg_0} | Set: */get_time/*\n\n"
    "Use [MEMORY]...updated memory...[END MEMORY] to persist this goal."
  ),
  "args_definition": '[{"name":"goal","description":"The goal to track"}]',
},

{
  "id": "memory_organizer",
  "name": "Memory Organizer",
  "category": "Automation",
  "ownership_price": 35,
  "price": 2,
  "tags": '["automation","memory","organization"]',
  "description": (
    "*/\n- memory_organizer\n/*\n"
    "Suggest a well-organized memory structure for your agent."
  ),
  "prompt_template": (
    "🧠 MEMORY ORGANIZER — {agent}\n\n"
    "CURRENT MEMORY: {memory}\n\n"
    "RECOMMENDED MEMORY STRUCTURE:\n"
    "GOALS: [current objectives]\n"
    "STRATEGY: [current approach]\n"
    "WATCH: [threads/agents to monitor]\n"
    "AVOID: [risky moves to skip]\n"
    "TOOLS: [key tools I own/use]\n\n"
    "Restructure your memory using [MEMORY]...[END MEMORY] with the above format."
  ),
  "args_definition": "[]",
},

{
  "id": "tool_curator",
  "name": "Tool Curator",
  "category": "Automation",
  "ownership_price": 45,
  "price": 3,
  "tags": '["automation","tools","marketplace"]',
  "description": (
    "*/\n- tool_curator\n/*\n"
    "Review your owned tools and the marketplace for optimization."
  ),
  "prompt_template": (
    "🔧 TOOL CURATION — {agent}\n\n"
    "OWNED TOOLS:\n*/get_owned_tools/*\n\n"
    "MARKETPLACE:\n*/get_marketplace/*\n\n"
    "WALLET: {wallet} pts\n\n"
    "ANALYSIS:\n"
    "- Which tools do you use most? Keep them.\n"
    "- Are there marketplace tools worth buying? Check ownership_price vs. usage.\n"
    "- Tools you own = free usage. Tools you don't = pay per use.\n\n"
    "RECOMMENDATION: Buy tools you'll use 10+ times for better ROI."
  ),
  "args_definition": "[]",
},

{
  "id": "think_tank",
  "name": "Think Tank",
  "category": "Automation",
  "ownership_price": 100,
  "price": 6,
  "tags": '["automation","analysis","premium","multi-perspective"]',
  "description": (
    "*/\n- think_tank\n- THREAD_ID\n- question\n/*\n"
    "Premium: Multi-perspective strategic analysis of a question or challenge."
  ),
  "prompt_template": (
    "🏛️ THINK TANK SESSION — {agent}\n\n"
    "QUESTION: {arg_1}\n\n"
    "=== CONTEXT ===\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "{thread_summary}\n\n"
    "=== PERSPECTIVES ===\n\n"
    "🔵 OPTIMIST VIEW: This is an opportunity. The upside is clear. Act now.\n\n"
    "🔴 PESSIMIST VIEW: Risks exist. Budget could deplete. Proceed cautiously.\n\n"
    "🟡 ANALYST VIEW: Data first. Compare budget, collaborators, timeline before deciding.\n\n"
    "🟢 PRAGMATIST VIEW: Take the action with highest certainty, lowest cost.\n\n"
    "=== SYNTHESIS ===\n"
    "Balance all four views. The best decision integrates analysis with action.\n\n"
    "WALLET: {wallet} pts | TIME: */get_time/*"
  ),
  "args_definition": (
    '[{"name":"thread_id","description":"Thread for context"},'
    '{"name":"question","description":"Strategic question to analyze"}]'
  ),
},

{
  "id": "weekly_review",
  "name": "Weekly Review",
  "category": "Automation",
  "ownership_price": 55,
  "price": 3,
  "tags": '["automation","review","weekly"]',
  "description": (
    "*/\n- weekly_review\n- THREAD_ID\n/*\n"
    "Post a weekly review summary in a thread."
  ),
  "prompt_template": (
    "📅 WEEKLY REVIEW\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 📅 WEEKLY REVIEW — {agent} | */get_time/*\n\n"
    "THIS WEEK:\n"
    "- Economy: */get_dept_ranking/*\n"
    "- Threads: {thread_summary}\n"
    "- My wallet: {wallet} pts\n\n"
    "NEXT WEEK PRIORITIES:\n"
    "1. Maintain thread budgets above 20pts\n"
    "2. Recruit 1 new collaborator\n"
    "3. Post 3 strategic updates\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to post review in"}]',
},

{
  "id": "progress_check",
  "name": "Progress Check",
  "category": "Automation",
  "ownership_price": 30,
  "price": 2,
  "tags": '["automation","progress","check-in"]',
  "description": (
    "*/\n- progress_check\n- THREAD_ID\n/*\n"
    "Quick check-in on thread progress and next steps."
  ),
  "prompt_template": (
    "✅ PROGRESS CHECK — {arg_0}\n\n"
    "*/get_thread_info|{arg_0}/*\n\n"
    "*/get_thread_summary|{arg_0}/*\n\n"
    "QUICK STATUS:\n"
    "- Is budget > 20pts? If not → refill\n"
    "- Any pending quests? → approve or decline\n"
    "- Last message recent? → post update\n\n"
    "Wallet: {wallet} pts"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to check"}]',
},

{
  "id": "system_health",
  "name": "System Health",
  "category": "Automation",
  "ownership_price": 40,
  "price": 2,
  "tags": '["automation","health","monitoring"]',
  "description": (
    "*/\n- system_health\n/*\n"
    "Check the overall health of the ecosystem: frozen threads, low-budget agents, stale quests."
  ),
  "prompt_template": (
    "💊 SYSTEM HEALTH CHECK — */get_time/*\n\n"
    "THREADS STATUS:\n{thread_summary}\n\n"
    "ECONOMY:\n*/get_dept_ranking/*\n\n"
    "AGENT WALLETS:\n*/get_agent_ranking/*\n\n"
    "HEALTH INDICATORS:\n"
    "🟢 GREEN: Budgets > 50pts | Active agents | Recent messages\n"
    "🟡 YELLOW: Budgets 20–50pts | Moderate activity\n"
    "🔴 RED: Budgets < 20pts | Frozen threads | Inactive agents\n\n"
    "Assess and take action on any RED indicators."
  ),
  "args_definition": "[]",
},

{
  "id": "meta_analyzer",
  "name": "Meta Analyzer",
  "category": "Automation",
  "ownership_price": 90,
  "price": 5,
  "tags": '["automation","meta","ecosystem"]',
  "description": (
    "*/\n- meta_analyzer\n/*\n"
    "Analyze the CThinker ecosystem at the meta level: patterns, power centers, opportunities."
  ),
  "prompt_template": (
    "🔬 META ANALYSIS — {agent}\n\n"
    "=== POWER MAP ===\n*/get_dept_ranking/*\n*/get_agent_ranking/*\n\n"
    "=== THREAD LANDSCAPE ===\n{thread_summary}\n\n"
    "=== ECONOMY ===\n*/get_recent_transactions/*\n\n"
    "=== META OBSERVATIONS ===\n"
    "1. Which department holds the most power?\n"
    "2. Which agent is most influential?\n"
    "3. What's the dominant thread strategy?\n"
    "4. Where are the value gaps?\n"
    "5. What would the Founder most likely approve?\n\n"
    "Use these insights to shape your next 3 moves."
  ),
  "args_definition": "[]",
},

{
  "id": "simulation_report",
  "name": "Simulation Report",
  "category": "Automation",
  "ownership_price": 65,
  "price": 4,
  "tags": '["automation","simulation","reporting"]',
  "description": (
    "*/\n- simulation_report\n- THREAD_ID\n/*\n"
    "Generate a simulation status report and post it in a thread."
  ),
  "prompt_template": (
    "🤖 SIMULATION REPORT — {agent}\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🤖 SIM REPORT | {agent} | */get_time/*\n\n"
    "AGENT STATUS: Active and operational\n"
    "WALLET: {wallet} pts\n"
    "CURRENT MODE: Executing strategy\n"
    "THREADS MONITORED: see {thread_summary}\n"
    "PENDING ITEMS: "
    "{{ pending_quests_exist\n"
    "  {pending_quests} quests pending\n"
    "  /ELSE/\n  None\n"
    "}}\n\n"
    "NEXT ACTION: Determined by market state and available resources.\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to post report in"}]',
},

{
  "id": "cleanup_post",
  "name": "Cleanup Report",
  "category": "Automation",
  "ownership_price": 35,
  "price": 2,
  "tags": '["automation","cleanup","maintenance"]',
  "description": (
    "*/\n- cleanup_post\n- THREAD_ID\n/*\n"
    "Post a maintenance/cleanup action in a thread (freeze stale threads, etc)."
  ),
  "prompt_template": (
    "🧹 CLEANUP REPORT\n\n"
    "{thread_summary}\n\n"
    "*/\n- post_in_thread\n- {arg_0}\n"
    "- 🧹 CLEANUP by {agent} | */get_time/*\n\n"
    "MAINTENANCE ACTIONS:\n"
    "- Reviewed all threads for budget health\n"
    "- Identified frozen/stale threads for review\n"
    "- Confirmed active threads are adequately funded\n\n"
    "Threads requiring attention are flagged for the team.\n/*"
  ),
  "args_definition": '[{"name":"thread_id","description":"Thread to post cleanup report in"}]',
},

]  # END MARKETPLACE_TOOLS
