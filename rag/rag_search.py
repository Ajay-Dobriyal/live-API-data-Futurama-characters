# rag/rag_search.py
import os
import json
import subprocess
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAG_DIR = os.path.join(BASE_DIR, "rag")
FAISS_INDEX_DIR = os.path.join(RAG_DIR, "faiss_index")
TEXT_STORE_PATH = os.path.join(RAG_DIR, "text_store.json")

# Path to Ollama executable (Windows)
OLLAMA_PATH = r"C:\Users\ajayd\AppData\Local\Programs\Ollama\ollama.exe"  # <- change if needed

# Load embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load FAISS index and text DB
faiss_index_file = os.path.join(RAG_DIR, "faiss_index.idx")
if not os.path.exists(faiss_index_file):
    raise FileNotFoundError("FAISS index not found. Run consumer first.")

index = faiss.read_index(faiss_index_file)

# Load FAISS index
index_file = os.path.join(FAISS_INDEX_DIR, "index.faiss")
vector_store = None
try:
    import pickle
    with open(os.path.join(FAISS_INDEX_DIR, "faiss.pkl"), "rb") as f:
        vector_store = pickle.load(f)
except Exception:
    pass  # fallback if FAISS index saved differently

with open(TEXT_STORE_PATH, "r", encoding="utf-8") as f:
    text_db = json.load(f)

def build_prompt(context_chunks, question):
    context = "\n\n".join([f"- {c}" for c in context_chunks])
    prompt = f"""You are a helpful assistant. Use only the context below to answer concisely.
If the answer is not present in the context, reply: "Not found in the provided data."

Context:
{context}

Question:
{question}

Answer:"""
    return prompt

def query_rag(question, k=3):
    # Embed query
    q_emb = embed_model.encode(question).astype("float32")
    q_emb = np.array([q_emb])

    # FAISS search directly
    D, I = index.search(q_emb, k)  # D=distances, I=indices
    retrieved = [text_db[i] for i in I[0] if i < len(text_db)]

    # Build RAG prompt
    prompt = build_prompt(retrieved, question)

    # Call Ollama
    try:
        proc = subprocess.run(
            [OLLAMA_PATH, "run", "mistral", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",  # force UTF-8 decoding
            errors="replace",  # replace invalid characters
            check=False
        )
        output = proc.stdout.strip() or proc.stderr.strip()

    except FileNotFoundError:
        raise RuntimeError(f"Ollama not found at {OLLAMA_PATH}. Please check path or install Ollama.")
    
    return output
