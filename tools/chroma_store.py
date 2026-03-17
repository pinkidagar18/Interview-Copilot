# tools/chroma_store.py
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
import hashlib

# Load embedding model once (not every function call)
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding model ready")

# Create persistent ChromaDB client
# persistent_directory means data survives between runs
chroma_client = chromadb.PersistentClient(path="./chroma_db")


def get_or_create_collection(collection_name: str):
    """Get existing collection or create new one."""
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # cosine similarity for text
    )


def store_chunks(chunks: List[str], collection_name: str = "resume") -> None:
    """
    Embeds text chunks and stores them in ChromaDB.
    Each chunk gets a unique ID based on its content.
    """
    collection = get_or_create_collection(collection_name)

    # Delete existing docs to avoid duplicates on re-run
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        print(f"🗑 Cleared {len(existing['ids'])} old chunks")

    # Generate embeddings for all chunks at once (faster than one by one)
    embeddings = embedding_model.encode(chunks).tolist()

    # Create unique IDs using content hash
    ids = [hashlib.md5(chunk.encode()).hexdigest()[:12] for chunk in chunks]

    # Store in ChromaDB
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )
    print(f"✅ Stored {len(chunks)} chunks in ChromaDB collection: '{collection_name}'")


def query_chunks(query: str, collection_name: str = "resume", n_results: int = 5) -> List[str]:
    """
    Semantically searches ChromaDB and returns most relevant chunks.
    
    n_results=5 means return top 5 most relevant chunks.
    """
    collection = get_or_create_collection(collection_name)

    # Check collection has data
    if collection.count() == 0:
        print("⚠ Collection is empty — no chunks to query")
        return []

    # Embed the query and search
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )

    chunks = results["documents"][0]
    print(f"✅ Query returned {len(chunks)} relevant chunks")
    return chunks