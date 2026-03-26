from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import PGVector

loader = TextLoader("data/docs.txt")
docs = loader.load()

db = PGVector.from_documents(
    docs,
    OpenAIEmbeddings(),
    connection_string="postgresql://user:pass@localhost:5432/rag"
)
