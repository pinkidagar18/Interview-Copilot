# agents/interviewer.py
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from graph.state import AgentState

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.6
)


def interviewer_node(state: AgentState) -> AgentState:
    """
    Interviewer Agent — Stage 4 of the pipeline.

    What it does:
    1. Gets current question index from state
    2. Picks the next question from question_bank
    3. Determines current round (technical/hr)
    4. Adapts difficulty based on previous score
    5. Presents question naturally to the candidate
    6. Waits for answer (answer comes from UI/test harness)
    """
    print("\n" + "="*50)
    print("🎤 INTERVIEWER AGENT")
    print("="*50)

    try:
        question_bank = state.get("question_bank", [])
        current_index = state.get("current_question_index", 0)
        scores = state.get("scores", [])
        conversation_history = state.get("conversation_history", [])

        # Check if all questions are done
        if current_index >= len(question_bank):
            print("✅ All questions answered — marking complete")
            return {
                **state,
                "is_complete": True
            }

        # Get current question
        current_question = question_bank[current_index]

        # Determine round
        if current_question["type"] in ["technical"]:
            current_round = "technical"
        elif current_question["type"] == "behavioural":
            current_round = "hr"
        else:
            current_round = "hr"

        # Adapt difficulty signal based on last score
        difficulty_hint = ""
        if scores:
            last_score = scores[-1].get("overall", 5)
            if last_score < 4:
                difficulty_hint = " (Note: Previous answer was weak — probe deeper)"
            elif last_score >= 8:
                difficulty_hint = " (Note: Strong answer — increase difficulty)"

        # Format question naturally using Groq
        format_prompt = f"""You are a professional interviewer at {state.get('company_name', 'a top tech company')}.

Ask this interview question naturally and professionally. Add a brief context sentence before the question if it makes it flow better. Keep it concise.

Question to ask: {current_question['question']}
Question type: {current_question['type']}
Round: {current_round}
{difficulty_hint}

Return ONLY the formatted question text. No labels, no JSON, just the question as you would say it."""

        response = llm.invoke(format_prompt)
        formatted_question = response.content.strip()

        print(f"\n📍 Question {current_index + 1}/{len(question_bank)}")
        print(f"   Type: {current_question['type']} | Round: {current_round}")
        print(f"   Difficulty: {current_question.get('difficulty', 'medium')}")
        print(f"\n🎤 INTERVIEWER: {formatted_question}")

        # Add question to conversation history
        updated_history = conversation_history + [{
            "role": "interviewer",
            "content": formatted_question,
            "question_id": current_question["id"],
            "question_type": current_question["type"],
            "question_index": current_index
        }]

        return {
            **state,
            "current_round": current_round,
            "conversation_history": updated_history,
            "is_complete": False,
            "error_message": None
        }

    except Exception as e:
        print(f"❌ Interviewer error: {e}")
        return {
            **state,
            "error_message": str(e)
        }


def submit_answer(state: AgentState, answer: str) -> AgentState:
    """
    Helper function called by UI/test harness to submit candidate answer.
    Adds answer to conversation history so evaluator can score it.
    """
    conversation_history = state.get("conversation_history", [])

    updated_history = conversation_history + [{
        "role": "candidate",
        "content": answer,
        "question_index": state.get("current_question_index", 0)
    }]

    print(f"\n👤 CANDIDATE: {answer}")

    return {
        **state,
        "conversation_history": updated_history
    }