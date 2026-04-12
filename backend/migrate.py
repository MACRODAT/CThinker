import sqlite3
import os

def run():
    db_path = os.path.join(os.path.dirname(__file__), 'cthinker.db')
    print("Connecting to", db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Add custom_directives to prompt_templates
    try:
        c.execute('ALTER TABLE prompt_templates ADD COLUMN custom_directives TEXT')
        print("Added custom_directives to prompt_templates")
    except Exception as e: print("custom_directives:", e)

    # Add next_mode to agents (for self-selection preview)
    try:
        c.execute('ALTER TABLE agents ADD COLUMN next_mode TEXT')
        print("Added next_mode to agents")
    except Exception as e: print("next_mode:", e)

    # Create custom_prompt_entries table
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS custom_prompt_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created TEXT DEFAULT (datetime('now'))
            )
        ''')
        print("Created custom_prompt_entries table")
    except Exception as e: print("custom_prompt_entries table:", e)

    # Add total_invested and last_tax_check to threads
    try:
        c.execute('ALTER TABLE threads ADD COLUMN total_invested INTEGER DEFAULT 0')
        print("Added total_invested to threads")
    except Exception as e: print("total_invested:", e)
    
    try:
        c.execute('ALTER TABLE threads ADD COLUMN last_tax_check TEXT')
        print("Added last_tax_check to threads")
    except Exception as e: print("last_tax_check:", e)

    # Create thread_collaborators TABLE
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS thread_collaborators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                agent_id TEXT,
                joined_at TEXT,
                FOREIGN KEY(thread_id) REFERENCES threads(id),
                FOREIGN KEY(agent_id) REFERENCES agents(id)
            )
        ''')
        print("Created thread_collaborators table")
    except Exception as e: print("thread_collaborators table:", e)

    # Create join_quests TABLE
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS join_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                agent_id TEXT,
                offer_points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'PENDING',
                created TEXT,
                FOREIGN KEY(thread_id) REFERENCES threads(id),
                FOREIGN KEY(agent_id) REFERENCES agents(id)
            )
        ''')
    except Exception as e: print("join_quests table creation:", e)

    try:
        c.execute('ALTER TABLE join_quests ADD COLUMN is_invite BOOLEAN DEFAULT 0')
        print("Added is_invite to join_quests")
    except Exception as e: print("is_invite:", e)

    try:
        c.execute('ALTER TABLE join_quests ADD COLUMN is_read BOOLEAN DEFAULT 0')
        print("Added is_read to join_quests")
    except Exception as e: print("is_read:", e)

    try:
        c.execute('ALTER TABLE join_quests ADD COLUMN expires_at TEXT')
        print("Added expires_at to join_quests")
    except Exception as e: print("expires_at:", e)

    conn.commit()
    conn.close()
    print("Migration complete.")

run()
