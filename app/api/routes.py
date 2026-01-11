from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.agents.orchestrator import Orchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Orchestrator (Single instance)
orchestrator = Orchestrator()

class ChatMessage(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    # user_id or session_id could be added here

class ChatResponse(BaseModel):
    answer: str
    # we could add sources, charts data structure here later

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Extract the latest user message
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        last_message = request.messages[-1]
        if last_message.role != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")
            
        user_query = last_message.content
        
        # Extract history (excluding the last one)
        # Convert Pydantic models to list of dicts or whatever format agents expect
        # Agents expect: [{"role": "user", "content": "..."}, ...]
        history = [
            {"role": m.role, "content": m.content} 
            for m in request.messages[:-1]
        ]
        
        # Run Orchestrator
        logger.info(f"Processing query: {user_query}")
        result = orchestrator.run(user_query, chat_history=history)
        
        # result is currently a string (response text)
        return ChatResponse(answer=result)
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
