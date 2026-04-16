import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cthinker.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE agents ADD COLUMN system_prompt TEXT")
        cursor.execute("ALTER TABLE agents ADD COLUMN user_prompt TEXT")
    except sqlite3.OperationalError as e:
        print("Columns might already exist:", e)

    # Fetch templates
    cursor.execute("SELECT id, system_prompt, user_prompt_template, custom_directives FROM prompt_templates")
    templates = {row[0]: row for row in cursor.fetchall()}

    # Fetch agents
    cursor.execute("SELECT id, mode, custom_prompt, memory FROM agents")
    agents = cursor.fetchall()

    for agent_id, mode, custom_prompt, memory in agents:
        template = templates.get(mode) or templates.get("Creator")
        if not template:
            sys_pr = ""
            usr_pr = "TASK:\n{{tools}}"
            dir_text = ""
        else:
            _, sys_prompt, usr_prompt, custom_dir = template
            sys_pr = sys_prompt or ""
            usr_pr = usr_prompt or ""
            dir_text = custom_dir or ""
        
        # Merge directives into system_prompt
        final_sys = sys_pr
        if dir_text:
            final_sys += f"\n\n# MODE DIRECTIVES\n{dir_text}"
        if custom_prompt:
            final_sys += f"\n\n# PERSONAL DIRECTIVES\n{custom_prompt}"
            
        # Transform python .format vars to placeholder vars
        final_usr = usr_pr.replace("{tools}", "{{tools}}").replace("{actions}", "{{actions}}").replace("{memory}", "{{memory}}").replace("{dept}", "{{dept}}").replace("{wallet}", "{{wallet}}").replace("{name}", "{{name}}").replace("{id}", "{{id}}").replace("{directives}", "").replace("{message}", "{{message}}")

        cursor.execute("UPDATE agents SET system_prompt = ?, user_prompt = ? WHERE id = ?", (final_sys, final_usr, agent_id))

    conn.commit()
    conn.close()
    print("Migration successful.")

if __name__ == "__main__":
    migrate()
