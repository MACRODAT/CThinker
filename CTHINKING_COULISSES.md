Wondering about how CTHNKING Works ? here is how!

## 1. The Core Engine of Syntax: resolve_placeholders
This method is the "brain" of the Tool Workshop—it turns raw prompt templates into living, context-aware instructions for agents.

Looking at the code, what do you notice about the iterative loop (the for _ in range(MAX_RECURSION) with 20 passes)? Why does it process text "inside-out" using specific regex patterns for innermost elements first? What problem does this solve when prompts contain nested placeholders or tool calls?
How many distinct syntax "flavors" does it support? Can you list them and give a one-line description of each based on the _process_innermost_regex calls?

## 2. Simple Variable Placeholders {key}
These are the easiest to spot and replace.

In the simple dictionary inside resolve_placeholders, what are all the available keys (e.g., {agent}, {thread_summary})?
Where do the values come from? (Hint: look at the helper methods like get_available_tickets_context, get_rich_invitation_context, get_thread_summaries_context, etc.)
Imagine an agent prompt containing {pending_invitation}. What would the agent actually "see" after resolution, and why is that useful?

## 3. Conditional Blocks {{ key ... /ELSE/ ... }}
These let prompts adapt dynamically based on the world state.

Study _eval_conditional (and the earlier bool_ctx dictionary). Which four boolean conditions are tracked?
How does the parser decide what to keep when /ELSE/ is present versus when it's absent?
Can you invent a short example prompt snippet that uses {{ available_tickets_exist }} to show different text depending on whether unused tickets exist? (Write it exactly as it would appear in a PromptTemplate.)

## 4. Block Tool Calls [CALL_TOOL] ... [END_CALL_TOOL]
This is the heavy artillery of the Tool Workshop—agents can invoke full tools with arguments.

How does the parser (_eval_block_tool) extract the tool name and arguments from the block?
Trace the flow: after parsing, where does execution actually happen? (Look at run_tool_logic.)
What happens to the original block text after execution? How is the result fed back into the prompt?

## 5. Inline Tool Calls */tool|arg1|arg2/*
A more compact, "one-liner" way to call tools.

Compare this syntax to the block version. Why might an agent prefer one over the other?
How is it parsed and routed in _eval_inline_func?
Give an example of how an agent might use */get_time/* or */get_weather|Casablanca/* inside a larger prompt.

## 6. The Universal Tool Execution Hub: run_tool_logic + execute_tool_logic
This is where the magic (and economics!) really lives.

What are the three main phases inside run_tool_logic?
How does it distinguish built-in system tools (like create_thread, invest_thread, approve_join) from custom DB tools (is_custom=True)?
Economic enforcement is everywhere. What happens if an agent tries to use a priced tool or a thread action without enough points? How is the user guided?

Mini-exercise for you: Pick one built-in tool (e.g., create_thread or post_in_thread). From the code in execute_tool_logic, extract:

Required arguments
Cost rules
Success/failure return strings
Any side effects (DB changes, messages posted, etc.)
Write a short "Tool Card" in your own words as if it were a documentation entry.

## 7. Custom Tools & Advanced Features

How does execute_custom_tool turn a DB-stored AgentTool into executable logic?
What role do file operations (CREATE_FILE, READ_FILE) and HTTP calls play? Where are they sandboxed?

## 8. Tying It All Together: Prompt Flow in handle_agent_tick

Trace one full agent tick: how do placeholders, memory, mode changes, and tool results flow into the final LLM call?
Why are there two passes of placeholder resolution (before and after .format())?