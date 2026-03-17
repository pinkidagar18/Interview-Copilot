# agents/answer_evaluator.py
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from graph.state import AgentState

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1  # Low temp = consistent scoring
)


def evaluator_node(state: AgentState) -> AgentState:
    """
    Answer Evaluator Agent — Stage 4 of the pipeline.

    What it does:
    1. Gets the last question and candidate answer from history
    2. Gets expected answer from question bank
    3. Sends to Groq with STAR scoring prompt
    4. Stores score in state
    5. Advances question index
    6. Sets is_complete if all questions answered
    """
    print("\n" + "="*50)
    print("📊 ANSWER EVALUATOR AGENT")
    print("="*50)

    try:
        question_bank = state.get("question_bank", [])
        current_index = state.get("current_question_index", 0)
        conversation_history = state.get("conversation_history", [])
        scores = state.get("scores", [])

        # Get current question details
        if current_index >= len(question_bank):
            return {**state, "is_complete": True}

        current_question = question_bank[current_index]

        # Extract last interviewer question and candidate answer
        interviewer_msg = None
        candidate_answer = None

        for msg in reversed(conversation_history):
            if msg["role"] == "candidate" and candidate_answer is None:
                candidate_answer = msg["content"]
            if msg["role"] == "interviewer" and interviewer_msg is None:
                interviewer_msg = msg["content"]
            if interviewer_msg and candidate_answer:
                break

        if not candidate_answer:
            print("⚠ No candidate answer found — skipping evaluation")
            return {
                **state,
                "current_question_index": current_index + 1,
                "is_complete": (current_index + 1) >= len(question_bank)
            }

        print(f"\n📝 Evaluating answer for Q{current_index + 1}...")
        print(f"   Question type: {current_question['type']}")
        print(f"   Answer preview: {candidate_answer[:100]}...")

        # STAR scoring prompt
        star_prompt = f"""You are an expert technical interviewer. Evaluate this interview answer using the STAR framework.

Question: {current_question['question']}
Question Type: {current_question['type']}
Expected Answer Should Cover: {current_question.get('expected_answer', 'Relevant technical knowledge and clear explanation')}

Candidate's Answer: {candidate_answer}

Score each STAR dimension from 0-10:
- Situation (S): Did they set clear context? (For technical: did they explain the problem/scenario?)
- Task (T): Was their specific role/goal clear?
- Action (A): Were their specific steps detailed and personal? (Used "I" not "we"?)
- Result (R): Was there a measurable outcome or impact?

Return ONLY valid JSON, no markdown, no backticks:
{{
    "S": 0,
    "T": 0,
    "A": 0,
    "R": 0,
    "overall": 0,
    "good": "what was strong about this answer",
    "missing": "what was missing or weak",
    "model_answer": "how a top candidate would have answered this"
}}"""

        response = llm.invoke(star_prompt)
        raw_output = response.content.strip()

        # Clean up response
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]
        raw_output = raw_output.strip()

        score_data = json.loads(raw_output)

        # Add metadata to score
        score_data["question_id"] = current_question["id"]
        score_data["question_index"] = current_index
        score_data["question_text"] = current_question["question"]
        score_data["candidate_answer"] = candidate_answer
        score_data["question_type"] = current_question["type"]

        # Compute overall if not provided
        if not score_data.get("overall"):
            score_data["overall"] = round(
                (score_data["S"] + score_data["T"] +
                 score_data["A"] + score_data["R"]) / 4, 1
            )

        print(f"\n📊 STAR Scores:")
        print(f"   S (Situation): {score_data['S']}/10")
        print(f"   T (Task):      {score_data['T']}/10")
        print(f"   A (Action):    {score_data['A']}/10")
        print(f"   R (Result):    {score_data['R']}/10")
        print(f"   Overall:       {score_data['overall']}/10")
        print(f"\n✅ Good: {score_data['good'][:100]}")
        print(f"❌ Missing: {score_data['missing'][:100]}")

        # Advance to next question
        next_index = current_index + 1
        is_complete = next_index >= len(question_bank)

        if is_complete:
            print("\n🏁 All questions completed!")
        else:
            print(f"\n➡ Moving to question {next_index + 1}/{len(question_bank)}")

        return {
            **state,
            "scores": scores + [score_data],
            "current_question_index": next_index,
            "is_complete": is_complete,
            "error_message": None
        }

    except Exception as e:
        print(f"❌ Evaluator error: {e}")
        # Advance index even on error to avoid infinite loop
        next_index = state.get("current_question_index", 0) + 1
        return {
            **state,
            "current_question_index": next_index,
            "is_complete": next_index >= len(state.get("question_bank", [])),
            "error_message": str(e)
        }