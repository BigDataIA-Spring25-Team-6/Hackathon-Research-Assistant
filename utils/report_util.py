import os
import json
import re
from langchain_openai import ChatOpenAI
from agents.final_report_agent import FinalReportInput, final_report_tool
from langgraph_code.langgraph_flow import graph

from dotenv import load_dotenv
 
load_dotenv()


def generate_structured_summary_from_logs(state):
    # Extract logs from all AgentAction objects
    logs = [action.log for action in state["intermediate_steps"]]
    print("\n\n\n\n\n\n\n\n\n\n Data")
    print(logs)
    combined_logs = "\n\n".join(logs)
   
    # Optionally, use a regex to capture any URLs that might be missing (not strictly needed if logs include them)
    url_pattern = r'https?://\S+'
    found_urls = re.findall(url_pattern, combined_logs)
    if found_urls:
        # Append found URLs (if any) to the combined logs to ensure they get included in sources.
        combined_logs += "\n\n" + ", ".join(found_urls)
   
    # Create a prompt for the LLM to extract the six structured keys
    prompt = f"""
You are a seasoned business analyst. Based on the following logs, produce a JSON object with exactly the following keys:
- "executive_summary": A concise summary of the key findings.
- "market_overview": A summary of market trends and context.
- "internal_insights": Any insights from internal or platform-specific data.
- "quantitative_analysis": A detailed summary of any numerical data, statistics, or chart-related information.
- "recommendations": Actionable recommendations based on the data.
- "sources": A comma-separated list of all URLs or source references found in the logs.
If no data is available for a field, use an empty string.
Return only valid JSON with exactly these keys and no additional text.
 
Logs:
{combined_logs}
    """
   
    llm = ChatOpenAI(
        model="gpt-4o",
        openai_api_key=os.environ["OPENAI_API_KEY"],
        temperature=0
    )
   
    response = llm.invoke(prompt).content
    try:
        response = response.strip("` \n")
        response_clean = response.replace("json", "", 1).strip()
        print(response_clean)
        structured_summary = json.loads(response_clean)
    except Exception as e:
        # In case parsing fails, return an object with empty values.
        structured_summary = {
            "executive_summary": "",
            "market_overview": "",
            "internal_insights": "",
            "quantitative_analysis": "",
            "recommendations": "",
            "sources": ""
        }
        
    final_report_md = final_report_tool.invoke(structured_summary)

    return final_report_md