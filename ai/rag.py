import csv
from pathlib import Path

import numpy as np
from llm import ask_llm   # imported first, it also applies the certificate fix
from fastembed import TextEmbedding

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "documents"
MIN_SCORE = 0.55   # starting guess, we will tune it from the test output
TOP_K = 3


def load_chunks():
    chunks = []
    for path in sorted(DOCS.glob("*_sop.txt")):
        text = path.read_text(encoding="utf-8").strip()
        chunks.append({"id": path.stem, "source": path.name, "text": text})
    with open(DOCS / "business_rules.csv", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            text = f"{row['rule_name']}: {row['rule_text']}"
            chunks.append({"id": row["rule_id"], "source": "business_rules.csv", "text": text})
    return chunks


CHUNKS = load_chunks()
MODEL = TextEmbedding()


def embed(texts):
    vecs = np.array(list(MODEL.embed(texts)), dtype="float32")
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


MATRIX = embed([c["text"] for c in CHUNKS])


def retrieve(question, k=TOP_K, min_score=MIN_SCORE):
    """Returns [(score, chunk), ...] for the chunks closest in meaning to the question."""
    q = embed([question])[0]
    scores = MATRIX @ q
    order = np.argsort(-scores)[:k]
    return [(float(scores[i]), CHUNKS[i]) for i in order if scores[i] >= min_score]


NOT_FOUND = "I couldn't find that in the available company documents."

RAG_SYSTEM = (
    "You answer questions about ApexRoute Logistics using ONLY the numbered excerpts you are given.\n"
    "- Do not use outside knowledge and do not guess.\n"
    "- If the excerpts do not answer the question, reply with exactly: NOT_FOUND\n"
    "- If the excerpts only touch a related topic but do not directly answer the exact question asked, reply with exactly: NOT_FOUND\n"
    "- Say which document or rule the answer comes from, by name.\n"
    "- Be short and direct. For procedures, keep the steps in order."
)


def answer_from_docs(question):
    hits = retrieve(question)
    if not hits:
        # nothing relevant found, so don't even call the LLM
        return {"answer": NOT_FOUND, "type": "rag", "sources": []}
    context = "\n\n".join(
        f"[{i}] ({c['source']}, {c['id']})\n{c['text']}" for i, (s, c) in enumerate(hits, 1))
    reply = ask_llm(RAG_SYSTEM, f"Question: {question}\n\nExcerpts:\n{context}")
    if "NOT_FOUND" in reply:
        return {"answer": NOT_FOUND, "type": "rag", "sources": []}
    sources = [{"document": c["source"], "id": c["id"], "score": round(s, 2)} for s, c in hits]
    return {"answer": reply, "type": "rag", "sources": sources}


if __name__ == "__main__":
    import time
    tests = [
        "What are the steps to process a refund?",
        "When does a refund need Finance Manager approval?",
        "What happens when a shipment is delayed more than 2 days?",
        "How do we handle purchase orders?",
        "How do I get my money back as a customer?",
        "Who signs off on big spending?",
        "How many days of leave do employees get?",
        "What is the capital of France?",
    ]
    for q in tests:
        print("\nQ:", q)
        # min_score=0 shows the raw top scores, so we can pick a good cutoff
        print("top scores:", [(round(s, 2), c["id"]) for s, c in retrieve(q, min_score=0)])
        r = answer_from_docs(q)
        print("A:", r["answer"])
        time.sleep(2)
