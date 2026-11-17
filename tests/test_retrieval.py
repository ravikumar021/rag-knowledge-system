import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from http.server import ThreadingHTTPServer
from app.retrieval import Index, chunks
from app.query import ask_question
from app.main import handler

class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "index.db"
        self.index = Index(self.path)
        self.index.ingest("payments", "payment retry idempotency payment")
        self.index.ingest("search", "document search retrieval")

    def test_ranking_and_sources(self):
        hits = self.index.search("payment retry")
        self.assertEqual(hits[0].source, "payments")
        self.assertEqual(hits[0].chunk, 0)
        self.assertGreater(hits[0].score, 0)

    def test_no_evidence(self):
        self.assertEqual(ask_question("unicorn", self.path)["status"], "no_evidence")

    def test_persistent(self):
        self.assertEqual(Index(self.path).search("retrieval")[0].source, "search")

    def test_replacement_removes_old_chunks(self):
        self.index.ingest("payments", "a b c d e f", size=3, overlap=1)
        self.index.ingest("payments", "new")
        self.assertEqual(self.index.search("payment"), [])
        with self.index.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM chunks WHERE source='payments'").fetchone()[0], 1)

    def test_empty_replacement_preserves_existing(self):
        with self.assertRaises(ValueError): self.index.ingest("payments", "")
        self.assertTrue(self.index.search("payment"))

    def test_overlap(self):
        self.assertEqual(list(chunks("a b c d e", 3, 1)), ["a b c", "c d e"])

    def test_invalid_chunk_options(self):
        for size, overlap in [(0,0),(3,3),(3,-1)]:
            with self.assertRaises(ValueError): list(chunks("x",size,overlap))

    def test_invalid_queries(self):
        for q in ["", " ", "x" * 2001, None]:
            with self.assertRaises(ValueError): ask_question(q,self.path)

    def test_invalid_k(self):
        for k in [0,21,-1,True,1.5]:
            with self.assertRaises(ValueError): self.index.search("payment",k)

    def test_sql_characters_are_data(self):
        self.index.ingest("'; DROP TABLE chunks; --", "special source")
        self.assertTrue(self.index.search("special"))
        self.assertTrue(self.index.search("payment"))

    def test_http(self):
        server = ThreadingHTTPServer(("127.0.0.1",0),handler(self.path))
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urlopen(base+"/ask?q=payment") as r:
                self.assertEqual(json.load(r)["evidence"][0]["source"],"payments")
            with self.assertRaises(HTTPError) as err: urlopen(base+"/ask")
            self.assertEqual(err.exception.code,400)
            err.exception.close()
        finally:
            server.shutdown();server.server_close();thread.join()

if __name__ == "__main__": unittest.main()
