from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import PGVector
from langchain.embeddings import OpenAIEmbeddings

def ask_question(query):
    db = PGVector(
        connection_string="postgresql://user:pass@localhost:5432/rag",
        embedding_function=OpenAIEmbeddings()
    )

    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(),
        retriever=db.as_retriever()
    )

    return qa.run(query)
