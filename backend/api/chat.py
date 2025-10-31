from fastapi import APIRouter, HTTPException
from typing import List

from ..models.schemas import ChatRequest, ChatResponse, ChatMessage
from ..agent.scheduling_agent import SchedulingAgent

router = APIRouter()
agent = SchedulingAgent()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for the appointment scheduling agent.
    
    Processes user messages and returns appropriate responses.
    """
    try:
        # Convert conversation history to the format expected by the agent
        conversation_history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Process message with agent
        response, intent, requires_confirmation = agent.process_message(
            request.message,
            conversation_history
        )
        
        return ChatResponse(
            response=response,
            intent=intent,
            requires_confirmation=requires_confirmation
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

