"""
agent.py

The CGPA Guider, now with:
  - tools that come from an MCP server (Task 2)
  - memory in a SQLite file, one chat per person (Task 3)
  - streaming answers (Task 4, see helpers.py)
  - a server-down safety net (Task 6)

Run the server first (cd server, then python server.py), then from this
folder:  python agent.py
"""

import asyncio
import os

from dotenv import load_dotenv
from fastmcp import Client
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.mcp import MCPAdapter
from langchain.messages import ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from helpers import list_threads, show_history, repair_history, stream_reply
from llm import llm

load_dotenv()

MCP_URL = os.getenv("MCP_URL")
KEY = os.getenv("FASTMCP_KEY") or None  # empty means "this server needs no key"

# The chats are saved next to this file, so the same chats are found
# wherever you start the program from.
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chats.db")

SYSTEM_PROMPT = """
You are a friendly assistant that helps a PUCIT BS(CS) student with GPA and
CGPA questions.

Follow these rules at all times:

1. Never do any math yourself. Every number you give the student must come
   from a tool call. Your only job is to pick the right tool, fill in the
   right arguments, and explain the result in plain, simple words.

2. Never guess or invent marks, credit hours, a CGPA, or a semester number.
   If you need one of these and the student has not told you, ask for it
   before calling any tool. If they already told you earlier in this
   conversation, use that and do not ask again.

3. When something is missing, ask for one or two things at a time. Do not
   ask a long list of questions in one go.

4. Math Deficiency courses (MD-001, MD-002) are non-credit, pass/fail, and
   never count towards GPA. Every other course counts, including Quran
   Translation courses, even though they are only 0.5 credit hours each.

5. A required GPA above 4.0 is not a real answer. When a student asks what
   GPA they need, start with just their current semester and widen one
   semester at a time. Get the credit hours with get_credit_hours, using
   the list of semesters in the window (for a student in semester 5: [5],
   then [5, 6], then [5, 6, 7]), and pass that result as
   remaining_credit_hours to required_gpa_for_target. If the result is above
   4.0, do not report it - widen the window and try again. Stop when the
   result is 4.0 or below, or when semester 8 is included and it is still
   above 4.0 (then tell the student it is not reachable). Report only the
   narrowest window that works, briefly noting the shorter ones that didn't.

6. Only offer to save a report after you have produced something worth
   keeping, such as a semester GPA, a projected CGPA, or a graduation plan.
   Do not offer this after a clarifying question or a simple lookup, and
   never save a report unless the student agrees.

7. If a tool says the tool server is not available, tell the student that
   the tools are down right now and to try again later. Do not guess numbers.
"""


@wrap_tool_call
async def handle_tool_errors(request, handler):
    """If a tool call fails (for example the server is down), do not crash.

    We return a ToolMessage instead, so the model is TOLD that the tool did
    not run and the saved chat never ends with an unanswered tool call.
    """
    try:
        return await handler(request)
    except Exception as e:
        return ToolMessage(
            content=(
                f"Error: the tool could not run ({type(e).__name__}). "
                "The tool server is probably not available."
            ),
            tool_call_id=request.tool_call["id"],
            name=request.tool_call["name"],
            status="error",
        )


async def ask_name(memory):
    """Show the saved chats, then ask who is chatting. The name is the thread id."""
    saved = await list_threads(memory)
    print("Saved chats:", ", ".join(saved) if saved else "(none yet)")
    name = input("Who is chatting? ").strip().lower()
    return name or "guest"


async def main():
    # 1. Get the tools from the MCP server (connect, list tools, disconnect).
    try:
        server = Client(MCP_URL, auth=KEY)
        tools = await MCPAdapter(server).list_tools()
    except Exception as e:
        print(f"Could not reach the MCP server at {MCP_URL}")
        print(f"({type(e).__name__}: {e})")
        return
    print("Tools from server:", ", ".join(t.name for t in tools))

    # 2. The memory is a SQLite file, so chats survive closing the program.
    async with AsyncSqliteSaver.from_conn_string(DB_FILE) as memory:
        app = create_agent(
            llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=[handle_tool_errors],
            checkpointer=memory,
        )

        name = await ask_name(memory)
        config = {"configurable": {"thread_id": name}}
        print("Commands: /switch  /history  /forget  /quit")

        while True:
            text = input(f"{name}> ").strip()
            if not text:
                continue

            if text == "/quit":
                break
            elif text == "/switch":
                name = await ask_name(memory)
                config = {"configurable": {"thread_id": name}}
            elif text == "/history":
                await show_history(app, config)
            elif text == "/forget":
                await memory.adelete_thread(name)
                print(f"Forgot everything about {name}.")
            else:
                await repair_history(app, config)  # fix any unanswered tool call first
                try:
                    await stream_reply(app, text, config)
                except Exception as e:
                    print(f"\nSomething went wrong ({type(e).__name__}): {e}")


if __name__ == "__main__":
    asyncio.run(main())
