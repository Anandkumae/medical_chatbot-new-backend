import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import PyPDF2
from docx import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector database with sentence transformer model."""
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []  # Store document metadata
        self.embeddings = []  # Store embeddings
        
    def add_documents(self, texts: List[str], metadata: List[Dict] = None) -> None:
        """Add documents to the vector database."""
        if metadata is None:
            metadata = [{"source": f"doc_{i}"} for i in range(len(texts))]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents and embeddings
        for i, (text, meta) in enumerate(zip(texts, metadata)):
            self.documents.append({
                'text': text,
                'metadata': meta,
                'id': len(self.documents) + i
            })
        
        logger.info(f"Added {len(texts)} documents to vector database")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar documents."""
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['similarity_score'] = float(1 / (1 + dist))  # Convert distance to similarity
                results.append(doc)
        
        return results
    
    def save(self, file_path: str) -> None:
        """Save the vector database to disk."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{file_path}.index")
        
        # Save documents
        with open(f"{file_path}.pkl", 'wb') as f:
            pickle.dump(self.documents, f)
        
        logger.info(f"Vector database saved to {file_path}")
    
    def load(self, file_path: str) -> None:
        """Load the vector database from disk."""
        # Load FAISS index
        self.index = faiss.read_index(f"{file_path}.index")
        
        # Load documents
        with open(f"{file_path}.pkl", 'rb') as f:
            self.documents = pickle.load(f)
        
        logger.info(f"Vector database loaded from {file_path}")
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        return {
            'total_documents': len(self.documents),
            'embedding_dimension': self.dimension,
            'index_type': 'IndexFlatL2'
        }

class DocumentProcessor:
    """Process different document types for vector database."""
    
    @staticmethod
    def process_pdf(file_path: str) -> List[str]:
        """Extract text from PDF file."""
        texts = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        texts.append(f"Page {page_num + 1}: {text}")
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
        return texts
    
    @staticmethod
    def process_docx(file_path: str) -> List[str]:
        """Extract text from DOCX file."""
        texts = []
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    texts.append(paragraph.text)
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
        return texts
    
    @staticmethod
    def process_txt(file_path: str) -> List[str]:
        """Extract text from TXT file."""
        texts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Split by paragraphs or chunks
                paragraphs = content.split('\n\n')
                texts = [p.strip() for p in paragraphs if p.strip()]
        except Exception as e:
            logger.error(f"Error processing TXT {file_path}: {e}")
        return texts

# Initialize global vector database
vector_db = VectorDatabase()

def initialize_with_medical_data():
    """Initialize with some basic medical information."""
    medical_texts = [
        "Common cold symptoms include sore throat, runny nose, cough, congestion, and mild body aches. Usually resolves within 7-10 days.",
        "Influenza (flu) symptoms include fever, chills, muscle aches, cough, congestion, headaches, and fatigue. Can be serious for high-risk groups.",
        "COVID-19 symptoms include fever, dry cough, fatigue, loss of taste or smell, and difficulty breathing. Seek medical attention for severe symptoms.",
        "High blood pressure (hypertension) often has no symptoms but can cause heart disease, stroke, and kidney problems if untreated.",
        "Type 2 diabetes symptoms include increased thirst, frequent urination, hunger, fatigue, and blurred vision. Requires medical management.",
        "Chest pain can be a sign of heart attack and requires immediate medical attention, especially if accompanied by shortness of breath or sweating.",
        "Headaches can range from mild to severe. Migraines often include nausea, light sensitivity, and visual disturbances.",
        "Back pain is common and usually improves with rest and gentle exercise. Seek medical care if severe or persistent.",
        "Allergic reactions can cause hives, itching, swelling, and difficulty breathing. Severe reactions require emergency care.",
        "Asthma causes wheezing, shortness of breath, chest tightness, and coughing. Use inhaler as prescribed and seek care for severe attacks."
    ]
    
    metadata = [
        {"source": "general_medical_knowledge", "category": "respiratory"},
        {"source": "general_medical_knowledge", "category": "infectious_disease"},
        {"source": "general_medical_knowledge", "category": "infectious_disease"},
        {"source": "general_medical_knowledge", "category": "cardiovascular"},
        {"source": "general_medical_knowledge", "category": "endocrine"},
        {"source": "general_medical_knowledge", "category": "cardiovascular"},
        {"source": "general_medical_knowledge", "category": "neurological"},
        {"source": "general_medical_knowledge", "category": "musculoskeletal"},
        {"source": "general_medical_knowledge", "category": "immune"},
        {"source": "general_medical_knowledge", "category": "respiratory"}
    ]
    
    vector_db.add_documents(medical_texts, metadata)
    logger.info("Initialized vector database with basic medical knowledge")

# Initialize on import
try:
    vector_db.load("data/vector_db/medical_db")
    logger.info("Loaded existing vector database")
except:
    logger.info("Creating new vector database with medical data")
    initialize_with_medical_data()
    vector_db.save("data/vector_db/medical_db")
