# agents/report_generator.py
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from jinja2 import Environment, FileSystemLoader
from graph.state import AgentState

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)


def calculate_scores(scores: list) -> dict:
    """Calculate all aggregate scores from raw score list."""
    if not scores:
        return {}

    # Overall average
    overall = round(sum(s.get("overall", 0) for s in scores) / len(scores), 1)

    # STAR dimension averages
    star_averages = {
        "Situation": round(sum(s.get("S", 0) for s in scores) / len(scores), 1),
        "Task":      round(sum(s.get("T", 0) for s in scores) / len(scores), 1),
        "Action":    round(sum(s.get("A", 0) for s in scores) / len(scores), 1),
        "Result":    round(sum(s.get("R", 0) for s in scores) / len(scores), 1),
    }

    # Average by question type
    type_scores = {"technical": 0, "behavioural": 0, "company_specific": 0}
    type_counts = {"technical": 0, "behavioural": 0, "company_specific": 0}

    for s in scores:
        qtype = s.get("question_type", "technical")
        if qtype in type_scores:
            type_scores[qtype] += s.get("overall", 0)
            type_counts[qtype] += 1

    for qtype in type_scores:
        if type_counts[qtype] > 0:
            type_scores[qtype] = round(
                type_scores[qtype] / type_counts[qtype], 1
            )

    return {
        "overall": overall,
        "star_averages": star_averages,
        "type_scores": type_scores
    }


def get_readiness_label(score: float) -> str:
    """Convert score to readiness label."""
    if score >= 80:
        return "🟢 Strong — Ready to Interview"
    elif score >= 65:
        return "🟡 Good — Minor Gaps to Address"
    elif score >= 50:
        return "🟠 Fair — Needs More Preparation"
    else:
        return "🔴 Needs Work — Focused Study Required"


def generate_study_plan(weak_areas: list, company_name: str) -> list:
    """Use Groq to generate a personalized study plan."""
    if not weak_areas:
        return [{"topic": "Keep practising", "action": "You're in great shape! Do 2-3 mock interviews per week to maintain your edge."}]

    weak_skills = [area["skill"] for area in weak_areas]

    prompt = f"""You are a senior engineering mentor. Create a concise study plan for these weak areas:
Weak skills: {', '.join(weak_skills)}
Target company: {company_name}

Return ONLY valid JSON, no markdown, no backticks:
[
    {{
        "topic": "skill name",
        "action": "specific 2-3 sentence action plan with resources"
    }}
]"""

    try:
        response = llm.invoke(prompt)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return [{"topic": skill, "action": f"Study {skill} fundamentals and practice with real examples."} 
                for skill in weak_skills]


def report_generator_node(state: AgentState) -> AgentState:
    """
    Report Generator Agent — Stage 5 of the pipeline.

    What it does:
    1. Reads all scores from state
    2. Calculates overall + per-dimension + per-type scores
    3. Identifies weak areas (score < 6)
    4. Generates study plan using Groq
    5. Renders HTML report using Jinja2 template
    6. Converts HTML to PDF using WeasyPrint
    7. Saves PDF to outputs/ folder
    8. Writes report_html to state
    """
    print("\n" + "="*50)
    print("📄 REPORT GENERATOR AGENT")
    print("="*50)

    try:
        scores = state.get("scores", [])
        company_name = state.get("company_name", "Target Company")
        jd_skills = state.get("jd_skills", {})

        if not scores:
            raise ValueError("No scores found — interview may not have completed")

        print(f"📊 Processing {len(scores)} scored answers...")

        # Calculate all scores
        score_data = calculate_scores(scores)
        overall_pct = round(score_data["overall"] * 10)  # convert /10 to %

        print(f"   Overall score: {score_data['overall']}/10 ({overall_pct}%)")

        # Identify weak areas (score < 6)
        weak_areas = []
        for s in scores:
            if s.get("overall", 0) < 6:
                weak_areas.append({
                    "skill": s.get("question_type", "unknown").replace("_", " ").title(),
                    "feedback": s.get("missing", "Needs improvement")
                })

        print(f"   Weak areas found: {len(weak_areas)}")

        # Generate study plan
        print("🤖 Generating study plan with Groq...")
        study_plan = generate_study_plan(weak_areas, company_name)

        # Build question reviews for template
        question_reviews = []
        for s in scores:
            question_reviews.append({
                "question": s.get("question_text", ""),
                "type": s.get("question_type", "technical").replace("_", " "),
                "S": s.get("S", 0),
                "T": s.get("T", 0),
                "A": s.get("A", 0),
                "R": s.get("R", 0),
                "overall": s.get("overall", 0),
                "candidate_answer": s.get("candidate_answer", ""),
                "good": s.get("good", ""),
                "missing": s.get("missing", ""),
                "model_answer": s.get("model_answer", "")
            })

        # Render HTML template
        print("🎨 Rendering HTML report...")
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("report_template.html")

        report_html = template.render(
            company_name=company_name,
            role_level=jd_skills.get("seniority_level", "Mid").title(),
            overall_score=overall_pct,
            readiness_label=get_readiness_label(overall_pct),
            star_averages=score_data["star_averages"],
            type_scores=score_data["type_scores"],
            weak_areas=weak_areas,
            study_plan=study_plan,
            question_reviews=question_reviews
        )

        # Save HTML
        os.makedirs("outputs", exist_ok=True)
        html_path = "outputs/report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(report_html)
        print(f"✅ HTML report saved: {html_path}")

        # Convert to PDF using WeasyPrint
        print("📄 Converting to PDF...")
        try:
            from weasyprint import HTML
            pdf_path = "outputs/interview_report.pdf"
            HTML(string=report_html).write_pdf(pdf_path)
            print(f"✅ PDF report saved: {pdf_path}")
        except Exception as pdf_error:
            print(f"⚠ PDF generation failed: {pdf_error}")
            print("  HTML report is still available at outputs/report.html")

        print(f"\n📊 Final Summary:")
        print(f"   Overall Readiness: {overall_pct}%")
        print(f"   {get_readiness_label(overall_pct)}")
        print(f"   Weak areas: {len(weak_areas)}")
        print(f"   Study plan items: {len(study_plan)}")

        return {
            **state,
            "report_html": report_html,
            "error_message": None
        }

    except Exception as e:
        print(f"❌ Report Generator error: {e}")
        return {
            **state,
            "report_html": "",
            "error_message": str(e)
        }