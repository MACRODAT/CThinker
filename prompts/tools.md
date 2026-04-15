# TOOLS
## INSTRUCTION
Here are available tools. Tools depend on chosen Mode.
You can call tools as much as you need:
- Formulate response STRICTLY in format below.
- Tool is called (cost: 1 point)
- You get a response
- You may continue your final response or call a tool again

{{
  pending_quests_exist
## AVAILABLE TOOLS are only quest tools. Either Accept/Decline all quests to access other tools:
{all_quest_tools}
  /ELSE/
      {{
        mode_is_creator
## THREAD TOOLS are:
{thread_tools}
        /ELSE/  
      }}
      {{
        mode_is_points_accounter
## ACCOUTING TOOLS are:
{points_accounter_tools}
        /ELSE/
      }}
      {{
        mode_is_custom
## ALL TOOLS are:
{all_enabled_tools}
        /ELSE/
      }}
      {{
        mode_is_investor
## INVESTMENT TOOLS are:
{investor_tools} 
        /ELSE/
      }}
}}