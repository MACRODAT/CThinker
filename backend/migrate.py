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
    except Exception as e:
        print("custom_directives:", e)

    # Add next_mode to agents (for self-selection preview)
    try:
        c.execute('ALTER TABLE agents ADD COLUMN next_mode TEXT')
        print("Added next_mode to agents")
    except Exception as e:
        print("next_mode:", e)

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
    except Exception as e:
        print("custom_prompt_entries table:", e)

    conn.commit()
    conn.close()
    print("Migration complete.")

run()
