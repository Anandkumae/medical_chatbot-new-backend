from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import tempfile
from vector_db import vector_db, DocumentProcessor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a document file (PDF, DOCX, TXT)."""
    
    # Check file type
    allowed_extensions = ['.pdf', '.docx', '.txt']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Process the file based on its type
        if file_extension == '.pdf':
            texts = DocumentProcessor.process_pdf(tmp_file_path)
        elif file_extension == '.docx':
            texts = DocumentProcessor.process_docx(tmp_file_path)
        elif file_extension == '.txt':
            texts = DocumentProcessor.process_txt(tmp_file_path)
        
        if not texts:
            raise HTTPException(
                status_code=400, 
                detail="No text content found in the uploaded file"
            )
        
        # Add to vector database
        metadata = {
            "source": "file_upload",
            "filename": file.filename,
            "file_type": file_extension,
            "total_chunks": len(texts)
        }
        
        vector_db.add_documents(texts, [metadata] * len(texts))
        vector_db.save("data/vector_db/medical_db")
        
        return {
            "message": f"Successfully processed {file.filename}",
            "chunks_processed": len(texts),
            "total_documents": len(vector_db.documents)
        }
        
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_file_path)
        except:
            pass

@router.get("/list")
async def list_documents():
    """List all documents in the vector database."""
    try:
        documents = []
        for doc in vector_db.documents:
            documents.append({
                "id": doc["id"],
                "metadata": doc["metadata"],
                "text_preview": doc["text"][:100] + "..." if len(doc["text"]) > 100 else doc["text"]
            })
        
        return {
            "total_documents": len(documents),
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.delete("/clear")
async def clear_database():
    """Clear all documents from the vector database."""
    try:
        global vector_db
        from vector_db import VectorDatabase
        vector_db = VectorDatabase()
        vector_db.save("data/vector_db/medical_db")
        
        return {"message": "Vector database cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing database: {str(e)}")
