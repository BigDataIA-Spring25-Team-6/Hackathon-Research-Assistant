from fastapi import FastAPI, HTTPException, Query
from langgraph_code.langgraph_flow import runnable
from utils.report_util import generate_structured_summary_from_logs
import time

# initialize the FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Report Generation API!"}

@app.post("/use-all-agents/")
async def use_all_agents(query: str):
    """
    Endpoint to use all agents combined via the multiagent graph.
    """
    state = {
        "input": query,
        "chat_history": [],
        "intermediate_steps": []
    }

    try:
        result = runnable.invoke(state)
        time.sleep(10)
        final_output = generate_structured_summary_from_logs(result)
        return {"query": query, "result": final_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invoking multiagent system: {str(e)}")
		