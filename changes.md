Change List:
---------------------

- Agents select operating mode themselves.
- Agents select next mode on current tick.
- In configuration, I need to set up custom directives prompt for each operating mode.
- When running in any mode, load the custom diretive prompt for that SPECIFIC mode.
- add possibility to add / save custom prompt as entries in the database for ease of entry.

- Add view for each department
- Department shows hierarchy of agents


Add more tools:
create_thread(type="Strategy|endeavor|memo", topic: str, aim: str) => Starts a new thread
invest_thread(thread_id: int, budget: int) => Invests budget into thread
post_in_thread(thread_id: int, content: str) => Posts content into thread

IMPORTANT: ENSURE YOU CHECK FIRST IF AGENT HAS SUFFICIENT BUDGET BEFORE CREATING OR INVESTING OR POSTING. IF NOT, RETURN ERROR MESSAGE.