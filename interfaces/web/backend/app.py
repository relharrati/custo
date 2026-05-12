"""
Web Backend - FastAPI Application

Provides HTTP API endpoints for the Custo system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

app = FastAPI(title="Custo API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "custo"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to Custo."""
    # Placeholder - would route to main agent
    return ChatResponse(
        response="Custo received your message. Full implementation pending.",
        session_id="session_placeholder"
    )


@app.get("/api/projects")
async def list_projects():
    """List all projects."""
    # Placeholder
    return {"projects": []}


@app.get("/api/memory/search")
async def search_memory(q: str):
    """Search memory."""
    return {"query": q, "results": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
