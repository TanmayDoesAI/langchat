# app.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_search import QdrantSearch
from langchain_groq import ChatGroq
from nomic_embeddings import EmbeddingsModel

load_dotenv()

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

os.environ["TOKENIZERS_PARALLELISM"] = "FALSE"

# Initialize FastAPI app
app = FastAPI()

# Allow CORS for frontend on Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend URL for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global variables
collection_names = ["docs_v1_2", "docs_v2_2", "docs_v3_2"]
limit = 5
llm = ChatGroq(model="mixtral-8x7b-32768")
embeddings = EmbeddingsModel()
search = QdrantSearch(
    qdrant_url=os.environ["QDRANT_CLOUD_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
    embeddings=embeddings
)

# Define request and response models
class QueryRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sources: list

# API endpoint to handle user queries
@app.post("/api/chat", response_model=AnswerResponse)
async def chat_endpoint(request: QueryRequest):
    query = request.question.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Step 1: Retrieve relevant documents from Qdrant
    retrieved_docs = search.query_multiple_collections(query, collection_names, limit)

    # Step 2: Prepare the context from retrieved documents
    context = "\n".join([doc['text'] for doc in retrieved_docs])

    # Step 3: Construct the prompt with context and question
    prompt = (
        "You are LangAssist, a knowledgeable assistant for the LangChain Python Library. "
        "Given the following context from the documentation, provide a helpful answer to the user's question.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ).format(context=context, question=query)

    # Step 4: Generate an answer using the language model
    try:
        answer = llm.invoke(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Prepare sources
    sources = [
        {
            "source": doc['source'],
            "text": doc['text']
        } for doc in retrieved_docs
    ]

    # Step 5: Return the answer and sources
    # return AnswerResponse(answer=answer.strip(), sources=sources)
    return AnswerResponse(answer=answer.content.strip(), sources=sources)

