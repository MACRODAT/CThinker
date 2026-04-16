"""
migrate_glue.py — Add vault_id column to threads table for GLUE wiki linking.
Safe to re-run: checks if column already exists.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cthinker.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check existing columns
    cur.execute("PRAGMA table_info(threads)")
    cols = [row[1] for row in cur.fetchall()]

    if "vault_id" not in cols:
        cur.execute("ALTER TABLE threads ADD COLUMN vault_id TEXT")
        print("[migrate_glue] Added vault_id column to threads.")
    else:
        print("[migrate_glue] vault_id column already exists.")

    conn.commit()
    conn.close()
    print("[migrate_glue] Done.")


if __name__ == "__main__":
    migrate()
