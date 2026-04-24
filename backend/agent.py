"""
Travel Deal Investigator — Agentic Loop with Gemini
Handles: Query → LLM → Tool Call → Tool Result → Query → LLM → ... → Final Answer
Each query accumulates ALL past interactions.
"""

import google.generativeai as genai
from tools import TOOL_FUNCTIONS
import json
import time


# ============================================================
# TOOL DECLARATIONS (sent to Gemini so it knows what tools exist)
# ============================================================

TOOL_DECLARATIONS = [
    {
        "name": "analyze_deal",
        "description": (
            "Parses and extracts structured information from travel deal text. "
            "Returns origin, destination, price, dates, airline, and deal type. "
            "Always call this FIRST to understand the deal."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "deal_text": {
                    "type": "string",
                    "description": "The raw text of the travel deal to analyze"
                }
            },
            "required": ["deal_text"]
        }
    },
    {
        "name": "check_price_history",
        "description": (
            "Checks historical price data for a travel route. "
            "Returns lowest, average, highest prices seen, plus a 6-month trend. "
            "Use this to determine if the deal price is actually good."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Travel destination city or region"
                },
                "origin": {
                    "type": "string",
                    "description": "Origin city or region"
                },
                "deal_type": {
                    "type": "string",
                    "description": "Type of deal: Flight, Hotel, or Travel Package"
                }
            },
            "required": ["destination"]
        }
    },
    {
        "name": "get_destination_info",
        "description": (
            "Returns travel information about a destination including visa requirements, "
            "weather by season, safety advisories, travel tips, and average daily budget. "
            "Use this to give travelers useful context about the destination."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The destination city or country to get information about"
                }
            },
            "required": ["destination"]
        }
    }
]

SYSTEM_INSTRUCTION = """You are a Travel Deal Investigator Agent. Your job is to thoroughly analyze travel deals and give users an honest verdict.

IMPORTANT WORKFLOW — You MUST follow these steps in order:
1. FIRST call analyze_deal to parse the deal text
2. THEN call check_price_history to compare against historical prices
3. THEN call get_destination_info to provide travel context
4. FINALLY, synthesize everything into a clear verdict

For each step, briefly explain your reasoning BEFORE calling the tool.
After all tools are called, give a final verdict with:
- Deal Score: Great Deal / Good Deal / Average / Bad Deal
- Price Analysis: Is the price good compared to historical data?
- Destination Highlights: Key info travelers should know
- Recommendation: Your honest advice

Be specific with numbers and facts. Be helpful and honest — if a deal is bad, say so."""


# ============================================================
# AGENTIC LOOP
# ============================================================

def run_agent(deal_text: str, api_key: str) -> dict:
    """
    Runs the full agentic loop:
    Query → Gemini → Tool Call → Tool Result → Query → Gemini → ... → Final Answer

    Returns a dict with:
      - steps: list of reasoning chain steps (for UI display)
      - logs: raw text logs (for assignment submission)
      - final_answer: the agent's final verdict text
    """

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-3-flash-preview",
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[{"function_declarations": TOOL_DECLARATIONS}]
    )

    # State
    steps = []          # Reasoning chain for UI
    logs = []           # Raw logs for assignment
    max_iterations = 10 # Safety limit
    iteration = 0

    def add_log(msg):
        timestamp = time.strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")
        print(f"[{timestamp}] {msg}")  # Also print to terminal

    def add_step(step_type, title, content):
        steps.append({
            "type": step_type,
            "title": title,
            "content": content
        })

    # Start the conversation
    add_log(f"🚀 [AGENT] Starting investigation...")
    add_log(f"📝 [USER QUERY] {deal_text}")

    chat = model.start_chat()

    # Initial query
    user_message = f'Investigate this travel deal and give me a thorough analysis:\n\n"{deal_text}"'
    add_log(f"\n📤 [SENDING TO GEMINI] Query 1: {user_message[:100]}...")

    response = chat.send_message(user_message)

    # ---- AGENTIC LOOP ----
    while iteration < max_iterations:
        iteration += 1
        add_log(f"\n🔄 [ITERATION {iteration}]")

        # Check if response has function calls
        has_function_call = False

        for part in response.parts:
            # Text response (agent's reasoning/thought)
            if hasattr(part, 'text') and part.text:
                add_log(f"💭 [AGENT THOUGHT] {part.text[:200]}...")
                add_step("thought", "Agent Thinking", part.text)

            # Function call (tool invocation)
            if hasattr(part, 'function_call') and part.function_call:
                has_function_call = True
                fn_call = part.function_call
                tool_name = fn_call.name
                tool_args = dict(fn_call.args) if fn_call.args else {}

                add_log(f"🔧 [TOOL CALL] {tool_name}({json.dumps(tool_args)})")
                add_step("tool-call", f"Tool Call: {tool_name}", json.dumps(tool_args, indent=2))

                # Execute the tool
                try:
                    tool_fn = TOOL_FUNCTIONS.get(tool_name)
                    if not tool_fn:
                        raise ValueError(f"Unknown tool: {tool_name}")
                    tool_result = tool_fn(tool_args)
                except Exception as e:
                    tool_result = json.dumps({"error": str(e)})
                    add_log(f"❌ [TOOL ERROR] {str(e)}")

                add_log(f"📊 [TOOL RESULT] {tool_name} → {tool_result[:200]}...")
                add_step("tool-result", f"Result: {tool_name}", tool_result)

                # Send tool result back to Gemini (conversation history is automatic with chat)
                add_log(f"📤 [SENDING TO GEMINI] Tool result for {tool_name}")

                response = chat.send_message(
                    genai.protos.Content(
                        parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={"result": tool_result}
                            )
                        )]
                    )
                )
                # Break inner loop to re-process new response
                break

        # If no function call was found, agent is done
        if not has_function_call:
            add_log(f"\n✅ [AGENT COMPLETE] Investigation finished after {iteration} iterations")
            break

    # Extract final answer
    final_answer = ""
    for part in response.parts:
        if hasattr(part, 'text') and part.text:
            final_answer += part.text

    if not final_answer:
        final_answer = "The agent completed its investigation but did not produce a final summary."

    add_log(f"\n📋 [FINAL VERDICT]\n{final_answer}")

    # Log the full conversation history
    add_log(f"\n{'='*60}")
    add_log(f"FULL CONVERSATION HISTORY ({len(chat.history)} turns):")
    add_log(f"{'='*60}")
    for i, msg in enumerate(chat.history):
        role = msg.role
        parts_summary = []
        for p in msg.parts:
            if hasattr(p, 'text') and p.text:
                parts_summary.append(f"TEXT: {p.text[:100]}...")
            if hasattr(p, 'function_call') and p.function_call:
                parts_summary.append(f"FUNC_CALL: {p.function_call.name}")
            if hasattr(p, 'function_response') and p.function_response:
                parts_summary.append(f"FUNC_RESULT: {p.function_response.name}")
        add_log(f"  Turn {i+1} [{role}]: {' | '.join(parts_summary)}")

    return {
        "steps": steps,
        "logs": "\n".join(logs),
        "final_answer": final_answer,
        "iterations": iteration
    }
