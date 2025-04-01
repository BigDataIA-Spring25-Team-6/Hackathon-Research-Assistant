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
        time.sleep(60)
        final_output = generate_structured_summary_from_logs(result)
        return {"query": query, "result": final_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invoking multiagent system: {str(e)}")

    # try:
    #     result = runnable.invoke(state)
    #     max_retries = 2  # Total attempts = initial + 2 retries
    #     retry_delay = 5  # Seconds between attempts
    #     final_output = None
    #     for attempt in range(max_retries + 1):
    #         try:
    #             final_output = generate_structured_summary_from_logs(result)
    #             break
    #         except Exception as e:
    #             if attempt == max_retries:
    #                 raise
    #             time.sleep(retry_delay)
    #             continue
    #     return {"query": query, "result": final_output}
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Failed after {max_retries} retries: {str(e)}"
    #     )    
		