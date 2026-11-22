"""
helpers.py

Small helper functions used by agent.py:
  list_threads   - which people already have a saved chat
  show_history   - print everything saved for one person
  repair_history - fix a tool call that never got an answer (Task 6)
  stream_reply   - send one message and print the answer as it arrives (Task 4)
"""

from langchain.messages import AIMessage, HumanMessage, ToolMessage


async def list_threads(memory):
    """Return the thread ids (names) that already have a saved chat."""
    names = []
    async for item in memory.alist(None):  # None = every thread
        thread_id = item.config["configurable"]["thread_id"]
        if thread_id not in names:
            names.append(thread_id)
    return names


async def show_history(app, config):
    """Print the saved messages of this thread, including tool calls."""
    state = await app.aget_state(config)
    messages = state.values.get("messages", [])

    if not messages:
        print("(no history yet)")
        return

    for m in messages:
        if isinstance(m, HumanMessage):
            print("You:", m.text)
        elif isinstance(m, AIMessage):
            for call in m.tool_calls:
                print(f"  [tool call] {call['name']} {call['args']}")
            if m.text:
                print("Agent:", m.text)
        elif isinstance(m, ToolMessage):
            print(f"  [tool result] {m.text}")


async def repair_history(app, config):
    """Answer any tool call that never got a result.

    If the server dies in the middle of a run, the saved chat ends with a tool
    call that has no answer. Most model APIs (Groq too) refuse such a chat, so
    the person would be stuck forever. Here we add a ToolMessage that tells the
    model the tool did not run.
    """
    state = await app.aget_state(config)
    messages = state.values.get("messages", [])

    answered = set()
    for m in messages:
        if isinstance(m, ToolMessage):
            answered.add(m.tool_call_id)

    fixes = []
    for m in messages:
        if isinstance(m, AIMessage):
            for call in m.tool_calls:
                if call["id"] not in answered:
                    fixes.append(
                        ToolMessage(
                            content="Error: the tool server was not available, so this tool did not run.",
                            tool_call_id=call["id"],
                            name=call["name"],
                            status="error",
                        )
                    )

    if fixes:
        await app.aupdate_state(config, {"messages": fixes})


async def stream_reply(app, text, config):
    """Send one new message and print the answer piece by piece.

    We ask for two kinds of chunks at once:
      "messages" - one small piece of the model's answer (a token)
      "updates"  - what a node returned when it finished a step
    """
    inputs = {"messages": [HumanMessage(text)]}  # only the NEW message
    line_open = False  # True while we are in the middle of printing the answer

    async for chunk in app.astream(
        inputs, config, stream_mode=["updates", "messages"], version="v2"
    ):
        if chunk["type"] == "messages":
            token, metadata = chunk["data"]
            if metadata["langgraph_node"] == "model" and token.text:
                if not line_open:
                    print("Agent: ", end="", flush=True)
                    line_open = True
                print(token.text, end="", flush=True)

        else:  # "updates"
            for node, update in chunk["data"].items():
                if not isinstance(update, dict):
                    continue
                for m in update.get("messages", []):
                    if line_open:
                        print()
                        line_open = False
                    if node == "model":
                        for call in m.tool_calls:
                            print(f"  ... calling {call['name']} {call['args']}")
                    elif node == "tools":
                        print(f"  ... {m.name} returned: {m.text}")

    if line_open:
        print()
