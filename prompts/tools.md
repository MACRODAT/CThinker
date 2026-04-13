# TOOLS
## INSTRUCTION
You can call tools as much as you need:
- Formulate response STRICTLY in format below.
- Tool is called (cost: 1 point)
- You get a response
- You may continue your final response or call a tool again

## FORMAT
[CALL_TOOL]
- tool_name
- argument 1
- argument 2
[END_CALL_TOOL]


{{
  pending_quests_exist
    # AVAILABLE TOOLS are only quest tools:
    {all_quest_tools}
  /ELSE/
    # AVAILABLE TOOLS are all tools:
    {all_enabled_tools}
}}