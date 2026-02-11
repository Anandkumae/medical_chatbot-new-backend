from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from vector_db import vector_db
import logging
from document_routes import router as document_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Medical Chatbot API", version="1.0.0")

# Include document routes
app.include_router(document_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Medical Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat")
def chat(req: ChatRequest):
    if not OPENROUTER_API_KEY:
        return {"error": "OpenRouter API key not configured"}
    
    # Retrieve relevant medical information from vector database
    try:
        relevant_docs = vector_db.search(req.message, k=3)
        context = "\n\n".join([doc["text"] for doc in relevant_docs])
    except Exception as e:
        logger.error(f"Error searching vector database: {e}")
        context = "No specific medical information found."
    
    prompt = f"""
You are a medical assistant AI. Use the following medical information to help answer the user's symptoms, but always prioritize safety and recommend professional medical care when appropriate.

Medical Context:
{context}

User Symptoms: {req.message}

Instructions:
1. Analyze the symptoms based on the provided medical context
2. Provide possible causes based on the information
3. Suggest precautions the user can take
4. Recommend whether to see a doctor (always recommend professional medical care for serious symptoms)
5. Include a clear disclaimer that this is not medical advice

Response Format:
- **Possible Causes:** [list based on context]
- **Precautions:** [list of safe measures]
- **When to See a Doctor:** [clear guidance]
- **Disclaimer:** This AI assistant provides general information and is not a substitute for professional medical care. Always consult with a qualified healthcare provider for medical concerns.
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error calling OpenRouter API: {e}")
        return {"error": f"Failed to get response from AI: {str(e)}"}

# New endpoints for document management
@app.post("/documents/upload")
async def upload_document(text: str, metadata: dict = None):
    """Upload a new document to the vector database."""
    try:
        if metadata is None:
            metadata = {"source": "user_upload"}
        
        vector_db.add_documents([text], [metadata])
        vector_db.save("data/vector_db/medical_db")
        
        return {"message": "Document uploaded successfully", "doc_count": len(vector_db.documents)}
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return {"error": f"Failed to upload document: {str(e)}"}

@app.get("/documents/search")
async def search_documents(query: str, k: int = 5):
    """Search documents in the vector database."""
    try:
        results = vector_db.search(query, k)
        return {"results": results, "query": query}
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return {"error": f"Failed to search documents: {str(e)}"}

@app.get("/vector-db/stats")
async def get_vector_db_stats():
    """Get vector database statistics."""
    try:
        stats = vector_db.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting vector DB stats: {e}")
        return {"error": f"Failed to get stats: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
