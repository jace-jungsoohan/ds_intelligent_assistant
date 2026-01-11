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
    data: Optional[List[dict]] = None
    sql: Optional[str] = None
    agent: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        last_message = request.messages[-1]
        
        user_query = last_message.content
        
        history = [
            {"role": m.role, "content": m.content} 
            for m in request.messages[:-1]
        ]
        
        logger.info(f"Processing query: {user_query}")
        result = orchestrator.run(user_query, chat_history=history)
        
        # Extract data
        answer_text = result.get("text", "")
        data_payload = None
        
        raw_data = result.get("data")
        if raw_data is not None:
            # Assuming raw_data is a Pandas DataFrame
            # Convert NaN to None for invalid JSON fix
            try:
                import pandas as pd
                if isinstance(raw_data, pd.DataFrame):
                    # Replace NaN with None (which becomes null in JSON)
                    df_clean = raw_data.where(pd.notnull(raw_data), None)
                    data_payload = df_clean.to_dict(orient="records")
            except Exception as e:
                logger.warning(f"Failed to serialize DataFrame: {e}")
        
        return ChatResponse(
            answer=answer_text,
            data=data_payload,
            sql=result.get("sql"),
            agent=result.get("agent")
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
