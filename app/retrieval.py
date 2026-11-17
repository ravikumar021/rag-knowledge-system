"""Persistent, offline lexical retrieval baseline. No model or network required."""
import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass

@dataclass(frozen=True)
class Hit:
    source: str
    chunk: int
    text: str
    score: float


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def chunks(text, size=180, overlap=30):
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Require size > overlap >= 0")
    words = text.split()
    for start in range(0, len(words), size - overlap):
        yield " ".join(words[start:start + size])
        if start + size >= len(words):
            break


class Index:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS chunks (source TEXT NOT NULL, ordinal INTEGER NOT NULL, text TEXT NOT NULL, PRIMARY KEY(source, ordinal))")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def ingest(self, source, text, size=180, overlap=30):
        if not isinstance(source, str) or not source.strip():
            raise ValueError("Source must be nonempty")
        parts = list(chunks(text, size, overlap))
        if not parts:
            raise ValueError("Document must be nonempty")
        # Replace all chunks atomically, removing stale chunks on re-ingestion.
        with self.connect() as db:
            db.execute("DELETE FROM chunks WHERE source=?", (source,))
            db.executemany("INSERT INTO chunks VALUES (?, ?, ?)", [(source, i, t) for i, t in enumerate(parts)])
        return len(parts)

    def search(self, query, k=3):
        if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= 20:
            raise ValueError("k must be an integer between 1 and 20")
        terms = set(tokens(query))
        if not terms:
            return []
        with self.connect() as db:
            rows = db.execute("SELECT source, ordinal, text FROM chunks ORDER BY source, ordinal").fetchall()
        bags = [Counter(tokens(row[2])) for row in rows]
        n = len(rows)
        if not n:
            return []
        avg = sum(sum(b.values()) for b in bags) / n or 1
        df = {term: sum(term in b for b in bags) for term in terms}
        ranked = []
        for row, bag in zip(rows, bags):
            length = sum(bag.values())
            score = 0.0
            for term in terms:
                freq = bag[term]
                if freq:
                    idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                    score += idf * (freq * 2.2) / (freq + 1.2 * (0.25 + 0.75 * length / avg))
            if score > 0:
                ranked.append(Hit(*row, score))
        return sorted(ranked, key=lambda h: (-h.score, h.source, h.chunk))[:k]
