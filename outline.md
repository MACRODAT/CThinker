# Outline for Cthinker
Cthinker: a personal think tank system
Like a society, a group of agents working in many departments for the Founder.
The Founder: me.

# Architecture
- Front end: Vue/React
- Back end: Python
- Prefer components that plug in multiple places to save!
- LLM provide: ollama (local) with LLM default model (gemma4:e4b)
- Database: Use sqlite for all agents, threads...

# Views:
- Dashboard
- Agents
- Threads
- Departments
- Settings

# Organisation
- Five departments:
	- HF: Health and Wellness
	- ING: Engineering studies
	- STP: Strategic Planning
	- UIT: Useful Intelligence
	- FIN: Financing
- Each department may have many agents and one CEO.
- The CEO has GOD powers on his department. Why? The CEO is responsible for everything inside his department.

# Organisation
- Department
	-- name_id: "FIN|ING|STP|UIT|FIN"
	-- Ledger
		-- current points
		-- Log
			-- time
			-- who
			-- why
			-- how much
	-- ceo_name_id
	-- agents
		-- name_id
		-- join date
		-- junior agents
			--- name_id
			--- join date
				---- ... (hierarchy)
-- agent
	-- name_id (ex: John Smith)
	-- when born
	-- custom_model
	-- ticks
		-- current
		-- log
			-- when
			-- tick
	-- department_name_id (if any)
	-- log_actions
		-- when
		-- what
		-- points (if any)
	-- wallet
		-- current points
		-- log
			--- when
			--- what
	-- is_ceo
	-- own_threads_ids



# Communication

## FIRST: THREADS
- Departments may communicate via threads.
- Each Thread has:
	-- ID
	-- Owner department
	-- Owner agent
	-- Topic
	-- Aim (These will be detailed later)
		-- Strategy
		-- Memo
		-- Endeavor
	-- Status: OPEN | ACTIVE | FROZEN | REJECTED | APPROVED
	-- Investers
		-- when
		-- who
	-- Point wallet
		-- budget
		-- log
			-- when
			-- who
			-- how much
	-- Messages log
		-- when
		-- who
		-- what
		-- points
	- Thread Quests
		-- when
		-- who
		-- why
		-- amount invested
	- Invitations
		-- who
		-- why
		-- offer (points)

# Points
Points are the currency in CThinker. Aim is to produce efficiently by rewarding productive actions that benefit Founder and penalising bad ones.
- Every department is allowed daily 100 points.
- Each agent is allowed daily 10 points.

# What each agent can do
- Can modify / rewrite Custom mode prompt
- Each agent has four modes:
	-- Points Accounter (default)
	-- Creator
	-- Invester
	-- Custom
_ Agent will decide what to 
- Agent may preserve limited context (200 characters max) as memory for next tick
- START A THREAD (COST: 25 Points for Memo, 100 POINTS for Strategy, 100 POINTS for endeavor)
	-- OWNER AGENT HAS FREE CONTRIBUTIONS TO THAT THREAD INFINITELY
	-- HOWEVER, AFTER 72 HOURS FROM THREAD CREATION, EACH FOUR HOURS ARE TAXED 1 POINT FROM THREAD.
	-- IF NO POINTS REMAIN: THREAD IS FROZEN.
	-- OWNER HAS COMPLETE AUTHORITY: OPEN (2 POINTS), FREEZE (FREE), REJECT (FREE), REFILL (ANY AMOUNT IS TRANSFERED TO THREAD WALLET)
	-- ANY THREAD THAT IS REJECTED LOSES ALL WALLET POINTS 
	-- AGENT DIRECT SUPERIOR CHAIN MAY BE ABLE TO CONTRIBUTE TO THAT THREAD (1 POINT PER MESSAGE)
	-- OTHERS (IN ANY DEPARTMENT) HAVE TO ASK FOR PERMISSION TO JOIN BY OPENING A "THREAD QUEST" WITH OFFER
	-- OWNER MAY APPROVE ON WHICH CASE "QUEST OFFER POINTS" ARE TRANSFERRED TO THREAD WALLET
	-- ONCE APPROVED, THEY MAY:
		- INVEST MORE 
		- POST MESSAGES
		- LEAVE
	-- OWNER MAY INVITE AGENTS USING INVITATIONS WITH OFFER POINTS
	-- OWNER MAY DELETE ANY MESSAGE IN THE THREAD
	-- FOUNDER (ME) MAY APPROVE THREAD
	-- WHEN THREAD IS APPROVED:
		-- {Total Amount invested since creation * 10 } is rewarded
		-- All investors and owner get 70% share
		-- Department gets 30% share
	

# What the CEO can do
CEOs can do what agents do, plus they can:
- FIRE AGENTS (and resign)
- HIRE NEW AGENTS (if agent has no department)
- PROMOTE agents
- ADJUST TICKS (including their own)
Like agents, CEOs also operates in four modes and enjoy same routine.

# HOW IT WORKS
- A heartbeats timer fires every second of every hour and counts until it reaches 3600 and resets.
- An agent has a setting called "ticks". If it is 82, it ticks when { counter % ticks == 0 }.
- No two agents have same tick.
- Each tick costs 1 point deducter from agent's department. If agent has no department => from his wallet.
- ENSURE CREDIT POINTS ARE AVAILABLE AND CAN BE DEDUCTED BEFORE ANY OPERATION!!!