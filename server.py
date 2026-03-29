
import os
import json
import asyncio
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from engine import RetrievalEngine, LLMBridge

# Logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AIFT-FastServer")

app = FastAPI(title="AIFT Fast Server", description="Asynchronous RAG Pipeline with Real-Time Streaming")

# CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Engines

retriever = None
llm = None

@app.on_event("startup")
async def startup_event():
    global retriever, llm
    try:
        logger.info("Initializing engines...")
        retriever = RetrievalEngine()
        llm = LLMBridge()
        logger.info("Engines initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize engines: {e}", exc_info=True)

@app.get("/")
async def read_index():
    return FileResponse("index.html")

async def response_generator(query: str) -> AsyncGenerator[str, None]:
    """ SSE generator """

    try:
        # 1. Retrieval
        context_list = retriever.search(query, k=3)
        yield f"data: {json.dumps({'context': context_list})}\n\n"
        
        # LLM stream

        async for chunk in llm.generate_response(query, context_list):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Error in response generation: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': 'Sunucu hatası oluştu.'})}\n\n"

@app.post("/api/ask")
async def ask(request: Request):
    body = await request.json()
    query = body.get("query", "").strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Boş sorgu gönderilemez.")
    
    if retriever is None or llm is None:
        raise HTTPException(status_code=503, detail="Sistem henüz hazır değil.")

    return StreamingResponse(
        response_generator(query),
        media_type="text/event-stream"
    )

# Static files

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Optimized for production on port 5000
    uvicorn.run(app, host="127.0.0.1", port=5000)
