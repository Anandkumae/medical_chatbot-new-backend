from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import logging
from dotenv import load_dotenv
from vector_db import vector_db
from document_routes import router as document_router
from assessment_routes import router as assessment_router
from translation import translation_service
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Medical Chatbot API", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: Optional[str] = 'en'  # Language preference: 'en', 'hi', 'mr'

class ChatResponse(BaseModel):
    choices: list
    session_id: Optional[str] = None
    language: Optional[str] = 'en'

@app.get("/")
def root():
    return {"message": "Medical Chatbot API with Guided Assessment"}

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
    
    # Translate user message to English for processing if needed
    processed_message = req.message
    if req.language and req.language != 'en':
        try:
            # For now, we'll process in English and translate the response
            # In a production system, you might want to translate the input too
            logger.info(f"Processing message in language: {req.language}")
        except Exception as e:
            logger.error(f"Translation error: {e}")
    
    prompt = f"""
You are a medical assistant AI. Use the following medical information to help answer the user's symptoms, but always prioritize safety and recommend professional medical care when appropriate.

Medical Context:
{context}

User Symptoms: {processed_message}

Instructions:
1. Analyze the symptoms based on the provided medical context
2. Provide possible causes based on the information
3. Suggest precautions the user can take
4. Recommend whether to see a doctor (always recommend professional medical care for serious symptoms)
5. Include a clear disclaimer that this is not medical advice
6. Use simple, clear language that's easy to understand

Response Format:
- Possible Causes: [list based on context]
- Precautions: [list of safe measures]
- When to See a Doctor: [clear guidance]
- Disclaimer: This AI assistant provides general information and is not a substitute for professional medical care. Always consult with a qualified healthcare provider for medical concerns.
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
        
        if response.status_code == 200:
            result = response.json()
            
            # Translate response if needed
            if req.language and req.language != 'en':
                try:
                    translated_content = translation_service.translate_text(
                        result['choices'][0]['message']['content'], 
                        req.language
                    )
                    result['choices'][0]['message']['content'] = translated_content
                    logger.info(f"Response translated to {req.language}")
                except Exception as e:
                    logger.error(f"Translation failed: {e}")
                    # Keep original English response if translation fails
            
            # Add language info to response
            result['language'] = req.language
            return result
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return {"error": "Failed to get response from AI service"}
            
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {e}")
        return {"error": "Failed to connect to AI service"}

# Include routers
app.include_router(document_router, prefix="/documents")
app.include_router(assessment_router)

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
