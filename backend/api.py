from fastapi import FastAPI
from pydantic import BaseModel
from backend.agent import agent_graph

app = FastAPI(
    title="Mini Agentic Bot API",
    description="An API for interacting with a project management agent.",
    version="1.0.0",
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.post("/chat", response_model=QueryResponse)
async def chat_with_agent(request: QueryRequest):
    """
    Sends a query to the agent and gets a response.
    NOTE: This stateless endpoint doesn't support the human-in-the-loop confirmation flow.
    It's designed for direct Read (SELECT) operations.
    A stateful implementation would be needed for CUD operations via API.
    """
    inputs = {"input": request.query, "chat_history": []}

    final_response = "This API endpoint is for demonstration. For the full interactive experience with confirmation, please use the Streamlit UI."

    try:
        response_generator = agent_graph.stream(inputs)
        for chunk in response_generator:
            if "__end__" not in chunk:
                current_state = list(chunk.values())[0]
                if "input" in current_state and isinstance(current_state["input"], str):
                    final_response = current_state["input"]
                    break
                if "proposed_action_summary" in current_state:
                     final_response = current_state["proposed_action_summary"] + " Confirmation required via UI."
                     break
    except Exception as e:
        final_response = f"An error occurred: {e}"

    return QueryResponse(response=final_response)