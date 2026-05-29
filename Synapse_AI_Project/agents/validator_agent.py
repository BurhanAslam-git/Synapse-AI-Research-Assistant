# ============================================================
# agents/validator_agent.py — Agent 3: Research Validator
# ============================================================
# This agent checks if the research data is good enough.
# It acts as a quality control checkpoint.
#
# Decision logic:
#   sufficient   → research is good → go to Synthesis Agent
#   insufficient → research is poor → go back to Research Agent
#                  BUT only if attempts < 3 (prevents infinite loop)
#   max attempts → force proceed to Synthesis regardless of quality
# ============================================================

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# SETTING UP THE AI BRAIN
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0
    # Zero temperature for consistent, reliable decisions
    # Validation must be deterministic not random
)


# ============================================================
# SYSTEM PROMPT — Job Description for Validator Agent
# ============================================================

VALIDATOR_SYSTEM_PROMPT = """You are a Research Quality Validator for a business research assistant.

Your job is to evaluate whether research data is sufficient to answer a user's query.

You will receive:
1. The original user query
2. The research data found
3. The confidence score given by the researcher

Evaluate the research based on:
- Is the company specifically mentioned and researched?
- Is there meaningful, relevant information present?
- Are there specific facts, numbers, or developments mentioned?
- Would a user be satisfied with this information?

Research is SUFFICIENT if:
- Contains specific information about the requested company
- Has at least some recent news or financial data
- Provides enough context to give a useful answer
- Confidence score is 5 or above

Research is INSUFFICIENT if:
- Very little or no relevant information found
- Information is too generic or off-topic
- Confidence score is below 4
- Research is completely empty or useless

You MUST respond in EXACTLY this format:
VALIDATION: sufficient
or
VALIDATION: insufficient
REASON: [brief explanation of your decision]
"""


# ============================================================
# THE MAIN VALIDATOR FUNCTION
# ============================================================

def validator_agent(state: dict) -> dict:
    """
    Validator Agent function called by LangGraph.
    
    Reads research data from state,
    evaluates its quality and completeness,
    decides if it's sufficient or needs more research.
    
    Args:
        state: Shared state dictionary from LangGraph
        
    Returns:
        Updated state with validation_result
    """

    # Read values from shared state
    user_query = state["user_query"]
    research_data = state.get("research_data", "")
    confidence_score = state.get("confidence_score", 0)
    research_attempts = state.get("research_attempts", 0)

    print(f"\n[Validator Agent] Validating research...")
    print(f"[Validator Agent] Confidence score received: {confidence_score}/10")
    print(f"[Validator Agent] Research attempts so far: {research_attempts}")
    print(f"[Validator Agent] Research data length: {len(research_data)} characters")

    # --------------------------------------------------------
    # CHECK 1: Maximum attempts reached?
    # If Research Agent already tried 3 times, stop looping
    # and proceed with whatever we have
    # --------------------------------------------------------

    if research_attempts >= 3:
        print(f"[Validator Agent] Maximum attempts (3) reached!")
        print(f"[Validator Agent] Forcing: sufficient (proceeding with best available data)")
        return {
            "validation_result": "sufficient"
        }

    # --------------------------------------------------------
    # CHECK 2: Is research data completely empty?
    # --------------------------------------------------------

    if not research_data or len(research_data.strip()) < 50:
        print(f"[Validator Agent] Research data is empty or too short!")
        return {
            "validation_result": "insufficient"
        }

    # --------------------------------------------------------
    # CHECK 3: Ask GPT-4 to evaluate the research quality
    # --------------------------------------------------------

    # Build the evaluation prompt with all context
    evaluation_prompt = f"""
    User's original query: {user_query}
    
    Confidence score given by researcher: {confidence_score}/10
    
    Research data collected:
    {research_data}
    
    Please evaluate if this research is sufficient to answer the user's query.
    """

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", VALIDATOR_SYSTEM_PROMPT),
        ("human", evaluation_prompt)
    ])

    # Create the chain
    output_parser = StrOutputParser()
    validator_chain = prompt | llm | output_parser

    # Run the validation
    response = validator_chain.invoke({})

    print(f"[Validator Agent] GPT-4 evaluation: {response[:100]}...")

    # --------------------------------------------------------
    # STEP 4: Parse the response
    # --------------------------------------------------------

    validation_result = "sufficient"  # Default to sufficient

    lines = response.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("VALIDATION:"):
            result_text = line.replace("VALIDATION:", "").strip().lower()
            if "insufficient" in result_text:
                validation_result = "insufficient"
            else:
                validation_result = "sufficient"
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()
            print(f"[Validator Agent] Reason: {reason}")

    print(f"[Validator Agent] Final decision: {validation_result}")

    # Return updated state with validation result
    return {
        "validation_result": validation_result
    }


# ============================================================
# TEST BLOCK
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("Testing Validator Agent")
    print("=" * 50)

    # Test 1 — Good research data (should be sufficient)
    print("\nTest 1: Good research data")
    result1 = validator_agent({
        "user_query": "Tell me about Tesla",
        "research_data": """Tesla, Inc. reported strong Q1 2025 earnings with revenue 
        of $21.3 billion. CEO Elon Musk announced new Cybercab production starting 
        in Texas. Tesla stock is at $390 with a 15% year-over-year growth. 
        The company delivered 450,000 vehicles this quarter, beating analyst 
        expectations. New Gigafactory planned for India by 2026.""",
        "confidence_score": 8.0,
        "research_attempts": 1
    })
    print(f"Result: {result1}")

    # Test 2 — Poor research data (should be insufficient)
    print("\nTest 2: Poor research data")
    result2 = validator_agent({
        "user_query": "Tell me about Tesla financials",
        "research_data": "Tesla is a car company.",
        "confidence_score": 2.0,
        "research_attempts": 1
    })
    print(f"Result: {result2}")

    # Test 3 — Max attempts reached (should force sufficient)
    print("\nTest 3: Maximum attempts reached")
    result3 = validator_agent({
        "user_query": "Tell me about Tesla",
        "research_data": "Some minimal data found.",
        "confidence_score": 3.0,
        "research_attempts": 3
    })
    print(f"Result: {result3}")