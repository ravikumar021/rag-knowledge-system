"""Return cited evidence, not fabricated model-generated answers."""
from dataclasses import asdict
from app.retrieval import Index

def ask_question(query, db_path="index.sqlite3", k=3):
    if not isinstance(query, str) or not query.strip() or len(query) > 2000:
        raise ValueError("Query must contain 1–2000 characters")
    hits = Index(db_path).search(query, k)
    return {"mode": "retrieval_only", "status": "evidence_found" if hits else "no_evidence",
            "evidence": [asdict(hit) for hit in hits]}
