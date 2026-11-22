# CGPA Guider - Assignment 3

A chat agent for PUCIT BS(CS) GPA/CGPA questions. Its tools run on an MCP
server, and the agent has memory (SQLite) and streaming answers.

## Links

- MCP server URL: `<paste your hosted URL here, ends with /mcp>`
- API key (only if the server needs one): `<paste key here, or write "none">`
- GitHub repo (server code): `<paste repo link here>`

## Run locally

1. `pip install -r requirements.txt` (from the project folder)
2. Server (terminal 1): `cd server`, then `python server.py`
3. In `agent/`, copy `.env.example` to `.env` and fill in `GROQ_API_KEY`,
   `MCP_URL` (and `FASTMCP_KEY` if the server needs one)
4. Agent (terminal 2): `cd agent`, then `python agent.py`

Commands inside the chat: `/switch`, `/history`, `/forget`, `/quit`

## Files

- `server/server.py` - shares all tools over MCP
- `server/tools.py` - the tool functions (plain Python)
- `server/requirements.txt` - what the hosting service installs
- `agent/agent.py` - the agent, memory and the chat loop
- `agent/helpers.py` - list threads, show history, streaming, repair of unanswered tool calls
- `agent/llm.py` - the Groq model
- `agent/.env.example` - template for the keys and server URL
- `requirements.txt` - packages for the whole project
