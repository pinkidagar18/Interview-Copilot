# tools/pdf_loader.py
from pypdf import PdfReader
import os

def load_pdf(file_path: str) -> str:
    """
    Reads a PDF file and returns all text as a single string.
    Handles multiple pages automatically.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found at: {file_path}")

    reader = PdfReader(file_path)
    full_text = ""

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"

    if not full_text.strip():
        raise ValueError("PDF appears to be empty or unreadable")

    print(f"✅ PDF loaded: {len(reader.pages)} pages, {len(full_text)} characters")
    return full_text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Splits text into overlapping chunks.
    
    Why overlap? So that sentences at chunk boundaries don't lose context.
    Example: chunk_size=500 means each chunk is ~500 characters.
    overlap=50 means last 50 chars of chunk 1 appear at start of chunk 2.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Don't cut in the middle of a word
        if end < len(text):
            # Find the last space before the cut point
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap  # overlap with previous chunk

    print(f"✅ Text split into {len(chunks)} chunks")
    return chunks