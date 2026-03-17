# graph/workflow.py
from langgraph.graph import StateGraph, END
from graph.state import AgentState

# ── All real agents now ──────────────────────────────────────────
from agents.resume_parser import resume_parser_node
from agents.jd_analyzer import jd_analyzer_node
from agents.web_researcher import web_researcher_node
from agents.question_generator import question_generator_node
from agents.interviewer import interviewer_node
from agents.answer_evaluator import evaluator_node
from agents.report_generator import report_generator_node

# ── Conditional edge function ────────────────────────────────────
def should_continue(state: AgentState) -> str:
    if state.get("is_complete", False):
        return "generate_report"
    return "ask_question"

# ── Build graph ──────────────────────────────────────────────────
def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("parse_resume", resume_parser_node)
    workflow.add_node("analyze_jd", jd_analyzer_node)
    workflow.add_node("research_company", web_researcher_node)
    workflow.add_node("generate_questions", question_generator_node)
    workflow.add_node("ask_question", interviewer_node)
    workflow.add_node("evaluate_answer", evaluator_node)
    workflow.add_node("generate_report", report_generator_node)

    workflow.set_entry_point("parse_resume")
    workflow.add_edge("parse_resume", "analyze_jd")
    workflow.add_edge("analyze_jd", "research_company")
    workflow.add_edge("research_company", "generate_questions")
    workflow.add_edge("generate_questions", "ask_question")
    workflow.add_edge("ask_question", "evaluate_answer")
    workflow.add_conditional_edges(
        "evaluate_answer",
        should_continue,
        {
            "ask_question": "ask_question",
            "generate_report": "generate_report",
        }
    )
    workflow.add_edge("generate_report", END)

    return workflow.compile()

app = build_graph()