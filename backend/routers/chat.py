from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
import json, asyncio

from db.models import User, Trip, SearchHistory, get_db
from agents.graph import graph, AgentState
from routers.auth import get_current_user
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class SaveTripRequest(BaseModel):
    title: str
    destination: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    itinerary: Optional[dict] = None


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream AI response via SSE."""
    async def event_generator():
        try:
            # Build message history
            messages = []
            for msg in req.history[-6:]:  # Last 6 messages for context
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))
            messages.append(HumanMessage(content=req.message))

            initial_state: AgentState = {
                "messages": messages,
                "intent": "",
                "trip_context": {},
                "api_data": {},
                "final_response": "",
            }

            # Run graph
            result = await graph.ainvoke(initial_state)
            response_text = result.get("final_response", "I couldn't process that request.")
            api_data = result.get("api_data", {})
            intent = result.get("intent", "general")

            # Save to history
            history_entry = SearchHistory(
                user_id=user.id,
                query=req.message,
                results={"intent": intent, "api_data": api_data, "response": response_text[:500]}
            )
            db.add(history_entry)
            await db.commit()

            # Stream response token by token (simulate for SSE)
            # Send metadata first
            yield f"data: {json.dumps({'type': 'meta', 'intent': intent, 'has_data': bool(api_data)})}\n\n"
            await asyncio.sleep(0.01)

            # Stream text in chunks
            words = response_text.split(" ")
            chunk = ""
            for i, word in enumerate(words):
                chunk += word + " "
                if len(chunk) > 20 or i == len(words) - 1:
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
                    chunk = ""
                    await asyncio.sleep(0.02)

            # Send API data if available
            if api_data:
                yield f"data: {json.dumps({'type': 'api_data', 'data': api_data})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/ask")
async def chat_ask(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Non-streaming chat endpoint (simpler)."""
    messages = []
    for msg in req.history[-6:]:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    messages.append(HumanMessage(content=req.message))

    initial_state: AgentState = {
        "messages": messages,
        "intent": "",
        "trip_context": {},
        "api_data": {},
        "final_response": "",
    }

    result = await graph.ainvoke(initial_state)
    response_text = result.get("final_response", "Sorry, I couldn't process that.")
    api_data = result.get("api_data", {})
    intent = result.get("intent", "general")

    db.add(SearchHistory(
        user_id=user.id,
        query=req.message,
        results={"intent": intent, "response": response_text[:500]}
    ))
    await db.commit()

    return {
        "response": response_text,
        "intent": intent,
        "api_data": api_data,
    }


@router.get("/history")
async def get_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == user.id)
        .order_by(desc(SearchHistory.created_at))
        .limit(20)
    )
    items = result.scalars().all()
    return [{"id": h.id, "query": h.query, "created_at": str(h.created_at)} for h in items]


@router.post("/trips")
async def save_trip(
    req: SaveTripRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    trip = Trip(
        user_id=user.id,
        title=req.title,
        destination=req.destination,
        start_date=req.start_date,
        end_date=req.end_date,
        itinerary=req.itinerary,
    )
    db.add(trip)
    await db.commit()
    return {"id": trip.id, "title": trip.title, "message": "Trip saved!"}


@router.get("/trips")
async def get_trips(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trip).where(Trip.user_id == user.id).order_by(desc(Trip.created_at))
    )
    trips = result.scalars().all()
    return [{
    "id": t.id,
    "title": t.title,
    "destination": t.destination,
    "start_date": t.start_date,
    "end_date": t.end_date,
    "itinerary": t.itinerary,
    "created_at": str(t.created_at)
} for t in trips]

@router.delete("/trips/{trip_id}")
async def delete_trip(
    trip_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Trip).where(Trip.id == trip_id, Trip.user_id == user.id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(404, "Trip not found")
    await db.delete(trip)
    await db.commit()
    return {"message": "Deleted"}
