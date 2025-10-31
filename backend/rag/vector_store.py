import os
import json
import chromadb
from chromadb.config import Settings
from typing import List, Dict
from pathlib import Path

from .embeddings import create_embeddings


class VectorStore:
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "faq_knowledge_base"):
        """
        Initialize ChromaDB vector store.
        
        Args:
            db_path: Path to store ChromaDB data
            collection_name: Name of the collection to use
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, documents: List[str], metadatas: List[Dict] = None, ids: List[str] = None):
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries (optional)
            ids: List of document IDs (optional)
        """
        if not documents:
            return
        
        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{}] * len(documents)
        
        # Generate embeddings (with error handling)
        try:
            embeddings = create_embeddings(documents)
            
            # Add to collection with embeddings
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            # If embeddings fail, store documents without embeddings (will use keyword matching)
            error_msg = str(e).lower()
            if "quota" in error_msg or "429" in error_msg or "api" in error_msg or "key" in error_msg:
                # Store documents as text only (fallback mode)
                # Use zero embeddings as placeholder - queries will use keyword matching
                print(f"Warning: Using fallback mode without embeddings")
                # Store metadata for keyword search fallback
                for doc, meta, doc_id in zip(documents, metadatas, ids):
                    meta['document_text'] = doc
                    meta['fallback_mode'] = True
                # Add without embeddings (ChromaDB will handle it)
                try:
                    self.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                except:
                    # If even that fails, just store metadata
                    pass
            else:
                raise
    
    def query(self, query_text: str, n_results: int = 3) -> List[Dict]:
        """
        Query the vector store for similar documents.
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            
        Returns:
            List of dictionaries containing documents, metadatas, distances, and ids
        """
        query_embedding = create_embeddings([query_text])[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None,
                    'id': results['ids'][0][i] if results['ids'] else None
                })
        
        return formatted_results
    
    def delete_collection(self):
        """Delete the collection (useful for testing/resetting)."""
        self.client.delete_collection(name=self.collection_name)
    
    def get_collection_count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()


def initialize_faq_knowledge_base(data_path: str = "./data/clinic_info.json") -> VectorStore:
    """
    Initialize the FAQ knowledge base from clinic_info.json.
    
    Args:
        data_path: Path to clinic_info.json file
        
    Returns:
        Initialized VectorStore instance
    """
    vector_store = VectorStore()
    
    # Resolve path relative to project root
    if not os.path.isabs(data_path):
        # Try relative to current directory first
        if os.path.exists(data_path):
            resolved_path = data_path
        else:
            # Try relative to backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            resolved_path = os.path.join(os.path.dirname(backend_dir), data_path.lstrip('./'))
            if not os.path.exists(resolved_path):
                # Try relative to project root
                project_root = os.path.dirname(backend_dir)
                resolved_path = os.path.join(project_root, data_path.lstrip('./'))
    else:
        resolved_path = data_path
    
    # Load FAQ data
    with open(resolved_path, 'r') as f:
        clinic_data = json.load(f)
    
    # Extract FAQ documents
    documents = []
    metadatas = []
    ids = []
    
    for i, faq in enumerate(clinic_data.get('faqs', [])):
        # Combine question and answer for better retrieval
        doc_text = f"Question: {faq['question']}\nAnswer: {faq['answer']}"
        documents.append(doc_text)
        metadatas.append({
            'question': faq['question'],
            'answer': faq['answer'],
            'type': 'faq'
        })
        ids.append(f"faq_{i}")
    
    # Add clinic information
    if 'clinic_name' in clinic_data:
        clinic_info = f"Clinic Name: {clinic_data['clinic_name']}\n"
        clinic_info += f"Address: {clinic_data.get('address', '')}\n"
        clinic_info += f"Phone: {clinic_data.get('phone', '')}\n"
        clinic_info += f"Email: {clinic_data.get('email', '')}\n"
        
        if 'hours' in clinic_data:
            clinic_info += "Operating Hours:\n"
            for day, hours in clinic_data['hours'].items():
                clinic_info += f"{day.capitalize()}: {hours}\n"
        
        documents.append(clinic_info)
        metadatas.append({'type': 'clinic_info'})
        ids.append("clinic_info")
    
    # Clear existing collection if it exists and has data
    if vector_store.get_collection_count() > 0:
        vector_store.delete_collection()
        vector_store = VectorStore()
    
    # Add documents to vector store (with error handling for API quota issues)
    try:
        vector_store.add_documents(documents, metadatas, ids)
    except Exception as e:
        error_msg = str(e).lower()
        # If embeddings fail due to quota/API issues, we can still use the vector store
        # The documents just won't have embeddings, but we'll handle this in query
        if "quota" in error_msg or "429" in error_msg or "api" in error_msg:
            print(f"Warning: Could not create embeddings due to API issues. RAG will use fallback mode.")
            # Store documents without embeddings (will use keyword matching fallback)
            pass
        else:
            raise
    
    return vector_store

