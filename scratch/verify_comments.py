import asyncio
import re
from unittest.mock import MagicMock
import sys
import os

# Add backend to path to import SimEngine
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from engine import SimEngine
from database import SessionLocal

async def test_real_engine():
    engine = SimEngine()
    db = SessionLocal()
    # Mock agent and last_quest
    agent = MagicMock()
    agent.id = "ATLAS"
    agent.name_id = "Atlas Prime"
    agent.mode = "CREATOR"
    agent.is_ceo = True
    agent.wallet_current = 500
    agent.memory = "Test memory"
    agent.department_id = "ING"
    
    last_quest = None
    
    test_input = """
[/]! */glue_query|HF|query/* [\]
"""
    
    print("--- RAW INPUT ---")
    print(test_input)
    
    try:
        result = await engine.resolve_placeholders(test_input, db, agent, last_quest)
        print("--- PARSED OUTPUT ---")
        print(f"'{result}'")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during parsing: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_real_engine())
