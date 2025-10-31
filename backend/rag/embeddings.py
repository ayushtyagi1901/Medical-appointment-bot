import os
from typing import List
import google.generativeai as genai

# Lazy initialization of Gemini client
_initialized = False

def _initialize_client():
    """Initialize Gemini client."""
    global _initialized
    if not _initialized:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        _initialized = True


def create_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for a list of texts using Gemini's embedding model.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    try:
        _initialize_client()
        
        embeddings = []
        for text in texts:
            # Use Gemini's embed_content method
            result = genai.embed_content(
                model="text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        
        return embeddings
    except Exception as e:
        raise Exception(f"Error creating embeddings: {str(e)}")


def create_single_embedding(text: str) -> List[float]:
    """
    Create an embedding for a single text.
    
    Args:
        text: Text string to embed
        
    Returns:
        Embedding vector
    """
    embeddings = create_embeddings([text])
    return embeddings[0]

