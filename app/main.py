from fastapi import FastAPI
from app.query import ask_question

app = FastAPI()

@app.get("/ask")
def ask(q: str):
    return {"answer": ask_question(q)}
