# ============================================================
# graph.py — The Master Workflow Controller
# ============================================================
# This file connects all 4 agents together into one
# complete working workflow using LangGraph.
#
# It defines:
# - Which agents run (nodes)
# - In what order (edges)
# - Under what conditions (conditional edges)
# - When to pause for human input (interrupt)
# ============================================================

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from state import ResearchState
from agents.clarity_agent import clarity_agent
from agents.research_agent import research_agent
from agents.validator_agent import validator_agent
from agents.synthesis_agent import synthesis_agent


# ============================================================
# STEP 1: ROUTING FUNCTIONS
# These functions read the state and decide where to go next
# ============================================================

def route_after_clarity(state: ResearchState) -> str:
    """
    Called after Clarity Agent runs.
    Reads clarity_status from state and decides next step.
    
    Returns:
        "interrupt_node" if query needs clarification
        "research" if query is clear enough to research
    """
    clarity_status = state.get("clarity_status", "clear")
    
    if clarity_status == "needs_clarification":
        print(f"[Router] Clarity: needs clarification → interrupting")
        return "interrupt_node"
    else:
        print(f"[Router] Clarity: clear → going to research")
        return "research"


def route_after_research(state: ResearchState) -> str:
    """
    Called after Research Agent runs.
    Reads confidence_score and decides next step.
    
    Returns:
        "synthesis" if confidence >= 6 (good enough)
        "validator" if confidence < 6 (needs checking)
    """
    confidence_score = state.get("confidence_score", 0)
    
    if confidence_score >= 6:
        print(f"[Router] Research confidence {confidence_score} >= 6 → going to synthesis")
        return "synthesis"
    else:
        print(f"[Router] Research confidence {confidence_score} < 6 → going to validator")
        return "validator"


def route_after_validation(state: ResearchState) -> str:
    """
    Called after Validator Agent runs.
    Reads validation_result and research_attempts.
    
    Returns:
        "research" if insufficient AND attempts < 3
        "synthesis" if sufficient OR max attempts reached
    """
    validation_result = state.get("validation_result", "sufficient")
    research_attempts = state.get("research_attempts", 0)
    
    if validation_result == "insufficient" and research_attempts < 3:
        print(f"[Router] Validation: insufficient, attempt {research_attempts} → retrying research")
        return "research"
    else:
        print(f"[Router] Validation: {validation_result}, attempts: {research_attempts} → going to synthesis")
        return "synthesis"


# ============================================================
# STEP 2: SPECIAL INTERRUPT NODE
# This node pauses workflow and asks user for clarification
# ============================================================

def interrupt_node(state: ResearchState) -> ResearchState:
    """
    Special node that pauses the workflow.
    
    When Clarity Agent says query is unclear:
    1. This node runs
    2. Workflow PAUSES completely
    3. UI shows clarification question to user
    4. User types their answer
    5. Workflow RESUMES with updated query
    """
    
    # Get the clarification question from Clarity Agent
    clarification_question = state.get(
        "clarification_request",
        "Could you please be more specific about your query?"
    )
    
    print(f"[Interrupt Node] Pausing workflow...")
    print(f"[Interrupt Node] Asking user: {clarification_question}")
    
    # THIS LINE PAUSES THE ENTIRE WORKFLOW
    # The value passed shows as the interrupt value
    # The workflow waits here until resumed
    user_clarification = interrupt(clarification_question)
    
    print(f"[Interrupt Node] User responded: {user_clarification}")
    
    # Update the query with user's clarification
    # Now research will use this clearer query
    return {
        "user_query": user_clarification,
        "clarity_status": "clear"
    }


# ============================================================
# STEP 3: BUILD THE GRAPH
# ============================================================

def create_graph():
    """
    Creates and returns the complete LangGraph workflow.
    
    This function:
    1. Creates a StateGraph with our ResearchState
    2. Adds all 4 agents as nodes
    3. Adds the interrupt node
    4. Connects everything with edges
    5. Compiles with memory for Human-in-the-Loop
    
    Returns:
        Compiled LangGraph workflow ready to run
    """
    
    print("[Graph] Building workflow graph...")
    
    # Create a new StateGraph using our state schema
    # ResearchState is the shared whiteboard blueprint
    workflow = StateGraph(ResearchState)
    
    # ----------------------------------------------------------
    # ADD NODES (Add each agent as a stop in the workflow)
    # ----------------------------------------------------------
    
    # Each add_node call registers a function as a workflow stop
    # First arg = name of node (used in routing)
    # Second arg = the function to run at this node
    
    workflow.add_node("clarity", clarity_agent)
    workflow.add_node("interrupt_node", interrupt_node)
    workflow.add_node("research", research_agent)
    workflow.add_node("validator", validator_agent)
    workflow.add_node("synthesis", synthesis_agent)
    
    print("[Graph] Nodes added: clarity, interrupt, research, validator, synthesis")
    
    # ----------------------------------------------------------
    # ADD EDGES (Connect the nodes with paths)
    # ----------------------------------------------------------
    
    # START → clarity
    # The workflow always begins at the clarity node
    workflow.add_edge(START, "clarity")
    
    # clarity → ??? (conditional - depends on clarity_status)
    # Uses route_after_clarity function to decide
    workflow.add_conditional_edges(
        "clarity",
        route_after_clarity,
        {
            "interrupt_node": "interrupt_node",
            "research": "research"
        }
    )
    
    # interrupt_node → research
    # After user clarifies, always go to research
    workflow.add_edge("interrupt_node", "research")
    
    # research → ??? (conditional - depends on confidence_score)
    # Uses route_after_research function to decide
    workflow.add_conditional_edges(
        "research",
        route_after_research,
        {
            "synthesis": "synthesis",
            "validator": "validator"
        }
    )
    
    # validator → ??? (conditional - depends on validation_result)
    # Uses route_after_validation function to decide
    workflow.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "research": "research",
            "synthesis": "synthesis"
        }
    )
    
    # synthesis → END
    # After synthesis, workflow always ends
    workflow.add_edge("synthesis", END)
    
    print("[Graph] Edges connected successfully")
    
    # ----------------------------------------------------------
    # COMPILE THE GRAPH WITH MEMORY
    # ----------------------------------------------------------
    
    # MemorySaver enables Human-in-the-Loop
    # It saves the complete state when workflow pauses
    # so it can resume from exactly the same point
    checkpointer = MemorySaver()
    
    # Compile turns our blueprint into a runnable workflow
    # interrupt_before is no longer needed since we use
    # interrupt() function directly inside interrupt_node
    compiled_graph = workflow.compile(
        checkpointer=checkpointer
    )
    
    print("[Graph] ✅ Graph compiled successfully!")
    print("[Graph] Workflow ready to run!")
    
    return compiled_graph


# ============================================================
# STEP 4: QUICK TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Graph Creation")
    print("=" * 50)
    
    # Create the graph
    graph = create_graph()
    
    print("\nRunning a test query...")
    print("-" * 50)
    
    # Every conversation needs a unique thread_id
    # This is how LangGraph tracks different conversations
    config = {"configurable": {"thread_id": "test-001"}}
    
    # Initial state — starting values for the whiteboard
    initial_state = {
        "user_query": "Tell me about Apple's recent news",
        "messages": [],
        "research_attempts": 0,
        "clarity_status": None,
        "clarification_request": None,
        "research_data": None,
        "confidence_score": None,
        "validation_result": None,
        "final_answer": None
    }
    
    print(f"Query: {initial_state['user_query']}")
    print("-" * 50)
    
    # Run the complete workflow
    # stream() runs the graph and yields updates at each step
    for event in graph.stream(initial_state, config):
        # event is a dictionary showing what each node returned
        for node_name, node_output in event.items():
            print(f"\n[Graph] Node '{node_name}' completed")
            
            # Show the final answer when synthesis completes
            if node_name == "synthesis" and "final_answer" in node_output:
                print("\n" + "=" * 50)
                print("FINAL ANSWER FROM WORKFLOW:")
                print("=" * 50)
                print(node_output["final_answer"])