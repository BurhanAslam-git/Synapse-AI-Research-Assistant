# ============================================================
# state.py — The Shared Memory Between All Agents
# ============================================================

# IMPORT SECTION
# "from X import Y" means: go to library X and bring in tool Y

from typing import TypedDict, Annotated, List, Optional
# TypedDict  = lets us create a dictionary with strict types
# Annotated  = lets us add special instructions to a field
# List       = means this field holds a list of items
# Optional   = means this field can be empty (None) sometimes

from langchain_core.messages import BaseMessage
# BaseMessage = the standard format LangChain uses for messages
# Every chat message (user or AI) follows this format

from langgraph.graph.message import add_messages
# add_messages = special instruction that tells LangGraph:
#                "keep adding to this list, don't overwrite it"


# ============================================================
# THE STATE CLASS — Our Shared Whiteboard
# ============================================================

class ResearchState(TypedDict):
    # This class defines ALL the information that gets
    # shared between our 4 agents
    # Think of each line as one "drawer" in the filing cabinet

    # --- USER INPUT ---
    user_query: str
    # What the user typed
    # Example: "Tell me about Tesla's recent news"
    # str = string = text

    # --- CONVERSATION HISTORY ---
    messages: Annotated[List[BaseMessage], add_messages]
    # The full conversation — every message ever sent
    # Annotated means we're adding special instructions
    # List[BaseMessage] means: a list of chat messages
    # add_messages means: keep adding, never overwrite
    # This is what makes follow-up questions work!

    # --- CLARITY AGENT OUTPUT ---
    clarity_status: Optional[str]
    # What Clarity Agent decided about the query
    # Either: "clear" or "needs_clarification"
    # Optional means it starts as None (empty) at first

    clarification_request: Optional[str]
    # If query is unclear, what question should we ask user?
    # Example: "Which company are you referring to?"
    # Optional because we only need this when unclear

    # --- RESEARCH AGENT OUTPUT ---
    research_data: Optional[str]
    # The raw research findings from Tavily search
    # Example: "Tesla reported record profits in Q4..."
    # Optional because it starts empty

    confidence_score: Optional[float]
    # How confident is the Research Agent in its findings?
    # Scale: 0.0 to 10.0
    # float = decimal number (like 7.5, 8.0, 5.3)
    # Optional because it starts empty

    # --- VALIDATOR AGENT OUTPUT ---
    validation_result: Optional[str]
    # What Validator Agent decided about research quality
    # Either: "sufficient" or "insufficient"
    # Optional because it starts empty

    # --- LOOP CONTROL ---
    research_attempts: int
    # How many times has Research Agent tried?
    # Starts at 0, goes up by 1 each attempt
    # We stop at 3 to prevent infinite loops
    # int = integer = whole number (0, 1, 2, 3)

    # --- SYNTHESIS AGENT OUTPUT ---
    final_answer: Optional[str]
    # The final clean answer written for the user
    # This is what gets displayed in the UI
    # Optional because it starts empty