# agents/question_generator.py
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tools.chroma_store import query_chunks
from graph.state import AgentState

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7  # Higher temp = more creative/varied questions
)


def question_generator_node(state: AgentState) -> AgentState:
    """
    Question Generator Agent — Stage 3 of the pipeline.

    What it does:
    1. Queries ChromaDB for relevant resume sections
    2. Combines resume context + JD skills + company context
    3. Sends everything to Groq with a carefully engineered prompt
    4. Generates 15 personalized questions (5 tech + 5 behavioural + 5 company)
    5. Writes question_bank to state
    """
    print("\n" + "="*50)
    print("❓ QUESTION GENERATOR AGENT")
    print("="*50)

    try:
        jd_skills = state.get("jd_skills", {})
        company_context = state.get("company_context", {})

        # Query ChromaDB for most relevant resume sections
        print("🔍 Querying resume from ChromaDB...")
        skills_chunks = query_chunks(
            query="technical skills programming languages frameworks",
            collection_name="resume",
            n_results=3
        )
        project_chunks = query_chunks(
            query="projects built experience work",
            collection_name="resume",
            n_results=3
        )

        # Combine resume context
        resume_context = "\n".join(skills_chunks + project_chunks)

        # Build the prompt
        prompt = f"""You are an expert technical interviewer at {company_context.get('company_name', 'a top tech company')}.

You have the following information about the candidate and role:

CANDIDATE RESUME HIGHLIGHTS:
{resume_context}

JOB REQUIREMENTS:
- Required Skills: {', '.join(jd_skills.get('required_skills', []))}
- Preferred Skills: {', '.join(jd_skills.get('preferred_skills', []))}
- Seniority Level: {jd_skills.get('seniority_level', 'mid')}
- Key Responsibilities: {', '.join(jd_skills.get('key_responsibilities', []))}

COMPANY CONTEXT:
- Tech Stack: {', '.join(company_context.get('tech_stack', []))}
- Interview Style: {company_context.get('interview_style', '')}
- What They Look For: {', '.join(company_context.get('what_they_look_for', []))}

Generate exactly 15 interview questions — 5 technical, 5 behavioural, 5 company-specific.

Rules:
- Technical questions must test skills from the JD that match or gap with the resume
- Behavioural questions must use STAR format (Situation, Task, Action, Result)
- Company-specific questions must reference the actual company culture/tech/values
- Every question must be specific to THIS candidate applying to THIS company
- Include what a perfect answer would contain

Return ONLY valid JSON, no markdown, no backticks, no extra text:
{{
    "technical": [
        {{
            "id": "T1",
            "question": "question text here",
            "type": "technical",
            "difficulty": "easy/medium/hard",
            "skill_tested": "which skill this tests",
            "expected_answer": "key points a good answer should cover"
        }}
    ],
    "behavioural": [
        {{
            "id": "B1",
            "question": "Tell me about a time when...",
            "type": "behavioural",
            "difficulty": "medium",
            "skill_tested": "which soft skill this tests",
            "expected_answer": "what STAR components to look for"
        }}
    ],
    "company_specific": [
        {{
            "id": "C1",
            "question": "question about company culture/values/tech",
            "type": "company_specific",
            "difficulty": "medium",
            "skill_tested": "cultural fit / company knowledge",
            "expected_answer": "what a well-researched answer looks like"
        }}
    ]
}}"""

        print("🤖 Generating 15 personalized questions with Groq...")
        response = llm.invoke(prompt)
        raw_output = response.content.strip()

        # Clean up response
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]
        raw_output = raw_output.strip()

        questions_dict = json.loads(raw_output)

        # Flatten into single list with order: technical → behavioural → company
        question_bank = []
        question_bank.extend(questions_dict.get("technical", []))
        question_bank.extend(questions_dict.get("behavioural", []))
        question_bank.extend(questions_dict.get("company_specific", []))

        print(f"\n✅ Question bank generated:")
        print(f"   Technical:        {len(questions_dict.get('technical', []))} questions")
        print(f"   Behavioural:      {len(questions_dict.get('behavioural', []))} questions")
        print(f"   Company-specific: {len(questions_dict.get('company_specific', []))} questions")
        print(f"   Total:            {len(question_bank)} questions")

        # Preview first question of each type
        print(f"\n📋 Sample questions:")
        for category in ["technical", "behavioural", "company_specific"]:
            qs = questions_dict.get(category, [])
            if qs:
                print(f"\n   [{category.upper()}]")
                print(f"   Q: {qs[0]['question']}")
                print(f"   Tests: {qs[0]['skill_tested']}")

        return {
            **state,
            "question_bank": question_bank,
            "current_question_index": 0,
            "current_round": "technical",
            "error_message": None
        }

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"   Raw output: {raw_output[:300]}")
        return {
            **state,
            "question_bank": [],
            "error_message": f"Question generation failed: {str(e)}"
        }

    except Exception as e:
        print(f"❌ Question Generator error: {e}")
        return {
            **state,
            "question_bank": [],
            "error_message": str(e)
        }