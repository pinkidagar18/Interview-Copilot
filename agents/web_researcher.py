# agents/web_researcher.py
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tools.search_tool import search_web
from graph.state import AgentState

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)


def format_search_result(result) -> str:
    """
    Handles both string results (DuckDuckGo) 
    and list of dicts results (new Tavily).
    """
    if isinstance(result, str):
        return result[:1000]
    elif isinstance(result, list):
        # New Tavily returns list of dicts with 'content' key
        texts = []
        for item in result:
            if isinstance(item, dict):
                texts.append(item.get("content", str(item)))
            else:
                texts.append(str(item))
        return " ".join(texts)[:1000]
    else:
        return str(result)[:1000]


def web_researcher_node(state: AgentState) -> AgentState:
    """
    Company Intel Agent — Stage 2 of the pipeline.
    """
    print("\n" + "="*50)
    print("🌐 COMPANY INTEL AGENT")
    print("="*50)

    try:
        company_name = state.get("company_name", "")

        if not company_name:
            raise ValueError("No company name found in state")

        print(f"🏢 Researching: {company_name}")

        print("\n🔍 Search 1: Tech stack...")
        tech_results = format_search_result(
            search_web(f"{company_name} engineering tech stack programming languages")
        )

        print("🔍 Search 2: Culture and work environment...")
        culture_results = format_search_result(
            search_web(f"{company_name} company culture work environment employee review")
        )

        print("🔍 Search 3: Interview process...")
        interview_results = format_search_result(
            search_web(f"{company_name} software engineer interview process questions 2024")
        )

        combined_research = f"""
TECH STACK RESEARCH:
{tech_results}

CULTURE RESEARCH:
{culture_results}

INTERVIEW PROCESS RESEARCH:
{interview_results}
"""

        print("\n🤖 Summarizing research with Groq...")
        summary_prompt = f"""Based on this research about {company_name}, create a concise company profile.

Research Data:
{combined_research}

Return ONLY valid JSON with no extra text, no markdown, no backticks:
{{
    "company_name": "{company_name}",
    "tech_stack": ["technology1", "technology2"],
    "culture_values": ["value1", "value2"],
    "interview_style": "description of their interview style",
    "recent_news": "one sentence about recent company news",
    "what_they_look_for": ["quality1", "quality2", "quality3"]
}}"""

        response = llm.invoke(summary_prompt)
        raw_output = response.content.strip()

        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]
        raw_output = raw_output.strip()

        company_context = json.loads(raw_output)

        print(f"✅ Company research complete:")
        print(f"   Tech stack: {company_context.get('tech_stack', [])}")
        print(f"   Interview style: {company_context.get('interview_style', '')[:80]}...")

        return {
            **state,
            "company_context": company_context,
            "error_message": None
        }

    except Exception as e:
        print(f"❌ Web Researcher error: {e}")
        return {
            **state,
            "company_context": {
                "company_name": state.get("company_name", "Unknown"),
                "tech_stack": [],
                "culture_values": [],
                "interview_style": "Standard technical interview",
                "recent_news": "No recent news found",
                "what_they_look_for": ["problem solving", "communication", "technical skills"]
            },
            "error_message": str(e)
        }