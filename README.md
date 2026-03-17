# 🎯 InterviewCopilot AI

> AI-powered personalised interview coach — Resume × JD × Company Intelligence

![Python](https://img.shields.io/badge/Python-3.11-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)
![Docker](https://img.shields.io/badge/Docker-Containerised-blue)

## What is this?

InterviewCopilot reads your resume, analyses the job description,
researches the company on the web — then conducts a full mock interview
tailored specifically to you. At the end it gives you a readiness score
and a downloadable PDF report.

## How it's different

| Feature | Generic tools | InterviewCopilot |
|---|---|---|
| Questions | Generic Q&A bank | Resume × JD × Company |
| Evaluation | Right/wrong | STAR scoring 0-10 |
| Difficulty | Fixed | Adaptive |
| Output | Nothing | PDF readiness report |

## Tech Stack

- **LangGraph** — cyclic multi-agent orchestration
- **ChromaDB** — vector store for resume RAG
- **Groq** — LLM inference (llama-3.3-70b)
- **Tavily** — live company research
- **FastAPI** — REST API backend
- **Streamlit** — frontend UI
- **WeasyPrint** — PDF generation
- **Docker** — containerisation

## Run Locally
```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/interview-copilot
cd interview-copilot

# 2. Setup
cp .env.example .env
# Add your GROQ_API_KEY and TAVILY_API_KEY to .env

# 3. Run with Docker
docker-compose up --build

# 4. Open
# UI: http://localhost:8501
# API: http://localhost:8000/docs
```

## Run Without Docker
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Terminal 1
uvicorn api.main:app --reload --port 8000

# Terminal 2
streamlit run app/streamlit_app.py
```

## Architecture
```
User Input (Resume + JD + Company)
        ↓
Resume RAG Agent → ChromaDB
JD Analyzer Agent → Groq
Company Intel Agent → Tavily
        ↓
Question Generator (15 personalised questions)
        ↓
Cyclic Interview Loop (LangGraph)
Interviewer Agent ↔ Answer Evaluator Agent
        ↓
Report Generator → PDF
```

## Project Structure
```
interview-copilot/
├── agents/          # 7 AI agents
├── graph/           # LangGraph state + workflow
├── tools/           # ChromaDB, search, PDF loader
├── app/             # Streamlit UI
├── api/             # FastAPI backend
├── templates/       # HTML report template
└── outputs/         # Generated reports
```