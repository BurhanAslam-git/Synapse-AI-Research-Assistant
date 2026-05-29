# ============================================================
# agents/research_agent.py — Agent 2: Company Research Agent
# ============================================================
# This agent searches the internet for company information.
# It uses Tavily search tool to find real-time data.
# After searching, it scores its own confidence (0-10).
# High confidence (>=6) → goes to Synthesis Agent
# Low confidence (<6)   → goes to Validator Agent
# ============================================================

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import sys
import os

# Add parent directory to path so we can import from tools/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.tavily_search import search_company_info

load_dotenv()


# ============================================================
# SETTING UP THE AI BRAIN WITH SEARCH TOOL ATTACHED
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1
    # Small temperature so research is focused
    # but slightly flexible for natural language
)

# Attach our Tavily search tool to the LLM
# Now GPT-4 can decide to search whenever it needs to
llm_with_tools = llm.bind_tools([search_company_info])


# ============================================================
# SYSTEM PROMPT — Job Description for Research Agent
# ============================================================

RESEARCH_SYSTEM_PROMPT = """You are an expert business research analyst.

Your job is to research companies thoroughly using the search tool available to you.

When given a company query:
1. Use the search_company_info tool to search for relevant information
2. Search for: recent news, financials, key developments, leadership
3. Analyze the search results carefully
4. Provide a comprehensive research summary

After your research, you MUST end your response with EXACTLY this format:
RESEARCH_SUMMARY: [your detailed findings here]
CONFIDENCE_SCORE: [a number from 0 to 10]

Confidence score guide:
- 8-10: Found comprehensive, detailed, recent information
- 6-7:  Found decent information, mostly complete
- 4-5:  Found some information but gaps exist
- 0-3:  Very little useful information found

Be thorough and search multiple aspects of the company.
"""


# ============================================================
# THE MAIN RESEARCH FUNCTION
# ============================================================

def research_agent(state: dict) -> dict:
    """
    Research Agent function called by LangGraph.
    
    Searches the internet for company information,
    evaluates the quality of findings,
    assigns a confidence score.
    
    Args:
        state: Shared state dictionary from LangGraph
        
    Returns:
        Updated state with research_data and confidence_score
    """

    # Read needed values from shared state
    user_query = state["user_query"]
    current_attempts = state.get("research_attempts", 0)

    # Increment attempt counter
    # This tracks how many times we've tried researching
    new_attempts = current_attempts + 1

    print(f"\n[Research Agent] Starting research attempt {new_attempts}")
    print(f"[Research Agent] Query: '{user_query}'")

    # --------------------------------------------------------
    # STEP 1: Let GPT-4 search using Tavily tool
    # --------------------------------------------------------

    # Build the message to send to GPT-4
    messages = [
        {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
        {"role": "user", "content": f"Please research this: {user_query}"}
    ]

    # Send to GPT-4 with tools attached
    # GPT-4 will automatically decide to call search_company_info
    print(f"[Research Agent] Sending to GPT-4 with search tool...")
    
    # First call — GPT-4 decides to use the tool
    ai_response = llm_with_tools.invoke(messages)
    
    # Check if GPT-4 wants to use any tools
    tool_results = ""
    if hasattr(ai_response, 'tool_calls') and ai_response.tool_calls:
        print(f"[Research Agent] GPT-4 is using search tool...")
        
        # Execute each tool call GPT-4 requested
        for tool_call in ai_response.tool_calls:
            search_query = tool_call['args'].get('query', user_query)
            print(f"[Research Agent] Searching for: '{search_query}'")
            
            # Actually run the Tavily search
            search_result = search_company_info.invoke(search_query)
            tool_results += f"\nSearch Results for '{search_query}':\n{search_result}\n"
    
    # --------------------------------------------------------
    # STEP 2: Send search results back to GPT-4 for analysis
    # --------------------------------------------------------

    # Now ask GPT-4 to analyze the search results
    # and produce a structured research summary
    analysis_prompt = f"""
    Original query: {user_query}
    
    Search results obtained:
    {tool_results if tool_results else "No tool results - use your training knowledge"}
    
    Please provide:
    1. A comprehensive research summary of the company
    2. Key findings from the search results
    3. Your confidence score (0-10) based on quality of information found
    
    End with EXACTLY:
    RESEARCH_SUMMARY: [detailed summary]
    CONFIDENCE_SCORE: [number 0-10]
    """

    final_messages = [
        {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
        {"role": "user", "content": analysis_prompt}
    ]

    # Get final analysis from GPT-4
    final_response = llm.invoke(final_messages)
    response_text = final_response.content

    print(f"[Research Agent] Research complete. Parsing results...")

    # --------------------------------------------------------
    # STEP 3: Parse the response to extract summary and score
    # --------------------------------------------------------

    research_data = ""
    confidence_score = 5.0  # Default score if parsing fails

    lines = response_text.strip().split("\n")

    # Find RESEARCH_SUMMARY and CONFIDENCE_SCORE in response
    summary_started = False
    summary_lines = []

    for line in lines:
        if line.startswith("RESEARCH_SUMMARY:"):
            summary_started = True
            # Get text after "RESEARCH_SUMMARY:"
            summary_text = line.replace("RESEARCH_SUMMARY:", "").strip()
            if summary_text:
                summary_lines.append(summary_text)

        elif line.startswith("CONFIDENCE_SCORE:"):
            summary_started = False
            # Extract the number after "CONFIDENCE_SCORE:"
            score_text = line.replace("CONFIDENCE_SCORE:", "").strip()
            try:
                # Convert text to float number
                confidence_score = float(score_text)
                # Make sure score is between 0 and 10
                confidence_score = max(0.0, min(10.0, confidence_score))
            except ValueError:
                # If conversion fails, use default
                confidence_score = 5.0

        elif summary_started:
            summary_lines.append(line)

    # Join all summary lines into one text block
    research_data = "\n".join(summary_lines).strip()

    # If parsing failed completely, use full response
    if not research_data:
        research_data = response_text

    print(f"[Research Agent] Confidence score: {confidence_score}/10")
    print(f"[Research Agent] Research data length: {len(research_data)} characters")

    # --------------------------------------------------------
    # STEP 4: Return updated state
    # --------------------------------------------------------

    return {
        "research_data": research_data,
        "confidence_score": confidence_score,
        "research_attempts": new_attempts
    }


# ============================================================
# TEST BLOCK
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("Testing Research Agent")
    print("=" * 50)

    test_state = {
        "user_query": "Tell me about Tesla's recent news and financials",
        "messages": [],
        "research_attempts": 0
    }

    result = research_agent(test_state)

    print("\n" + "=" * 50)
    print("RESEARCH RESULTS:")
    print("=" * 50)
    print(f"Confidence Score: {result['confidence_score']}/10")
    print(f"\nResearch Data:\n{result['research_data']}")