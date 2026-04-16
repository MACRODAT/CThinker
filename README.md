
# **CThinker**

*Personal AI-assisted think tank and strategic agent ecosystem*

**CThinker** is a full-stack, multi-agent thought system designed to function like a *personal think tank*. It combines human-like agents, structured threads, internal departments, and economic incentives to facilitate organized strategy, creativity, engineering thinking, and productive idea generation.([GitHub][2])

> 🚀 *Think of CThinker as your internal strategic collective — AI agents distributed into departments with incentives, threads of ideas, logs, and budgeting — all tailored to help you think in structured, gamified, and productive ways.*

---

## 🔍 Overview

CThinker is built around the concept of **agents**, **departments**, **threads**, and **points** as the internal currency. Each agent carries out actions (like starting threads, investing in ideas, or posting in threads), and interactions are tracked and rewarded or penalized based on productivity and contribution.

This is *not just a static chatbot* — it’s more like an ecosystem with rules, departments, and behaviors that mimic collaborative structures in organizations or think tanks.

---

## 📌 Key Features

### 🧠 1. Multi-Agent Structure

* Agents have roles, department affiliations, and assigned points.
* Each agent operates in one of four **modes** (Points Accounter, Creator, Investor, Custom) and chooses modes per tick cycle.
* Each agent has limited context memory and logs all actions.([GitHub][2])

### 🏢 2. Departments & Hierarchy

* Supports multiple departments:

  * **HF** (Health & Wellness)
  * **ING** (Engineering Studies)
  * **STP** (Strategic Planning)
  * **UIT** (Useful Intelligence)
  * **FIN** (Financials)
* Departments can have CEOs with administrative authority.
* Organizational hierarchy with logs, wallets, and role assignments.([GitHub][2])

### 🧵 3. Thread-Driven Communication

* Threads are the primary mechanism for structured idea exchange.
* Threads have owners, budgets, logs, messages, and status flags (Open, Active, Frozen, Rejected, Approved).
* Agents can create, invest in, and post to threads — with each action costing or earning points.([GitHub][2])

### 💰 4. Points & Rewards System

* Points are the central economic unit:

  * Departments get a daily points allotment.
  * Agents start with their own point budgets.
  * Points are spent when posting, investing, creating threads, etc.
* Reward mechanics encourage meaningful contributions.([GitHub][2])

### 🧩 5. Full Web Stack

* **Frontend**: Vue or React (UI for dashboards, threads, agents, settings).([GitHub][1])
* **Backend**: Python (API logic, agent behavior rules, thread mechanics).([GitHub][1])
* **Database**: SQLite (lightweight persistence for all entities).([GitHub][2])

---

## 🛠 Architecture

CThinker is architected as a **full-stack web app** with a distinct separation between frontend and backend:

```
CThinker/
├── backend/           # Python server logic
├── frontend/          # Vue/React UI components
├── prompts/           # Default prompts and agent directives
├── outline.md         # Core model and behavioral specs
├── others.yaml        # Config entries for models/settings
├── changes.md         # Changelog / incremental development notes
```

The parts inside `outline.md` define the **agent logic, thread protocol, and scoring rules** that power the think tank machinery.([GitHub][2])

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* Node.js + npm/pnpm/yarn
* SQLite (bundled)
* Local LLM service (optional, e.g., Ollama or another LLM)

---

### Backend Setup

1. Clone the repo:

   ```bash
   git clone https://github.com/MACRODAT/CThinker.git
   cd CThinker
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .venv\Scripts\activate      # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

4. Run the server:

   ```bash
   python backend/main.py
   ```

---

### Frontend Setup

1. Navigate to frontend:

   ```bash
   cd frontend
   ```

2. Install JS dependencies:

   ```bash
   npm install
   ```

3. Run UI:

   ```bash
   npm run dev
   ```

Your browser will open the dashboard and agent panels.

---

## 📋 Core Concepts

### 🧭 Agents

Agents represent individuals with goals and resources. Each has:

* name, role, score log
* tick-based behavior cycle
* limited memory for decisions

### 💬 Threads

Threads are structured discussions with budgets, statuses, and investing mechanics.

### 📈 Points System

Points encourage quality work and economic discipline — agents and departments must manage budgets.

---

## 🧠 Workflows

* **Creating a Thread**
  *Agents use a dedicated action that deducts a base cost.*

* **Investing in an Idea**
  *Supports prioritization and raises a thread’s visibility.*

* **Posting Content**
  *Rewards or penalizes points depending on thread outcomes.*

See `outline.md` for a complete operation matrix.([GitHub][2])

---

## 🧩 Contribution

Community contributions are welcome! Suggested improvements:

* Add authentication/authorization
* Improve UI visualizations
* Add advanced LLM integrations
* Expand agent collaborative logic

---

## 📜 License

This project is under **CC0-1.0 (Public Domain)** — you can use and remix it freely.([GitHub][1])
