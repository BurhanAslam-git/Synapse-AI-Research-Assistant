# ============================================================
# agents/clarity_agent.py — Agent 1: Query Clarity Checker
# ============================================================
# Evaluates whether the user's query is precise enough to research.
# Uses conversation history so follow-ups like "tell me about their CEO"
# are clear when Tesla was discussed in the previous turn.
# ============================================================

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0
)

CLARITY_SYSTEM_PROMPT = """You are a Query Clarity Analyzer for a multi-turn business research assistant.

Your job is to decide whether the CURRENT user message can be researched, using BOTH:
1. The current message
2. The full conversation history (prior user and assistant turns)

A query is CLEAR if ANY of these apply:
- The current message names a specific company (Tesla, Apple, Microsoft, etc.)
- The current message is a follow-up that clearly continues the same topic or company
  from earlier in the conversation (e.g. prior turn was about Tesla, now user asks
  "tell me about their CEO", "what about competitors?", "more on the financials")
- Pronouns and references (their, they, it, the company, the CEO) can be resolved from history

A query NEEDS CLARIFICATION only if:
- No company or research subject can be inferred from the current message OR history
- The conversation history is empty or unrelated and the current message is too vague
  (e.g. "tell me about that company", "how is it doing?" with no prior context)

Examples:
- History: User asked about Tesla → Current: "tell me about their CEO" → CLEAR
- History: User asked about Apple earnings → Current: "what about their competitors?" → CLEAR
- No history → Current: "tell me about their CEO" → NEEDS CLARIFICATION
- Current: "Tell me about Tesla's recent news" → CLEAR (standalone)

Respond in this EXACT format only:

STATUS: clear
or
STATUS: needs_clarification
QUESTION: [clarification question for the user]

If STATUS is clear AND the current message depends on conversation context, also add:
RESOLVED_QUERY: [standalone research query with company/topic filled in from history]

Example RESOLVED_QUERY for follow-up:
  History mentions Tesla, current message is "tell me about their CEO"
  → RESOLVED_QUERY: Tell me about Tesla's CEO

If STATUS is clear and the message is already fully self-contained, omit RESOLVED_QUERY.
If STATUS is needs_clarification, include QUESTION and omit RESOLVED_QUERY.
"""


def _format_conversation_history(messages: list[BaseMessage], max_messages: int = 10) -> str:
    """Turn LangChain message objects into readable text for the clarity prompt."""
    if not messages:
        return "No prior conversation."

    lines = []
    for msg in messages[-max_messages:]:
        if isinstance(msg, HumanMessage):
            lines.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            # Truncate long assistant replies — clarity only needs topic/company context
            content = msg.content or ""
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"Assistant: {content}")
        elif hasattr(msg, "content"):
            role = getattr(msg, "type", "message")
            lines.append(f"{role}: {msg.content}")

    return "\n".join(lines)


prompt = ChatPromptTemplate.from_messages([
    ("system", CLARITY_SYSTEM_PROMPT),
    (
        "human",
        "Conversation history:\n{conversation_history}\n\n"
        "Current user message:\n{user_query}\n\n"
        "Analyze the current message using the history above."
    ),
])

output_parser = StrOutputParser()
clarity_chain = prompt | llm | output_parser


def clarity_agent(state: dict) -> dict:
    """
    Clarity Agent — evaluates query clarity with multi-turn context.

    Reads user_query and messages from state. When a follow-up references a
    company from history, marks the query clear and rewrites user_query via
    RESOLVED_QUERY so downstream agents search the right topic.
    """
    user_query = state["user_query"]
    messages = state.get("messages", [])
    conversation_history = _format_conversation_history(messages)

    print(f"\n[Clarity Agent] Analyzing query: '{user_query}'")
    print(f"[Clarity Agent] History: {len(messages)} prior message(s)")

    response = clarity_chain.invoke({
        "user_query": user_query,
        "conversation_history": conversation_history,
    })

    print(f"[Clarity Agent] Raw response: {response}")

    clarity_status = "clear"
    clarification_request = None
    resolved_query = None

    for line in response.strip().split("\n"):
        line = line.strip()
        if line.startswith("STATUS:"):
            clarity_status = line.replace("STATUS:", "").strip()
        elif line.startswith("QUESTION:"):
            clarification_request = line.replace("QUESTION:", "").strip()
        elif line.startswith("RESOLVED_QUERY:"):
            resolved_query = line.replace("RESOLVED_QUERY:", "").strip()

    print(f"[Clarity Agent] Decision: {clarity_status}")
    if resolved_query:
        print(f"[Clarity Agent] Resolved query: {resolved_query}")
    if clarification_request:
        print(f"[Clarity Agent] Clarification needed: {clarification_request}")

    result = {
        "clarity_status": clarity_status,
        "clarification_request": clarification_request,
    }

    # Pass a standalone query to Research/Synthesis when follow-up was contextual
    if resolved_query and clarity_status == "clear":
        result["user_query"] = resolved_query

    return result


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Clarity Agent")
    print("=" * 50)

    print("\nTest 1: Clear standalone query")
    result1 = clarity_agent({
        "user_query": "Tell me about Tesla's recent news",
        "messages": [],
    })
    print(f"Result: {result1}")

    print("\nTest 2: Vague query with no history")
    result2 = clarity_agent({
        "user_query": "Tell me about that tech company",
        "messages": [],
    })
    print(f"Result: {result2}")

    print("\nTest 3: Follow-up with Tesla context (multi-turn)")
    result3 = clarity_agent({
        "user_query": "tell me about their CEO",
        "messages": [
            HumanMessage(content="Tell me about Tesla's recent news"),
            AIMessage(
                content="Tesla reported strong Q4 results and continued EV leadership..."
            ),
        ],
    })
    print(f"Result: {result3}")
    assert result3.get("clarity_status") == "clear", "Expected follow-up to be clear"
    assert "Tesla" in result3.get("user_query", ""), "Expected resolved query to mention Tesla"
