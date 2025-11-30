# query/ask_rag.py
from rag.rag_search import query_rag

print("🧠 Ask the RAG assistant (type 'exit' to quit).")

while True:
    q = input("\nYour question: ").strip()
    if q.lower() in ("exit", "quit"):
        break
    try:
        ans = query_rag(q, k=3)
        print("\n🤖 Answer:\n", ans)
    except Exception as e:
        print("Error:", e)
