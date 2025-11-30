# rag/embed_store.py
# Optional module - not required if consumer handles storing
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import json

FAISS_INDEX = "faiss_index"
TEXT_STORE = "text_store.json"

model = SentenceTransformer("all-MiniLM-L6-v2")
