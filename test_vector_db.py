#!/usr/bin/env python3
"""
Test script for vector database functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vector_db import vector_db, VectorDatabase

def test_vector_database():
    """Test basic vector database operations."""
    print("🔍 Testing Vector Database...")
    
    # Test 1: Check if vector database is initialized
    print(f"✅ Vector DB initialized with {len(vector_db.documents)} documents")
    
    # Test 2: Search for medical information
    query = "headache and fever symptoms"
    results = vector_db.search(query, k=3)
    
    print(f"\n🔍 Search results for: '{query}'")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Similarity Score: {result['similarity_score']:.3f}")
        print(f"   Text: {result['text'][:100]}...")
        print(f"   Source: {result['metadata']}")
    
    # Test 3: Get database stats
    stats = vector_db.get_stats()
    print(f"\n📊 Database Stats: {stats}")
    
    # Test 4: Add a new document
    test_doc = "Migraine is a neurological condition characterized by intense headaches, often accompanied by nausea and sensitivity to light."
    vector_db.add_documents([test_doc], [{"source": "test", "type": "medical_info"}])
    
    # Search again to see if new document appears
    new_results = vector_db.search("migraine", k=3)
    print(f"\n🔍 Search results after adding migraine info:")
    for i, result in enumerate(new_results, 1):
        print(f"{i}. Score: {result['similarity_score']:.3f} - {result['text'][:80]}...")
    
    print("\n✅ Vector database tests completed successfully!")

if __name__ == "__main__":
    test_vector_database()
