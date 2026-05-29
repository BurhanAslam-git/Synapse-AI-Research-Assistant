# ============================================================
# agents/synthesis_agent.py — Agent 4: Final Answer Writer
# ============================================================
# This is the LAST agent in our workflow.
# It takes all the research data collected and writes
# a clean, structured, professional answer for the user.
#
# It also has access to conversation history so it can
# handle follow-up questions intelligently.
# ============================================================

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# SETTING UP THE AI BRAIN
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3
    # Slightly higher temperature than other agents
    # because we want natural, readable writing
    # not robotic responses
)


# ============================================================
# SYSTEM PROMPT — Job Description for Synthesis Agent
# ============================================================

SYNTHESIS_SYSTEM_PROMPT = """You are an expert business research report writer.

Your job is to take raw research data and write a clear, 
professional, well-structured response for the user.

Guidelines:
- Write in a clear, professional but friendly tone
- Structure your response with clear sections
- Use emojis for section headers to make it readable
- Include specific facts, numbers, and dates when available
- Keep it comprehensive but not overwhelming
- If the research data is limited, be honest about it
- Always consider the conversation history for context
- For follow-up questions, reference previous context naturally

Structure your response like this:
📊 [Company Name] — Research Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 Recent News & Developments
[key news points]

💰 Financial Overview  
[financial data if available]

👤 Leadership & Strategy
[leadership info if available]

📈 Key Highlights
[most important points]

💡 Summary
[2-3 sentence overall summary]

If some sections have no data, skip them gracefully.
Adapt the structure based on what was actually asked.
"""


# ============================================================
# THE MAIN SYNTHESIS FUNCTION
# ============================================================

def synthesis_agent(state: dict) -> dict:
    """
    Synthesis Agent — the final step in our workflow.
    
    Takes research data from state,
    considers conversation history,
    writes a clean professional answer.
    
    Args:
        state: Shared state dictionary from LangGraph
        
    Returns:
        Updated state with final_answer filled in
    """

    # Read everything we need from shared state
    user_query = state["user_query"]
    research_data = state.get("research_data", "")
    confidence_score = state.get("confidence_score", 0)
    messages = state.get("messages", [])

    print(f"\n[Synthesis Agent] Writing final answer...")
    print(f"[Synthesis Agent] Query: '{user_query}'")
    print(f"[Synthesis Agent] Research confidence: {confidence_score}/10")
    print(f"[Synthesis Agent] Conversation history: {len(messages)} messages")

    # --------------------------------------------------------
    # BUILD CONVERSATION HISTORY CONTEXT
    # --------------------------------------------------------
    # Convert previous messages into readable text
    # so GPT-4 understands what was discussed before
    
    conversation_context = ""
    if messages:
        conversation_context = "\n\nPrevious conversation:\n"
        for msg in messages[-6:]:
            # Only use last 6 messages to keep context manageable
            # [-6:] means "last 6 items from the list"
            if isinstance(msg, HumanMessage):
                conversation_context += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                conversation_context += f"Assistant: {msg.content}\n"

    # --------------------------------------------------------
    # BUILD THE FINAL PROMPT
    # --------------------------------------------------------

    synthesis_prompt = f"""
Please write a comprehensive, well-structured response for the user.

User's Question: {user_query}

Research Data Collected:
{research_data if research_data else "Limited research data available."}

Research Confidence Score: {confidence_score}/10
{conversation_context}

Write a professional, clear response following the structure 
in your instructions. Be specific and use actual data from 
the research. If confidence is low, acknowledge limitations.
"""

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYNTHESIS_SYSTEM_PROMPT),
        ("human", synthesis_prompt)
    ])

    # Create chain and run it
    output_parser = StrOutputParser()
    synthesis_chain = prompt | llm | output_parser

    print(f"[Synthesis Agent] Generating response with GPT-4...")

    # Generate the final answer
    final_answer = synthesis_chain.invoke({})

    print(f"[Synthesis Agent] Answer generated! Length: {len(final_answer)} characters")
    print(f"[Synthesis Agent] ✅ Workflow complete!")

    # --------------------------------------------------------
    # UPDATE CONVERSATION HISTORY
    # --------------------------------------------------------
    # Add this interaction to messages so future
    # follow-up questions have context

    new_messages = [
        HumanMessage(content=user_query),
        AIMessage(content=final_answer)
    ]

    # Return final state with answer and updated messages
    return {
        "final_answer": final_answer,
        "messages": new_messages
    }


# ============================================================
# TEST BLOCK
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("Testing Synthesis Agent")
    print("=" * 50)

    # Test 1 — Fresh query with good research data
    print("\nTest 1: Fresh query")
    result1 = synthesis_agent({
        "user_query": "Tell me about Tesla's recent developments",
        "research_data": """
        Tesla Q1 2025 revenue: $21.3 billion (up 8% YoY)
        Stock price: $390.82 (+2.41% today)
        CEO Elon Musk announced Cybercab production in Texas
        Tesla gained Dutch regulatory approval for self-driving features
        New partnership with SpaceX for satellite connectivity in vehicles
        Optimus humanoid robot entering limited production
        Gigafactory India planned for 2026
        Vehicle deliveries: 450,000 units this quarter
        """,
        "confidence_score": 8.5,
        "messages": []
    })

    print("\n" + "=" * 50)
    print("FINAL ANSWER:")
    print("=" * 50)
    print(result1["final_answer"])

    # Test 2 — Follow-up question with conversation history
    print("\n" + "=" * 50)
    print("Test 2: Follow-up question with history")
    print("=" * 50)

    result2 = synthesis_agent({
        "user_query": "What about their CEO?",
        "research_data": """
        Elon Musk - CEO of Tesla since 2008
        Also CEO of SpaceX, X (Twitter), and xAI
        Recently focused on Optimus robot and autonomous driving
        Net worth approximately $200 billion
        """,
        "confidence_score": 7.0,
        "messages": [
            HumanMessage(content="Tell me about Tesla"),
            AIMessage(content="Tesla is a leading EV company with $21.3B revenue...")
        ]
    })

    print("\nFINAL ANSWER (Follow-up):")
    print(result2["final_answer"])