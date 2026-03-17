# agents/jd_analyzer.py
import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from graph.state import AgentState

load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1  # Low temperature = more consistent structured output
)


def jd_analyzer_node(state: AgentState) -> AgentState:
    """
    JD Analyzer Agent — Stage 2 of the pipeline.

    What it does:
    1. Takes raw job description text from state
    2. Sends to Groq with a structured extraction prompt
    3. Parses the JSON response
    4. Writes jd_skills back to state
    """
    print("\n" + "="*50)
    print("📋 JD ANALYZER AGENT")
    print("="*50)

    try:
        jd_text = state.get("jd_text", "")

        if not jd_text:
            raise ValueError("No job description found in state")

        print(f"📝 JD text length: {len(jd_text)} characters")

        # Prompt engineered for consistent JSON output
        prompt = f"""You are an expert technical recruiter. Analyze this job description and extract structured information.

Job Description:
{jd_text}

Return ONLY valid JSON with no extra text, no markdown, no backticks. Use exactly this format:
{{
    "required_skills": ["skill1", "skill2", "skill3"],
    "preferred_skills": ["skill1", "skill2"],
    "seniority_level": "junior/mid/senior",
    "key_responsibilities": ["responsibility1", "responsibility2"],
    "tech_stack": ["technology1", "technology2"],
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""

        print("🤖 Sending JD to Groq for analysis...")
        response = llm.invoke(prompt)
        raw_output = response.content.strip()

        # Clean up response in case model adds backticks
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]
        raw_output = raw_output.strip()

        # Parse JSON
        jd_skills = json.loads(raw_output)

        print(f"✅ JD Analysis complete:")
        print(f"   Required skills: {jd_skills.get('required_skills', [])}")
        print(f"   Seniority level: {jd_skills.get('seniority_level', 'unknown')}")
        print(f"   Tech stack: {jd_skills.get('tech_stack', [])}")

        return {
            **state,
            "jd_skills": jd_skills,
            "error_message": None
        }

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"   Raw output was: {raw_output[:200]}")
        # Return safe fallback
        return {
            **state,
            "jd_skills": {
                "required_skills": [],
                "preferred_skills": [],
                "seniority_level": "mid",
                "key_responsibilities": [],
                "tech_stack": [],
                "keywords": []
            },
            "error_message": f"JD parsing failed: {str(e)}"
        }

    except Exception as e:
        print(f"❌ JD Analyzer error: {e}")
        return {
            **state,
            "jd_skills": {},
            "error_message": str(e)
        }