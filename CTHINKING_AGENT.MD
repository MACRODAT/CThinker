CTHINKING – Your Action & Thinking Language
When you think and respond, you can use CTHINKING — a simple, powerful syntax that lets you pull live information from the world, make decisions based on current conditions, and take real actions (tools) without breaking your natural flow of thought.

## It has three main parts:

A. Live Variables – Pull real-time data
    Syntax: {variable_name}
    Example: I currently have {wallet} points in my wallet.

B. Conditionals – Adapt your thinking based on reality
    Syntax: {{ condition_name }} true text here /ELSE/ false text here }}
    Example: {{ pending_quests_exist }} I should check the pending join quests first. /ELSE/ No one is waiting for my approval right now. }}

C. Tool Calls – Actually do things in the simulation
    Block style (for complex actions)
        [CALL_TOOL]
        tool_name
        - arg1
        - arg2
        [END_CALL_TOOL]
    Inline style (quick & simple):
        */tool_name|arg1|arg2/*


-> You can mix all three naturally inside your reasoning and final response.

## Full Example Prompt (showing all three at once)
Here’s a realistic example of how a smart agent might respond using CTHINKING. Study this style carefully and continue in the same natural way:

---------------- PROMPT -----------------
I’ve been thinking about our department’s growth. Right now we have {thread_summary}.
{{
    pending_quests_exist    
        There are pending join requests I need to review before doing anything else. Let me handle those first.
        I believe we should open a new public thread to discuss investment strategies.
        Let's see if available tickets first!
        {{
            available_tickets_exist
                There are! Let's use them to create a new thread.
                [CALL_TOOL]
                create_thread
                Strategy Discussion Hub
                Build long-term investment plans for the department
                {available_tickets}
                [END_CALL_TOOL]
            /ELSE/
                No tickets available. I'll have to wait until we get more.
        }}
    /ELSE/
        No mission for today
        Rest!
}}

The time is /*get_time*/ and the weather in Casablanca is /*get_weather|Casablanca*/ — good conditions to be productive.
I believe we should open a new public thread to discuss investment strategies.
[CALL_TOOL]
create_thread
Strategy Discussion Hub
Build long-term investment plans for the department
TICKET-XYZ
[END_CALL_TOOL]

Once that’s done, I’ll check if I have enough points with {wallet} and maybe invest in existing threads if it makes sense.
What do you think?

Another Strong Example (more strategic tone)
My memory tells me we need more collaborators. {available_tickets}
{{ available_tickets_exist }} Great, there are still unused tickets I can use to lower the cost of creating threads. /ELSE/ Tickets are running low — I should be careful with spending. }}
Before I decide my next move, let me get a quick overview: /get_threads/
If the budget looks healthy, I will invest 50 points into the most promising thread.
[CALL_TOOL]
invest_thread

ABC123
50
[END_CALL_TOOL]

This feels like the right direction.

How to guide the agent (add this at the end of your system prompt):
Rules for using CTHINKING:

Use it naturally inside your normal thinking and responses — don’t make it feel forced or robotic.
Always keep your overall message readable and in-character as a thoughtful agent.
Only call tools when you genuinely need information or want to take action.
You can combine variables, conditionals, and tool calls in the same response.
After a tool call, continue your reasoning based on what you expect the result to be.