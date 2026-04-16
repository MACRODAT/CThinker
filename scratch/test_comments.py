import asyncio
import re
from unittest.mock import MagicMock

# Mocking parts of engine.py for testing
class MockEngine:
    def _eval_conditional(self, raw, bool_ctx):
        inner = raw[2:-2].strip()
        lines = inner.split("\n", 1)
        key = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        cond = bool_ctx.get(key, False)
        if "/ELSE/" in body:
            parts = body.split("/ELSE/", 1)
            return parts[0].strip() if cond else parts[1].strip()
        return body.strip() if cond else ""

    async def _eval_inline_func(self, raw, db, agent, add_step_cb):
        return f"[FUNC:{raw[2:-2]}]"

    async def _process_innermost_regex(self, text, pattern, func):
        matches = list(re.finditer(pattern, text, re.DOTALL))
        for m in reversed(matches):
            res = func(m.group(0))
            if asyncio.iscoroutine(res):
                res = await res
            text = text[:m.start()] + str(res) + text[m.end():]
        return text

    async def resolve_placeholders(self, text: str, db, agent, last_quest, add_step_cb=None, extra_ctx=None) -> str:
        # Context Maps (Mocked)
        bool_ctx = {
            "test_true": True,
            "test_false": False
        }
        simple = {
            "agent": "TestAgent"
        }
        if extra_ctx:
            simple.update(extra_ctx)

        # INSERT COMMENT REMOVAL HERE
        # text = ...

        MAX_RECURSION = 5
        for _ in range(MAX_RECURSION):
            original = text
            for k, v in simple.items():
                text = text.replace(f"{{{str(k)}}}", str(v))
                text = text.replace(f"{{{{{str(k)}}}}}", str(v))

            text = await self._process_innermost_regex(
                text, r"\{\{(?:(?!\{\{|\}\}).)*?\}\}", 
                lambda m: self._eval_conditional(m, bool_ctx)
            )

            text = await self._process_innermost_regex(
                text, r"\*\/(?:(?!\*\/|\/\*).)*?\/\*", 
                lambda m: self._eval_inline_func(m, db, agent, add_step_cb)
            )

            if text == original:
                break
        return text

async def test():
    engine = MockEngine()
    
    # Test cases
    test_input = """
// Inline comment
Hello {agent}!
[/] Multiline
comment [\]
This is a test.
URL: http://example.com/page
*/FUNC|ARG/* // Comment after call
{{ test_true
Visible text // Nested comment?
/ELSE/
Hidden
}}
"""
    
    # Expected after implementation of comment removal:
    # Hello TestAgent!
    # 
    # This is a test.
    # URL: http://example.com/page
    # [FUNC:FUNC|ARG] 
    # Visible text 
    
    # We will refine the implementation here to see what works
    def strip_comments(text):
        # Remove multiline comments [/] ... [\]
        text = re.sub(r'\[/\].*?\[\\\]', '', text, flags=re.DOTALL)
        # Remove inline comments // ... (but not in URLs)
        text = re.sub(r'(?<!:)\/\/.*', '', text)
        return text

    print("--- RAW INPUT ---")
    print(test_input)
    
    processed = strip_comments(test_input)
    print("--- STRIPPED COMMENTS ---")
    print(processed)
    
    # Try with resolve_placeholders logic (manual integration for now)
    # ...
    
if __name__ == "__main__":
    asyncio.run(test())
