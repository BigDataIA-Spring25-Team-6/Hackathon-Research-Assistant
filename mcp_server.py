from mcp.server.fastmcp import FastMCP
from agents.snowflake_agent import snowflake_tool

mcp = FastMCP("Retail Research MCP")

@mcp.tool()
def snowflake_tool_wrapper(query: str, platform: str, date_start: str = None, date_end: str = None):
    return snowflake_tool(query, platform, date_start, date_end)

if __name__ == "__main__":
    mcp.run()