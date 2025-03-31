from langgraph.graph import StateGraph, END
from langchain_core.agents import AgentAction
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from mcp.client import MCPClient
import operator
from typing import TypedDict, Annotated

# Step 1: Define Agent State
class AgentState(TypedDict):
    input: str
    chat_history: list
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

# Step 2: Define MCP Client
mcp = MCPClient("http://localhost:8000")

# Step 3: Create OpenAI Agent that uses MCP tools
# llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm = ChatOllama(model="llama3", temperature=0)

system_prompt = """
You are a research assistant with access to external tools. 
Use the available tools to gather information and generate insightful reports.
Never use a tool more than once for the same input. Once enough information is collected, finalize your answer.

Available tools:
- snowflake_tool: Search retail keyword demand data from Snowflake
- web_search_tool: Pull current news and external data
- rag_tool: Search internal documentation or previous reports
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    ("assistant", "scratchpad: {scratchpad}")
])

# Step 4: Bind tools to LLM
oracle = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x["chat_history"],
        "scratchpad": lambda x: create_scratchpad(x["intermediate_steps"])
    }
    | prompt
    | llm.bind_tools(mcp.get_tools(), tool_choice="any")
)

# Utility: convert intermediate steps to readable format
def create_scratchpad(steps):
    return "\n---\n".join([
        f"Tool: {a.tool}, Input: {a.tool_input}\nOutput: {o}"
        for a, o in steps
    ])

# Step 5: Define run_oracle and run_tool nodes
def run_oracle(state):
    out = oracle.invoke(state)
    tool_name = out.tool_calls[0]["name"]
    tool_args = out.tool_calls[0]["args"]
    return {"intermediate_steps": [AgentAction(tool=tool_name, tool_input=tool_args, log="TBD")]}  # store call

def router(state):
    return state["intermediate_steps"][-1].tool

def run_tool(state):
    action = state["intermediate_steps"][-1]
    result = mcp.call_tool(tool=action.tool, input=action.tool_input)
    action_out = AgentAction(tool=action.tool, tool_input=action.tool_input, log=str(result))
    return {"intermediate_steps": [action_out]}

# Step 6: Build LangGraph

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("oracle", run_oracle)
    graph.add_node("snowflake_tool", run_tool)
    graph.add_node("web_search_tool", run_tool)
    # graph.add_node("rag_tool", run_tool)
    graph.add_node("final_answer", run_tool)

    graph.set_entry_point("oracle")
    graph.add_conditional_edges("oracle", router)

    for tool in ["snowflake_tool", "web_search_tool", "rag_tool"]:
        graph.add_edge(tool, "oracle")

    graph.add_edge("final_answer", END)
    return graph.compile()