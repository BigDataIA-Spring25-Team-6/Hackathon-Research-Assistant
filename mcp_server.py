from mcp.server.fastmcp import FastMCP
from agents.snowflake_agent import snowflake_tool
from agents.image_generator_agent import analyze_prompt,generate_image_dalle

mcp = FastMCP("Retail Research MCP")

@mcp.tool()
def snowflake_tool_wrapper(query: str, platform: str, date_start: str = None, date_end: str = None):
    return snowflake_tool(query, platform, date_start, date_end)

@mcp.tool()
def image_generator_tool_wrapper(query: str):
    refined_prompt = analyze_prompt(query)
    return generate_image_dalle(refined_prompt)


if __name__ == "__main__":
    mcp.run()