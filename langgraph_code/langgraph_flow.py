import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.agents import AgentAction
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator

from langgraph_code.tools import *


# Define LangChain agent state
class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

# --- LLM & prompt setup ---

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key=os.environ["OPENAI_API_KEY"],
    temperature=0
)

system_prompt = """
You are the oracle, the great AI decision maker.
Given the user's query you must decide what to do with it based on the
list of tools provided to you.
 
If you see that a tool has been used (in the scratchpad) with a particular
query, do NOT use that same tool with the same query again. Also, do NOT use
any tool more than twice (ie, if the tool appears in the scratchpad twice, do
not use it again).
 
You should aim to collect information from a diverse range of sources before
providing the answer to the user. Once you have collected plenty of information
to answer the user's question (stored in the scratchpad) use the final_report_tool
to compile a report for the user.

TOOLS AVAILABLE:

1. snowflake_tool
- Use when the query asks for **platform-specific product trends or metrics** (e.g. "most searched products on Amazon", "top keywords on Walmart in 2023").
- Always pass: query, platform, date_start, and date_end if provided or inferrable.
- This tool returns structured data and chart visuals from Similarweb data.

2. web_search_tool
- Use for **open-ended** or **general knowledge** queries (e.g. comparisons, news, customer sentiment, or outside-the-platform data).
- Use when no internal data source (like Snowflake) can answer the question fully.

3. image_generator_tool
- Use if the user would benefit from a **visual representation**, **diagram**, or **concept illustration** of the query.

4. final_report_tool
- Use this when you've gathered all necessary insights and want to compile a **structured stakeholder-facing report**.
- Fields: executive_summary, market_overview, internal_insights, quantitative_analysis, recommendations, sources

IMPORTANT:
- Always reply with a structured tool call in JSON.
- Do NOT write explanations or summaries unless using `final_report_tool`.
"""


prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    ("assistant", "scratchpad: {scratchpad}"),
])

tools = [
        snowflake_tool,
        web_search_tool,
        image_generator_tool,
        final_report_tool
    ]

def create_scratchpad(intermediate_steps: list[AgentAction]):
    research_steps = []
    for i, action in enumerate(intermediate_steps):
        if action.log != "TBD":
            research_steps.append(
                f"Tool: {action.tool}, input: {action.tool_input}\n"
                f"Output: {action.log}"
            )
    return "\n---\n".join(research_steps)

oracle = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x["chat_history"],
        "scratchpad": lambda x: create_scratchpad( intermediate_steps=x["intermediate_steps"])
    }
    | prompt
    | llm.bind_tools(tools, tool_choice="any")
)

def run_oracle(state: AgentState):
    print("run_oracle")
    print(f"intermediate_steps: {state['intermediate_steps']}")
    out = oracle.invoke(state)
    print("[DEBUG] TOOL CALLS:", out.tool_calls)

    if not out.tool_calls:
        print("[ERROR] No tool calls returned by LLM.")
        return {
            "intermediate_steps": [
                AgentAction(
                    tool="final_report_tool",
                    tool_input={
                        "executive_summary": "No valid tools were called.",
                        "market_overview": "",
                        "internal_insights": "",
                        "quantitative_analysis": "",
                        "recommendations": "",
                        "sources": ""
                    },
                    log="[AUTOFAIL] No tool calls returned"
                )
            ]
        }

    tool_name = out.tool_calls[0]["name"]
    tool_args = out.tool_calls[0]["args"]
    action_out = AgentAction(
        tool=tool_name,
        tool_input=tool_args,
        log="TBD"
    )
    return {
        "intermediate_steps": [action_out]
    }

def router(state: AgentState):
    # If final_report_tool has been called, route to END so that it is not re‑invoked.
    if any(action.tool == "final_report_tool" for action in state["intermediate_steps"]):
        return END
    # Otherwise, return the tool from the last AgentAction if available.
    if state["intermediate_steps"]:
        return state["intermediate_steps"][-1].tool
    else:
        return "web_search_tool"
    
tool_str_to_func = {
    "snowflake_tool": snowflake_tool,
    "web_search_tool": web_search_tool,
    "image_generator_tool": image_generator_tool,
    "final_report_tool": final_report_tool
}

def run_tool(state: list):
    tool_name = state["intermediate_steps"][-1].tool
    tool_args = state["intermediate_steps"][-1].tool_input

    if tool_name == "final_report_tool" and isinstance(tool_args, dict):
        for step in state["intermediate_steps"]:
            if step.tool == "snowflake_tool" and "data:image/png;base64" in step.log:
                chart_html = f'<img src="{step.log}" alt="Chart">'
                tool_args["quantitative_analysis"] += f"\n\n{chart_html}"
                break

    print(f"{tool_name}.invoke(input={tool_args})")

    out = tool_str_to_func[tool_name].invoke(input=tool_args)
    action_out = AgentAction(
        tool=tool_name,
        tool_input=tool_args,
        log=str(out)
    )
    return {"intermediate_steps": [action_out]}

# Define the graph
graph = StateGraph(AgentState)

graph.add_node("oracle", run_oracle)
graph.add_node("snowflake_tool", run_tool)
graph.add_node("web_search_tool", run_tool)
graph.add_node("image_generator_tool", run_tool)
graph.add_node("final_report_tool", run_tool)
graph.add_node("refine_report_tool", run_tool)

graph.set_entry_point("oracle")

graph.add_conditional_edges(
    source="oracle",  # where in graph to start
    path=router,  # function to determine which node is called
)

# create edges from each tool back to the oracle
for tool_obj in tools:
    if tool_obj.name != "final_report_tool":
        graph.add_edge(tool_obj.name, "oracle")

# if anything goes to final answer, it must then move to END
graph.add_edge("final_report_tool", END)

# runnable = graph.compile()