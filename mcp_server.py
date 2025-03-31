from mcp.server.fastmcp import FastMCP
from agents.snowflake_agent import snowflake_tool
from agents.web_agent import web_search_tool

mcp = FastMCP("Retail Research MCP")

@mcp.tool()
def snowflake_tool_wrapper(query: str, platform: str, date_start: str = None, date_end: str = None):
    return snowflake_tool(query, platform, date_start, date_end)

@mcp.tool()
def web_search_wrapper(query: str):
    return web_search_tool(query)

if __name__ == "__main__":
    mcp.run()