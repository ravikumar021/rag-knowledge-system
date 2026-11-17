# Knowledge retrieval reference system

A runnable, offline retrieval baseline for a future RAG application. It indexes UTF-8 documents in SQLite, ranks chunks using BM25-style lexical scoring, and returns source-cited evidence through a local HTTP API. It does **not** currently generate LLM answers or perform semantic vector search.

## Run in two minutes

Requires Python 3.11 or newer; no packages, API key, Docker or paid service required.

```sh
python -m app.ingest examples/payments.txt
python -m app.ingest examples/search.txt
python -m app.main
```

In a second terminal:

```sh
curl 'http://127.0.0.1:8000/ask?q=payment%20retries&k=2'
python -m unittest discover -s tests -v
```

The JSON response contains `mode`, `status`, and `evidence`. Each evidence item includes `source`, `chunk`, `text`, and a ranking `score`. Scores are not probabilities or confidence estimates. No matching terms returns `no_evidence` with an empty list.

## Design decisions

- **Repeatable ingestion:** replacing a document deletes old chunks and inserts new ones in a single SQLite transaction. A failed or empty replacement preserves the old document.
- **Source provenance:** every chunk retains its filename and zero-based ordinal. Filenames are document IDs; files with the same name replace one another.
- **Bounded retrieval:** the API limits query length and top-k. Deterministic tie-breaking supports reproducible tests.
- **Offline baseline:** a working lexical baseline provides a comparison point before adding embeddings and an LLM. Search currently scans all chunks; it targets small demonstration corpora.
- **No unsupported results:** no production throughput, adoption, or business outcome has been measured for this project.

## Architecture

```text
UTF-8 file -> overlapping chunks -> SQLite
Question -> lexical scoring -> top-k evidence + source references -> HTTP JSON
```

## Tests

The suite checks ranking, source attribution, empty results, input validation, persistence, atomic document replacement, stale-chunk removal, and HTTP behavior using a temporary database and ephemeral local server.

## Scope and next steps

This is a portfolio prototype, not a production knowledge service. It has no authentication, tenant isolation, embeddings, LLM integration, or document access controls. The server binds to localhost only. Do not expose it on the internet or ingest private employer/client documents.

Next: introduce a retriever interface and compare a vector implementation on a labeled question set; add authorization before retrieval; only then add generation with citation and abstention evaluation. The previous LangChain scaffolding is retained in Git history, but was not a complete tested implementation.

## Development disclosure

This upgrade was prepared with AI coding assistance. Review the implementation and run the tests before presenting it in an interview. It is a new portfolio exercise, not evidence of prior production employment work.
