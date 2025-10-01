import os
import operator
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.tools import StructuredTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# --- 1. Define Database Engines ---
db_user_engine = create_engine("sqlite:///data/users.db")
db_task_engine = create_engine("sqlite:///data/tasks.db")


# --- 2. Define Smart Tools ---

def find_tasks_by_user(user_name: str) -> str:
    """Finds tasks assigned to a specific user by their name."""
    user_query = text("SELECT user_id FROM users WHERE LOWER(name) = LOWER(:name)")
    task_query = text("SELECT title, status FROM tasks WHERE assigned_to = :user_id")
    
    with db_user_engine.connect() as conn_user:
        user_result = conn_user.execute(user_query, {"name": user_name}).fetchone()
        if not user_result:
            return f"User '{user_name}' not found."
        user_id = user_result[0]

    with db_task_engine.connect() as conn_task:
        task_results = conn_task.execute(task_query, {"user_id": user_id}).fetchall()
        if not task_results:
            return f"No tasks found for user '{user_name}'."
        
        
        task_list = []
        for row in task_results:
            task_list.append(f"- {row[0]} (Status: {row[1]})")
        
        return f"Tasks for {user_name}:\n" + "\n".join(task_list)

def find_users_by_team(team_name: str) -> str:
    """Finds users who are part of a specific team."""
    query = text("SELECT name, email FROM users WHERE team = :team_name COLLATE NOCASE")
    with db_user_engine.connect() as connection:
        results = connection.execute(query, {"team_name": team_name}).fetchall()
        if not results:
            return f"No users found in team '{team_name}'."
        
        # Format the results as a readable string
        user_list = []
        for row in results:
            user_list.append(f"- {row[0]} ({row[1]})")
        
        return f"Users in {team_name} team:\n" + "\n".join(user_list)

def execute_modification_query(query: str, db_name: str) -> str:
    """Executes a data modification SQL query (INSERT, UPDATE, DELETE) on the specified database."""
    print(f"DEBUG: execute_modification_query called with query: {query}")
    print(f"DEBUG: Database: {db_name}")
    try:
        engine = db_user_engine if db_name == "users" else db_task_engine
        print(f"DEBUG: Using engine: {engine}")
        with engine.connect() as connection:
            trans = connection.begin()
            result = connection.execute(text(query))
            trans.commit()
            print(f"DEBUG: Query executed successfully, result: {result}")
            return "Query executed successfully."
    except Exception as e:
        print(f"DEBUG: Error executing query: {e}")
        return f"Error executing query: {e}"

class ModifyQueryInput(BaseModel):
    query: str = Field(description="The INSERT, UPDATE, or DELETE SQL query to execute.")
    db_name: str = Field(description="The database to run the query on, either 'users' or 'tasks'.")

tools = [
    StructuredTool.from_function(find_tasks_by_user),
    StructuredTool.from_function(find_users_by_team),
    StructuredTool.from_function(
        func=execute_modification_query,
        name="DataModificationTool",
        description="""Use this tool for any data modification (INSERT, UPDATE, DELETE) on the users or tasks database.

IMPORTANT DATABASE SCHEMA:
- Tasks table: task_id (INTEGER PRIMARY KEY), title (TEXT), description (TEXT), status (TEXT), assigned_to (INTEGER - user_id)
- Users table: user_id (INTEGER PRIMARY KEY), name (TEXT), email (TEXT), team (TEXT)

When creating tasks:
- Use 'title' column, not 'task_name'
- Use user_id for assigned_to, not the user's name
- Example: INSERT INTO tasks (title, assigned_to) VALUES ('Task Name', 1)

When assigning to users, first find their user_id:
- Alice = user_id 1, Bob = user_id 2, Charlie = user_id 3, etc.""",
        args_schema=ModifyQueryInput
    ),
]
tool_executor = ToolExecutor(tools)


# --- 3. Define Agent State and Model ---

class AgentState(TypedDict):
    input: str
    original_input: str
    chat_history: list[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
    pending_action: dict
    last_tool_name: str

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# --- 4. Define Graph Nodes ---

def get_agent_outcome(state: AgentState):
    """Determines the next action and saves the original input."""
    print(f"DEBUG: get_agent_outcome called with input: '{state['input']}'")
    
    # Check if this is a confirmation response
    user_input = state["input"].strip().lower()
    if user_input in ["yes", "y", "ok", "okay", "sure", "proceed"]:
        # This is a confirmation, we should route to confirmation_handler
        # But we need to make sure the pending_action is preserved
        if "pending_action" in state:
            print("DEBUG: Confirmation detected, routing to confirmation_handler")
            return {"agent_outcome": "confirmation_yes"}
        else:
            print("DEBUG: Confirmation detected but no pending action")
            return {"agent_outcome": AgentFinish(return_values={"output": "I don't have a pending action to confirm. Please start a new request."}, log="No pending action")}
    elif user_input in ["no", "n", "cancel", "stop"]:
        print("DEBUG: Cancellation detected")
        return {"agent_outcome": AgentFinish(return_values={"output": "Action cancelled."}, log="Action cancelled.")}
    else:
        # Regular input, process normally
        print(f"DEBUG: Processing regular input with LLM: '{state['input']}'")
        response = llm_with_tools.invoke(state["input"])
        print(f"DEBUG: LLM response: {response}")
        
        if response.tool_calls:
            print(f"DEBUG: LLM wants to call tool: {response.tool_calls[0]}")
            return {"agent_outcome": response.tool_calls[0], "original_input": state["input"]}
        else:
            print(f"DEBUG: LLM gave direct response: {response.content}")
            return {"agent_outcome": AgentFinish(return_values={"output": response.content}, log=response.content)}

def execute_tool(state: AgentState):
    tool_call = state["agent_outcome"]
    print(f"DEBUG: execute_tool called with tool_call: {tool_call}")
    action = AgentAction(tool=tool_call['name'], tool_input=tool_call['args'], log="")
    print(f"DEBUG: Executing action: {action}")
    result = tool_executor.invoke(action)
    print(f"DEBUG: Tool execution result: {result}")
    return {"intermediate_steps": [(action, str(result))], "last_tool_name": tool_call['name']}

def generate_final_response(state: AgentState):
    """Generates a friendly success message after a CUD action."""
    response_prompt = f"""
    The user's original request was: "{state['original_input']}"
    This action was just performed successfully.
    Please generate a short, friendly confirmation message for the user that acknowledges their original request was completed.
    """
    response = llm.invoke(response_prompt)
    return {"agent_outcome": AgentFinish(return_values={"output": response.content}, log=response.content)}

def generate_read_response(state: AgentState):
    """Generates a response for read operations (like finding tasks)."""
    if state.get("intermediate_steps"):
        last_result = state["intermediate_steps"][-1][1]
        print(f"DEBUG: generate_read_response called with result: {last_result}")
        return {"agent_outcome": AgentFinish(return_values={"output": last_result}, log=last_result)}
    else:
        return {"agent_outcome": AgentFinish(return_values={"output": "No results found."}, log="No results")}

def generate_confirmation_prompt(state: AgentState):
    """Generates the confirmation prompt and saves the pending action."""
    tool_call = state["agent_outcome"]
    query = tool_call['args']['query']
    print(f"DEBUG: generate_confirmation_prompt - SQL query: {query}")
    print(f"DEBUG: generate_confirmation_prompt - tool_call: {tool_call}")
    
    summary_prompt = f"""
    The user's request was: "{state['input']}"
    This has been translated into the following SQL query: `{query}`.
    Please generate a concise, one-sentence summary in plain English explaining what this query will do.
    """
    summary = llm.invoke(summary_prompt).content
    print(f"DEBUG: generate_confirmation_prompt - summary: {summary}")
    
    pending_action = {
        "summary": summary,
        "tool_call": tool_call,
        "original_input": state["original_input"]
    }
    return {"pending_action": pending_action}

# --- 5. Define Conditional Edges ---

def should_continue(state: AgentState):
    """Determines the routing logic."""
    outcome = state["agent_outcome"]
    print(f"DEBUG: should_continue called with outcome: {outcome}")
    
    if isinstance(outcome, AgentFinish):
        print("DEBUG: Routing to END (AgentFinish)")
        return END
    
    if outcome == "confirmation_yes":
        print("DEBUG: Routing to confirmation_handler")
        return "confirmation_handler"
    
    tool_name = outcome['name']
    print(f"DEBUG: Tool name: {tool_name}")
    if "find" in tool_name:
        print("DEBUG: Routing to execute_tool (find operation)")
        return "execute_tool"
    else:
        print("DEBUG: Routing to ask_for_confirmation (modification operation)")
        return "ask_for_confirmation"

def handle_user_confirmation(state: AgentState):
    """Handles the user's 'yes' or 'no' and restores the necessary context."""
    print(f"DEBUG: handle_user_confirmation called with state: {state}")
    
    if "pending_action" in state and state["pending_action"]:
        print(f"DEBUG: Restoring pending action: {state['pending_action']}")
        return {
            "agent_outcome": state["pending_action"]["tool_call"],
            "original_input": state["pending_action"]["original_input"]
        }
    else:
        print("DEBUG: No pending action found")
        return {"agent_outcome": AgentFinish(return_values={"output": "I don't have a pending action to confirm. Please start a new request."}, log="No pending action")}

# --- 6. Build the Graph ---

workflow = StateGraph(AgentState)
workflow.add_node("agent", get_agent_outcome)
workflow.add_node("tool_executor", execute_tool)
workflow.add_node("ask_for_confirmation", generate_confirmation_prompt)
workflow.add_node("final_response_generator", generate_final_response)
workflow.add_node("read_response_generator", generate_read_response)
workflow.add_node("confirmation_handler", handle_user_confirmation)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"execute_tool": "tool_executor", "ask_for_confirmation": "ask_for_confirmation", "confirmation_handler": "confirmation_handler", END: END})
workflow.add_conditional_edges("tool_executor", lambda state: "read_response_generator" if "find" in state.get("last_tool_name", "") else "final_response_generator", {"read_response_generator": "read_response_generator", "final_response_generator": "final_response_generator"})
workflow.add_edge("ask_for_confirmation", "confirmation_handler")
workflow.add_conditional_edges("confirmation_handler", lambda state: "tool_executor" if not isinstance(state["agent_outcome"], AgentFinish) else END, {"tool_executor": "tool_executor", END: END})
workflow.add_edge("final_response_generator", END)
workflow.add_edge("read_response_generator", END)


memory = MemorySaver()
agent_graph = workflow.compile(interrupt_after=["ask_for_confirmation"], checkpointer=memory)