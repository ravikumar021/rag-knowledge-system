"""Ingest a local UTF-8 text file; importing this module performs no work."""
import argparse
from pathlib import Path
from app.retrieval import Index

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--db", default="index.sqlite3")
    args = parser.parse_args()
    count = Index(args.db).ingest(args.file.name, args.file.read_text(encoding="utf-8"))
    print(f"Indexed {count} chunks from {args.file.name}")

if __name__ == "__main__":
    main()
