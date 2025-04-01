from langchain_core.tools import tool
from agents.snowflake_agent import snowflake_tool as raw_snowflake_tool
from agents.web_agent import web_search_tool as raw_web_tool
from agents.image_generator_agent import image_agent as raw_image_tool
from agents.final_report_agent import final_report_tool
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0)


@tool("snowflake_tool")
def snowflake_tool(query: str, platform: str, date_start: str = None, date_end: str = None) -> str:
    """Search retail keyword demand data from Snowflake using filters like platform, start date, and end date."""
    return raw_snowflake_tool(query, platform, date_start, date_end)


@tool("web_search_tool")
def web_search_tool(query: str) -> str:
    """Find recent articles and videos from the web using Tavily and YouTube, with image extraction from webpages."""
    return raw_web_tool(query)


@tool("image_generator_tool")
def image_generator_tool(query: str) -> str:
    """Generate a visual image based on a descriptive prompt using DALL·E and prompt optimization via Mistral."""
    return raw_image_tool(query)