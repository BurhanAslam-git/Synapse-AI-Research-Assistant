# Synapse AI Research Assistant

A multi-agent AI research assistant built with LangGraph, FastAPI, and React.
Features 4 specialized agents, human-in-the-loop clarification, and multi-turn
conversation memory to research any business in real time.

## Features
- 4 specialized agents: Clarity, Research, Validator, Synthesis
- Human-in-the-loop interrupt for ambiguous queries
- Multi-turn conversation with full context awareness
- Live web search via Tavily
- Confidence scoring + automatic retry logic

## Tech Stack
- Backend: FastAPI + LangGraph + Tavily
- Frontend: React (Sidebar, ChatWindow, AgentStatus, ClarificationModal)
- LLM: OpenAI GPT

## How to Run

### Backend
cd Synapse_AI_Project
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

### Frontend
cd frontend
npm install
npm start

## Environment Variables
Create a .env file in the root folder:
OPENAI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
