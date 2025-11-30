# app.py
import streamlit as st
from rag.rag_search import query_rag
from sentence_transformers import SentenceTransformer
import os
import json
import faiss

st.title("Real-Time RAG + GenAI Assistant")
st.write("Ask questions about Futurama characters!")

# Initialize embedding model (reuse same as consumer/rag)
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load FAISS index and text DB (same as your consumer/rag setup)
RAG_DIR = os.path.join(os.path.dirname(__file__), "rag")
FAISS_INDEX_FILE = os.path.join(RAG_DIR, "faiss_index.idx")
TEXT_STORE_PATH = os.path.join(RAG_DIR, "text_store.json")

# Load FAISS index
index = faiss.read_index(FAISS_INDEX_FILE)

# Load text DB
with open(TEXT_STORE_PATH, "r", encoding="utf-8") as f:
    text_db = json.load(f)

def simple_similarity_search(query, k=3):
    q_emb = embed_model.encode(query).astype("float32")
    q_emb = q_emb.reshape(1, -1)
    D, I = index.search(q_emb, k)
    retrieved = [text_db[i] for i in I[0] if i < len(text_db)]
    return retrieved

# User input
query = st.text_input("Your question:")

if st.button("Get Answer") and query:
    try:
        # 1️Show retrieved context chunks
        retrieved_chunks = simple_similarity_search(query, k=3)
        st.write(" Retrieved context chunks:", retrieved_chunks)

        # 2️Call RAG + GenAI
        answer = query_rag(query, k=3)
        st.success(" Answer: " + answer)
    except Exception as e:
        st.error(f"Error: {e}")
