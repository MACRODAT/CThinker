"""
Migration: Add marketplace columns to agent_tools + create tool_ownerships table.
Run once: python migrate_marketplace.py
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "cthinker.db"

COLUMNS = [
    ("status",             "TEXT DEFAULT 'STANDARD'"),
    ("ownership_price",    "INTEGER DEFAULT 0"),
    ("category",           "TEXT DEFAULT 'General'"),
    ("created_by",         "TEXT"),
    ("purchase_count",     "INTEGER DEFAULT 0"),
    ("tags",               "TEXT DEFAULT '[]'"),
    ("version",            "TEXT DEFAULT '1.0'"),
    ("workshop_validated", "INTEGER DEFAULT 0"),
    ("changelog",          "TEXT"),
]

CREATE_OWNERSHIPS = """
CREATE TABLE IF NOT EXISTS tool_ownerships (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id     TEXT REFERENCES agents(id),
    tool_id      TEXT REFERENCES agent_tools(id),
    purchased_at TEXT,
    price_paid   INTEGER DEFAULT 0
);
"""

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Add missing columns to agent_tools
    cur.execute("PRAGMA table_info(agent_tools)")
    existing = {row[1] for row in cur.fetchall()}
    for col, typedef in COLUMNS:
        if col not in existing:
            cur.execute(f"ALTER TABLE agent_tools ADD COLUMN {col} {typedef}")
            print(f"  + agent_tools.{col}")
        else:
            print(f"  = agent_tools.{col} (already exists)")

    # Mark all existing tools as STANDARD if not set
    cur.execute("UPDATE agent_tools SET status='STANDARD' WHERE status IS NULL OR status=''")

    # Create ownerships table
    cur.execute(CREATE_OWNERSHIPS)
    print("  ✓ tool_ownerships table ready")

    con.commit()
    con.close()
    print("Migration complete.")

if __name__ == "__main__":
    main()
