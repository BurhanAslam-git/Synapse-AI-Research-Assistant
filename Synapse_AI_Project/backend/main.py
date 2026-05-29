# ============================================================
# backend/main.py — FastAPI Backend Server
# ============================================================
# This file is the bridge between React and LangGraph.
# It receives HTTP requests from React, calls your existing
# graph.py, and sends back JSON responses.
#
# Run it with:  uvicorn backend.main:app --reload --port 8000
# ============================================================

import sys
import os
import uuid

# ── Tell Python where to find your existing files ───────────
# FastAPI runs from a different location than Streamlit did
# This line adds your root project folder to Python's search path
# so "from graph import create_graph" works correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── FastAPI imports ──────────────────────────────────────────
from fastapi import FastAPI
# FastAPI = the main class that creates our API server

from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware = security setting that allows React (localhost:3000)
# to talk to FastAPI (localhost:8000)
# Browsers BLOCK requests between different ports by default
# This middleware says "it's okay, I trust localhost:3000"

from pydantic import BaseModel
# BaseModel = lets us define exactly what shape of data
# we expect to receive in each request
# If React sends wrong data, FastAPI rejects it automatically

# ── Your existing LangGraph imports ─────────────────────────
from graph import create_graph
# This is the EXACT same import your Streamlit app uses
# Nothing changes in graph.py — we just import it here instead

from langchain_core.messages import HumanMessage
from langgraph.types import Command
# Command(resume=...) is how we resume a paused graph
# Your Streamlit already uses this — we copy it here


# ============================================================
# CREATE THE APP
# ============================================================

app = FastAPI(
    title="Synapse AI Research Assistant API",
    description="Multi-agent research assistant powered by LangGraph",
    version="1.0.0"
)
# This creates the FastAPI application
# title/description/version show up in auto-generated API docs
# Visit http://localhost:8000/docs to see them — FastAPI
# generates a beautiful interactive docs page automatically


# ============================================================
# CORS SETTINGS
# ============================================================
# This is the permission slip that lets React talk to FastAPI
# Without this, your browser will block ALL requests from React

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    # Only allow requests from React's address
    # In production you would put your real domain here

    allow_credentials=True,
    allow_methods=["*"],
    # Allow GET, POST, PUT, DELETE — all HTTP methods

    allow_headers=["*"],
    # Allow all headers in requests
)


# ============================================================
# CREATE THE GRAPH — ONCE, AT STARTUP
# ============================================================
# We create the graph ONE TIME when the server starts
# This is exactly what Streamlit did with st.session_state.graph
# We store it in a plain Python dict called "sessions"
# Key = thread_id (unique per conversation)
# Value = not needed — graph handles its own memory via MemorySaver

graph = create_graph()
# One single graph instance
# MemorySaver inside graph.py remembers ALL conversations
# by thread_id — so one graph handles many users correctly


# ============================================================
# REQUEST MODELS
# ============================================================
# These classes define what data React must send in each request
# Pydantic checks this automatically — wrong data = error response

class QueryRequest(BaseModel):
    query: str
    # The user's question, e.g. "Tell me about Tesla"
    thread_id: str
    # Unique ID for this conversation
    # React generates this with uuid and sends it every time

class ClarifyRequest(BaseModel):
    answer: str
    # The user's clarification, e.g. "I meant Tesla the car company"
    thread_id: str
    # Same thread_id as before — so graph knows which conversation to resume

class ResetRequest(BaseModel):
    thread_id: str
    # The old thread_id that we are replacing


# ============================================================
# HELPER FUNCTION: detect_interrupt
# ============================================================
# This is copied directly from your streamlit_app.py
# It reads the graph state and checks if the workflow paused

def detect_interrupt(thread_id: str):
    """
    Checks if the graph is currently paused at an interrupt.

    Returns:
        (True, "clarification question text") if paused
        (False, "") if not paused
    """
    config = {"configurable": {"thread_id": thread_id}}
    current_state = graph.get_state(config)

    # current_state.tasks contains pending work
    # If a task has .interrupts, the graph is paused
    if current_state.tasks:
        for task in current_state.tasks:
            if hasattr(task, 'interrupts') and task.interrupts:
                for interrupt_item in task.interrupts:
                    question = str(interrupt_item.value)
                    return True, question

    return False, ""


# ============================================================
# ENDPOINT 1: POST /query
# ============================================================
# React calls this when user sends a NEW question

@app.post("/query")
async def run_query(request: QueryRequest):
    """
    Starts a fresh LangGraph workflow with the user's query.

    React sends:  { "query": "Tell me about Tesla", "thread_id": "abc-123" }

    FastAPI returns one of two things:
    A) Normal completion:
       { "status": "complete", "answer": "Tesla reported..." }

    B) Interrupt (needs clarification):
       { "status": "needs_clarification", "question": "Which company?" }
    """

    # Build the config — this is how LangGraph tracks which
    # conversation we are in. Same pattern as your Streamlit app.
    config = {"configurable": {"thread_id": request.thread_id}}

    # Append this turn to conversation history (add_messages reducer in state.py).
    # Prior messages stay in the checkpointer for the same thread_id.
    initial_state = {
        "user_query": request.query,
        "messages": [HumanMessage(content=request.query)],
        "research_attempts": 0,
        "clarity_status": None,
        "clarification_request": None,
        "research_data": None,
        "confidence_score": None,
        "validation_result": None,
        "final_answer": None,
    }

    try:
        # Run the graph — stream() yields state updates as each
        # agent completes. We iterate through all of them.
        # stream_mode="values" means each event is the FULL state,
        # not just the changes — same as your Streamlit app.

        final_answer = None

        for event in graph.stream(initial_state, config, stream_mode="values"):
            # Each event is the full state after a node runs
            # We only care about the final_answer field
            if event.get("final_answer"):
                final_answer = event["final_answer"]

        # After streaming finishes, check two things:

        # Case 1: We got a final answer — workflow completed normally
        if final_answer:
            return {
                "status": "complete",
                "answer": final_answer,
                "confidence_score": None  # optional extra info
            }

        # Case 2: No final answer — check if graph paused at interrupt
        interrupted, question = detect_interrupt(request.thread_id)

        if interrupted:
            return {
                "status": "needs_clarification",
                "question": question
            }

        # Case 3: Something unexpected — return error
        return {
            "status": "error",
            "message": "Workflow completed without a final answer"
        }

    except Exception as e:
        # If anything crashes, send a clean error to React
        # React will show this to the user
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# ENDPOINT 2: POST /clarify
# ============================================================
# React calls this when user answers the clarification question

@app.post("/clarify")
async def resume_with_clarification(request: ClarifyRequest):
    """
    Resumes a paused LangGraph workflow with the user's clarification.

    React sends:  { "answer": "Tesla the car company", "thread_id": "abc-123" }

    FastAPI returns:
       { "status": "complete", "answer": "Tesla reported..." }
    """

    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        final_answer = None

        # Command(resume=...) is the LangGraph way of saying
        # "here is the user's answer, please continue"
        # This is exactly what your Streamlit does already
        for event in graph.stream(
            Command(resume=request.answer),
            config,
            stream_mode="values"
        ):
            if event.get("final_answer"):
                final_answer = event["final_answer"]

        if final_answer:
            return {
                "status": "complete",
                "answer": final_answer
            }

        # Check for another interrupt (edge case: double clarification)
        interrupted, question = detect_interrupt(request.thread_id)
        if interrupted:
            return {
                "status": "needs_clarification",
                "question": question
            }

        return {
            "status": "error",
            "message": "Could not resume workflow"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# ENDPOINT 3: POST /reset
# ============================================================
# React calls this when user clicks "New Conversation"

@app.post("/reset")
async def reset_conversation(request: ResetRequest):
    """
    Generates a new thread_id for a fresh conversation.

    React sends:  { "thread_id": "old-abc-123" }

    FastAPI returns:
       { "status": "reset", "new_thread_id": "new-xyz-456" }
    """
    new_thread_id = str(uuid.uuid4())
    # Generate a brand new unique ID
    # The old thread_id just gets abandoned — MemorySaver keeps
    # it in memory but it is never used again

    return {
        "status": "reset",
        "new_thread_id": new_thread_id
    }


# ============================================================
# ENDPOINT 4: GET /health
# ============================================================
# Simple check — lets React confirm the backend is running

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Synapse AI Backend is running"}