"""Local-only HTTP demo. No authentication: do not expose publicly."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from app.query import ask_question

def handler(db_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/health":
                code, body = 200, {"status": "ok"}
            elif url.path == "/ask":
                try:
                    params = parse_qs(url.query)
                    body = ask_question(params.get("q", [""])[0], db_path, int(params.get("k", ["3"])[0]))
                    code = 200
                except ValueError as exc:
                    code, body = 400, {"error": str(exc)}
                except Exception:
                    code, body = 500, {"error": "Internal retrieval error"}
            else:
                code, body = 404, {"error": "Not found"}
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    return Handler

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="index.sqlite3")
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), handler(args.db)).serve_forever()

if __name__ == "__main__":
    main()
