import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cthinker.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        CREATE TABLE agent_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id VARCHAR NOT NULL,
            mode VARCHAR NOT NULL,
            system_prompt TEXT DEFAULT '',
            user_prompt TEXT DEFAULT '',
            FOREIGN KEY(agent_id) REFERENCES agents(id)
        )
        """)
        cursor.execute("CREATE INDEX idx_agent_prompts_agent_id ON agent_prompts(agent_id)")
    except sqlite3.OperationalError as e:
        print("Table might already exist:", e)

    # Fetch agents and their legacy prompts
    cursor.execute("SELECT id, mode, system_prompt, user_prompt FROM agents")
    agents = cursor.fetchall()

    for agent_id, mode, sys_prompt, usr_prompt in agents:
        agent_mode = mode if mode else "Custom"
        
        # Check if row exists
        cursor.execute("SELECT id FROM agent_prompts WHERE agent_id = ? AND mode = ?", (agent_id, agent_mode))
        if cursor.fetchone():
            continue
            
        sys_pr = sys_prompt or ""
        usr_pr = usr_prompt or ""

        cursor.execute(
            "INSERT INTO agent_prompts (agent_id, mode, system_prompt, user_prompt) VALUES (?, ?, ?, ?)",
            (agent_id, agent_mode, sys_pr, usr_pr)
        )

    conn.commit()
    conn.close()
    print("Migration successful.")

if __name__ == "__main__":
    migrate()
