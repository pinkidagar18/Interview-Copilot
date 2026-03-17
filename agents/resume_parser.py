# agents/resume_parser.py
from graph.state import AgentState
from tools.pdf_loader import load_pdf, chunk_text
from tools.chroma_store import store_chunks, query_chunks


def resume_parser_node(state: AgentState) -> AgentState:
    """
    Resume RAG Agent — Stage 2 of the pipeline.
    
    What it does:
    1. Takes raw resume text from state
    2. Splits into chunks
    3. Embeds and stores in ChromaDB
    4. Does a test query to verify RAG is working
    5. Writes resume_chunks back to state
    """
    print("\n" + "="*50)
    print("📄 RESUME PARSER AGENT")
    print("="*50)

    try:
        resume_text = state.get("resume_text", "")

        if not resume_text:
            raise ValueError("No resume text found in state")

        print(f"📝 Resume text length: {len(resume_text)} characters")

        # Step 1: Split into chunks
        chunks = chunk_text(
            text=resume_text,
            chunk_size=500,
            overlap=50
        )

        # Step 2: Store in ChromaDB
        store_chunks(chunks, collection_name="resume")

        # Step 3: Test query to verify RAG works
        test_results = query_chunks(
            query="skills and technical experience",
            collection_name="resume",
            n_results=3
        )

        print(f"\n🔍 RAG test query results:")
        for i, chunk in enumerate(test_results, 1):
            print(f"   Chunk {i}: {chunk[:100]}...")

        # Step 4: Write to state
        return {
            **state,
            "resume_chunks": chunks,
            "error_message": None
        }

    except Exception as e:
        print(f"❌ Resume Parser error: {e}")
        return {
            **state,
            "resume_chunks": [],
            "error_message": str(e)
        }


def load_resume_from_pdf(pdf_path: str) -> str:
    """
    Helper function — loads PDF and returns text.
    Used by the Streamlit UI to get resume_text before passing to state.
    """
    return load_pdf(pdf_path)