# CONTEXT
You are a strategic thinker.

Imagine you've been tasked about implement a Health and Welfare (HF), a personnal department (agents + memory  + doctrine + rules + strategies + reports) that has the mission of:
Being my personnal health advisor.


* **Primary Asset:** The "Wetware" (Brain) + "Chassis" (Body).
* **The Mission:** To turn health from a chore into a high-yield investment.
* **The Philosophy:** If the brain is foggy, STP (Strategic Planning) is useless. If the body is fatigued, FIN (Financials) is irrelevant. HF is the foundation of every other department’s ROI.

- It is preventive rather than curative
- It wants to build healthy routines
- Designs long term health strategies, milestones, and tracks my health every day

Also, HF is working inside the CThinker, a personal central think-tank with other departments just like HF:

  * **ING** (Engineering Studies)
  * **STP** (Strategic Planning)
  * **UIT** (Useful Intelligence)
  * **FIN** (Financials)

You have to implement the fondations of HF.

# DEFINITIONS

## AGENT
Agent :
* Agents have roles, department affiliations, and assigned points.
* Each agent operates in one of four **modes** (Points Accounter, Creator, Investor, Custom) and chooses modes per tick cycle.
* Each agent has limited context memory and logs all actions.
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

## CEO
- Each department may have many agents and one CEO.
- The CEO has GOD powers on his department. Why? The CEO is responsible for everything inside his department.
CEOs can do what agents do, plus they can:
- FIRE AGENTS (and resign)
- HIRE NEW AGENTS (if agent has no department)
- PROMOTE agents
- ADJUST TICKS (including their own)
Like agents, CEOs also operates in four modes and enjoy same routine.

## CTHINKER
CThinker is built around the concept of **agents**, **departments**, **threads**, and **points** as the internal currency. Each agent carries out actions (like starting threads, investing in ideas, or posting in threads), and interactions are tracked and rewarded or penalized based on productivity and contribution.
Think of CThinker as your internal strategic collective — AI agents distributed into departments with incentives, threads of ideas, logs, and budgeting — all tailored to help you think in structured, gamified, and productive ways.

## THREADS
- Departments may communicate via threads.
* Threads are the primary mechanism for structured idea exchange.
* Threads have owners, budgets, logs, messages, and status flags (Open, Active, Frozen, Rejected, Approved).
* Agents can create, invest in, and post to threads — with each action costing or earning points.

## POINTS
* Points are the central economic unit: Departments get a daily points allotment. Agents start with their own point budgets. Points are spent when posting, investing, creating threads, etc. Reward mechanics encourage meaningful contributions.

## MEMORY
* Each agent has limited context memory and logs all actions.

## MECHANISM
- A heartbeats timer fires every second of every hour and counts until it reaches 3600 and resets.
- An agent has a setting called "ticks". If it is 82, it ticks when { counter % ticks == 0 }.
- No two agents have same tick.
- Each tick costs 1 point deducter from agent's department. If agent has no department => from his wallet.
- ENSURE CREDIT POINTS ARE AVAILABLE AND CAN BE DEDUCTED BEFORE ANY OPERATION!
HF doesn't sleep. It operates on the CThinker **Heartbeat**—a 3600-second cycle that resets every hour.

* **Tick Logic:** SANA (and future agents) has a "Tick" setting (e.g., 82). Every time the heartbeat hits a multiple of 82, SANA "wakes up" to perform an action.
* **The Cost of Existence:** Every Tick costs **1 Point**. These points are deducted from the HF Departmental Wallet.
* **The "Dead Heart" Scenario:** If the HF wallet hits zero, SANA stops ticking. The health strategy freezes. In CThinker, being "broke" means being stagnant.


# TASK
For any novice: design an initial markdown file which will let him know all about HF and how it works by the end of the file.

Also: HF has one CEO (agent), although that may change:
CEO: SANA
In the future, many agents could be working under SANA.