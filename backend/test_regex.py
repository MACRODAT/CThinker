import re

text = "Hello world */web_search|query1/* and then */get_time/* bye."
pattern = r"\*/(.*?)/\*"
matches = list(re.finditer(pattern, text, re.DOTALL))

for m in reversed(matches):
    inner = m.group(1)
    parts = inner.split("|")
    tool_name = parts[0]
    args = parts[1:]
    print(f"Tool: {tool_name}, Args: {args}")
    
    result = f"RESULT_OF_{tool_name}"
    result_str = f" [ {result} ] "
    text = text[:m.start()] + result_str + text[m.end():]

print(f"Processed: {text}")
