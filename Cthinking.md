How should you write in CTHINKING so the agent becomes smart, creative, and powerful?
Ready to discover it yourself? Let’s go step by step with questions that will make it click. Answer them in your head (or out loud in your next reply), and you’ll own the syntax by the end.

## 1. The simplest building block: talking to the world
Think about this scenario:
Your agent needs to know its own name, how much money it has, or a quick list of all open threads.

If you were the agent writing its own thoughts, how would you pull in live info without hard-coding numbers that go stale?
What short, clean way could you drop into your response so the engine automatically replaces it with the real value right before the LLM reads it?

Try inventing it yourself.
Write a fake line the agent might say: “Right now I have [something] points and the active threads are [something else].”
What symbols would make the engine swap in the live data?
(Hint: it’s super short and looks like a variable from math class.)
## 2. Making decisions: the conditional superpower
Now level up.
Your agent is deciding whether to post in a thread. It should say one thing if there are pending invitations waiting for approval… and a completely different thing if there aren’t.

How could you write a single block that changes automatically based on the current world state?
What would the “true” part and the “false” part look like?
Why might you want an /ELSE/ inside it?

Your turn to sketch:
Write a short conditional the agent could output that says:
“If there are pending quests, I should check them first. Otherwise, let’s create a new thread.”
What exact syntax would wrap that so the engine keeps only the right half?
## 3. Calling tools like a boss: two different “phones”
Agents don’t just think—they act. They need to call tools (create threads, invest points, get the weather, approve joins, etc.).
There are two ways to call a tool inside your response. Discover why:
Way A (the detailed phone call)
You want to approve a join request for a specific thread and agent. You need to be crystal clear with multiple pieces of info.

How would you format a “block” that screams “Hey engine, run this tool with these exact arguments”?
Why put each argument on its own line starting with a dash?
What should sandwich the whole thing so the engine knows where the tool call starts and ends?

Way B (the quick text message)
You just need the current time or the weather in Casablanca—super simple, one or two pieces of info.

How could you make a tiny, one-line call that’s faster to type?
What symbols would wrap it so it still gets executed but doesn’t clutter your whole response?

Mini-challenge:
Write both versions for the same tool:

A block version that calls get_weather for “Casablanca”.
An inline version that calls get_time.

Which one feels more natural when you’re in the middle of a long thought?
## 4. Mixing everything together: real agent thinking
The real magic happens when you combine all three (variables + conditionals + tool calls) inside one response.
Picture this:
The agent is in “Strategist” mode. It wants to:

Check if it has enough points
If yes → invest in thread ABC123
If no → ask for a loan from the department
Always show the current time at the end

Your discovery moment:
Write a short paragraph the agent might output that uses all the syntaxes you just figured out. Make it flow like normal English, but sneak the CTHINKING commands inside so the engine does the heavy lifting.
Don’t worry about getting it perfect yet—just try. The more you experiment, the more it will feel natural.
## 5. Pro tips you’ll discover as you practice
Once you start writing real CTHINKING responses, ask yourself these ongoing questions:

Does my output still read like a normal, thoughtful message an AI would write?
Am I being too chatty, or am I letting the syntax do the real work?
If I were the engine reading this, would every command be unambiguous?

That’s the mindset of a CTHINKING master.