# consumer/consumer.py
import os
import json
import numpy as np
import faiss
from kafka import KafkaConsumer
from sentence_transformers import SentenceTransformer

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAG_DIR = os.path.join(BASE_DIR, "rag")
os.makedirs(RAG_DIR, exist_ok=True)
FAISS_INDEX_PATH = os.path.join(RAG_DIR, "faiss_index.idx")
TEXT_STORE_PATH = os.path.join(RAG_DIR, "text_store.json")

# Kafka
TOPIC = "live_news"
KAFKA_BOOTSTRAP = "localhost:9092"

print("🔁 Starting consumer...")

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    consumer_timeout_ms=1000
)

# Embedding model
print("🔄 Loading embedding model (sentence-transformers)...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load or init FAISS index
vector_store = None
if os.path.exists(FAISS_INDEX_PATH):
    try:
        vector_store = faiss.read_index(FAISS_INDEX_PATH)
        print("✅ Loaded existing FAISS index.")
    except Exception as e:
        print("⚠ Could not load FAISS index:", e)

# Load text store
if os.path.exists(TEXT_STORE_PATH):
    with open(TEXT_STORE_PATH, "r", encoding="utf-8") as f:
        text_db = json.load(f)
else:
    text_db = []

def save_text_db():
    with open(TEXT_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(text_db, f, ensure_ascii=False, indent=2)

print("📥 Listening for messages... (Ctrl+C to stop)")

try:
    for msg in consumer:
        payload = msg.value
        text = payload.get("text", "").strip()
        if not text:
            continue

        print("📌 Consumed:", text)

        # Simple chunking - split into 300-char pieces
        chunks = [text[i:i+300] for i in range(0, len(text), 300)]
        vectors = [embed_model.encode(c) for c in chunks]

        if vector_store is None:
            dim = len(vectors[0])
            vector_store = faiss.IndexFlatL2(dim)
            vector_store.add(np.array(vectors).astype("float32"))
            print("🆕 Created new FAISS index with first documents.")
        else:
            vector_store.add(np.array(vectors).astype("float32"))
            print("➕ Added documents to FAISS index.")

        # Save chunk texts to JSON to map back later
        text_db.extend(chunks)
        save_text_db()

        # persist FAISS index on disk
        faiss.write_index(vector_store, FAISS_INDEX_PATH)
        print("💾 FAISS saved.\n")

except KeyboardInterrupt:
    print("Stopping consumer...")

finally:
    consumer.close()
