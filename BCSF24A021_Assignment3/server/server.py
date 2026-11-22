"""
server.py

The MCP server. It shares every tool from tools.py over the network.
Any MCP client (our agent, or a friend's agent in another language) can
ask "what tools do you have?" (tools/list) and then run one (tools/call).

Run it with:  python server.py   ->  http://127.0.0.1:8000/mcp
"""

import os

from fastmcp import FastMCP

from tools import (
    marks_to_grade_points,
    calculate_semester_gpa,
    calculate_new_cgpa,
    required_gpa_for_target,
    get_semester_courses,
    get_remaining_credit_hours,
    get_credit_hours,
    save_report,
)

mcp = FastMCP("cgpa")

# Each call turns one plain function into an MCP tool.
mcp.tool(marks_to_grade_points)
mcp.tool(calculate_semester_gpa)
mcp.tool(calculate_new_cgpa)
mcp.tool(required_gpa_for_target)
mcp.tool(get_semester_courses)
mcp.tool(get_remaining_credit_hours)
mcp.tool(get_credit_hours)
mcp.tool(save_report)


if __name__ == "__main__":
    # Locally these defaults are used. A hosting service (like Render) sets
    # HOST and PORT itself. Horizon ignores this block and runs `mcp` directly.
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)
