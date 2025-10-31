import os
from typing import List, Dict, Optional
import google.generativeai as genai

from .vector_store import VectorStore, initialize_faq_knowledge_base

# Lazy initialization of Gemini model
_model = None

def get_model():
    """Get or create Gemini model instance."""
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        model_name = os.getenv("LLM_MODEL", "gemini-flash-latest")
        # Remove 'models/' prefix if present, Gemini API adds it automatically
        if model_name.startswith("models/"):
            model_name = model_name.replace("models/", "")
        _model = genai.GenerativeModel(model_name)
    return _model

# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or initialize the vector store singleton."""
    global _vector_store
    if _vector_store is None:
        data_path = os.getenv("FAQ_DATA_PATH", "./data/clinic_info.json")
        _vector_store = initialize_faq_knowledge_base(data_path)
    return _vector_store


def retrieve_faq_context(query: str, top_k: int = 3) -> str:
    """
    Retrieve relevant FAQ context using RAG.
    
    Args:
        query: User query
        top_k: Number of top results to retrieve
        
    Returns:
        Formatted context string from retrieved FAQs
    """
    try:
        vector_store = get_vector_store()
        results = vector_store.query(query, n_results=top_k)
        
        if not results:
            return _keyword_fallback_search(query)
        
        context_parts = []
        for result in results:
            context_parts.append(result['document'])
        
        return "\n\n".join(context_parts)
    except Exception as e:
        # Fallback to keyword search if vector store fails
        return _keyword_fallback_search(query)


def _keyword_fallback_search(query: str) -> str:
    """Fallback keyword-based FAQ search when RAG is unavailable."""
    import json
    import os
    
    query_lower = query.lower()
    data_path = os.getenv("FAQ_DATA_PATH", "./data/clinic_info.json")
    
    # Resolve path
    if not os.path.isabs(data_path):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resolved_path = os.path.join(os.path.dirname(backend_dir), data_path.lstrip('./'))
        if not os.path.exists(resolved_path):
            project_root = os.path.dirname(backend_dir)
            resolved_path = os.path.join(project_root, data_path.lstrip('./'))
    else:
        resolved_path = data_path
    
    try:
        with open(resolved_path, 'r') as f:
            clinic_data = json.load(f)
        
        # Simple keyword matching
        best_matches = []
        for faq in clinic_data.get('faqs', []):
            question = faq.get('question', '').lower()
            answer = faq.get('answer', '')
            
            # Count keyword matches
            query_words = set(query_lower.split())
            question_words = set(question.split())
            matches = len(query_words.intersection(question_words))
            
            if matches > 0:
                best_matches.append((matches, f"Question: {faq['question']}\nAnswer: {answer}"))
        
        # Sort by match count and return top results
        best_matches.sort(reverse=True, key=lambda x: x[0])
        
        if best_matches:
            return "\n\n".join([match[1] for match in best_matches[:3]])
        else:
            return "No relevant information found."
    except Exception:
        return "No relevant information found."


def answer_faq_with_rag(user_query: str, conversation_history: List[Dict] = None) -> str:
    """
    Answer FAQ using RAG pipeline with Gemini.
    
    Args:
        user_query: User's question
        conversation_history: Previous conversation messages
        
    Returns:
        Answer to the user's question
    """
    # Retrieve relevant context
    context = retrieve_faq_context(user_query)
    
    # Build conversation history for context
    history_text = ""
    if conversation_history:
        recent_history = conversation_history[-3:]  # Last 3 messages for context
        history_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in recent_history
        ])
    
    # Construct prompt
    system_prompt = """You are a helpful assistant for HealthCare Plus Clinic. 
Answer the user's question based on the provided context from the clinic's FAQ database.
If the context doesn't contain enough information, politely let the user know and suggest they contact the clinic directly.
Be concise, friendly, and professional."""

    user_prompt = f"""Context from FAQ database:
{context}

{'Previous conversation:\n' + history_text if history_text else ''}

User question: {user_query}

Please provide a helpful answer based on the context provided."""

    try:
        model = get_model()
        
        # Convert to Gemini format
        conversation_text = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        
        # Generate response with Gemini
        response = model.generate_content(
            conversation_text,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 500,
            }
        )
        
        # Handle response - use parts accessor instead of text quick accessor
        # The text quick accessor only works for simple single-Part responses
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            # Check for safety ratings (blocked content)
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason in ['SAFETY', 'RECITATION']:
                # Safety filter blocked the response - use fallback
                print(f"Warning: Gemini safety filter blocked FAQ response (reason: {candidate.finish_reason})")
                raise Exception("Content was blocked by safety filters")
            
            # Extract text from parts (recommended way)
            if hasattr(candidate, 'content'):
                content = candidate.content
                # Check if content has parts attribute
                if hasattr(content, 'parts'):
                    # Check if parts exist and is not empty
                    try:
                        # Try direct iteration (works with RepeatedComposite)
                        text_parts = []
                        for part in content.parts:
                            # Check if part has text attribute and it's not None/empty
                            if hasattr(part, 'text'):
                                text_value = getattr(part, 'text', None)
                                if text_value:
                                    text_parts.append(str(text_value))
                        if text_parts:
                            return ' '.join(text_parts).strip()
                    except Exception as parts_error:
                        print(f"Debug: Error iterating parts: {parts_error}")
                        # Try list conversion as fallback
                        try:
                            parts_list = list(content.parts)
                            if parts_list:
                                text_parts = []
                                for part in parts_list:
                                    if hasattr(part, 'text'):
                                        text_value = getattr(part, 'text', None)
                                        if text_value:
                                            text_parts.append(str(text_value))
                                if text_parts:
                                    return ' '.join(text_parts).strip()
                        except Exception as list_error:
                            print(f"Debug: Error with list conversion: {list_error}")
                
                # Alternative: try direct text access on content
                if hasattr(content, 'text'):
                    text_value = getattr(content, 'text', None)
                    if text_value:
                        return str(text_value).strip()
        
        # Try the text quick accessor as fallback (may fail for complex responses)
        try:
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
        except ValueError:
            # text quick accessor failed, continue to check other methods
            pass
        
        # If no text found, check prompt_feedback for issues
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            feedback = response.prompt_feedback
            if hasattr(feedback, 'block_reason') and feedback.block_reason:
                print(f"Warning: FAQ prompt blocked (reason: {feedback.block_reason})")
                raise Exception(f"Prompt was blocked: {feedback.block_reason}")
        
        # If no text found, use fallback
        raise Exception("Gemini API returned response without text content")
    except Exception as e:
        error_msg = str(e)
        # Check for quota/rate limit errors (Gemini-specific)
        if any(keyword in error_msg.lower() for keyword in ["quota", "rate limit", "429", "resource_exhausted", "permission_denied"]):
            # Fallback: try to answer from context without LLM
            if context and context != "No relevant information found.":
                # Extract answer from context (simple extraction)
                if "Answer:" in context:
                    parts = context.split("Answer:")
                    if len(parts) > 1:
                        return parts[1].strip().split("\n")[0][:200] + "... For more information, please call us at +91 9897761393."
            return "I apologize, but I'm currently experiencing API limitations. For immediate assistance, please call us at +91 9897761393. Our staff will be happy to help you."
        return f"I apologize, but I encountered an error while processing your question. Please try again or contact the clinic directly at +91 9897761393."

