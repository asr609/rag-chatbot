from fastapi import FastAPI, UploadFile, Form, Request
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import HuggingFacePipeline, HuggingFaceHub
from transformers import pipeline
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging 
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(level=logging.INFO)
def log_interaction(query, response):
    logging.info(f"Query: {query}\nResponse: {response}\n---")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = None

@app.post("/upload/")
async def upload_file(file: UploadFile):
    content = await file.read()
    with open(file.filename, "wb") as f:
        f.write(content)
    # Choose loader based on file extension
    if file.filename.lower().endswith(".pdf"):
        loader = PyPDFLoader(file.filename)
    else:
        loader = TextLoader(file.filename)
    documents = loader.load()
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    global vector_store
    vector_store = FAISS.from_documents(documents, embeddings)
    return {"status": "uploaded"}

# Load the pipeline once at startup
hf_pipeline = pipeline("text2text-generation", model="google/flan-t5-base")
llm = HuggingFacePipeline(pipeline=hf_pipeline)

@app.post("/chat/")
@limiter.limit("5/minute")
async def chat(request: Request, query: str = Form(...)):
    if not vector_store:
        return {"error": "No documents uploaded"}
    def is_query_safe(query: str) -> bool:
        blocked_keywords = ["kill", "bomb", "hate", "attack", "suicide"]
        return not any(word in query.lower() for word in blocked_keywords)
    if not is_query_safe(query):
        return {"response": "Sorry, your query violates our safety policy."}

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})  # Increase k for more context
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    output = qa_chain.invoke(query)
    result = output["result"]
    source_docs = output.get("source_documents", [])

    # If no relevant source documents, warn about possible hallucination
    if not source_docs or all(len(doc.page_content.strip()) == 0 for doc in source_docs):
        return {"response": "Sorry, I could not find relevant information in your documents. The answer may not be reliable."}

    # Output Guardrail
    def is_response_safe(text: str) -> bool:
        blocked_keywords = ["kill", "bomb", "hate", "attack", "suicide"]
        return not any(word in text.lower().split() for word in blocked_keywords)
    if not is_response_safe(result):
        return {"response": "Sorry, the response violates our safety policy. Please rephrase your query."}

    log_interaction(query, result)
    # Return sources for transparency
    sources = [doc.metadata.get("source", "") for doc in source_docs]
    return {
        "response": result,
        "sources": sources
    }

@app.get("/")
async def root():
    return {"message": "RAG API is running"}
