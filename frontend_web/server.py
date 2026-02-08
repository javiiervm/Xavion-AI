import argparse
import os
import time
import uuid
import glob
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import json
import asyncio
from typing import List, Optional

from backend.core import process_message
from langchain_core.callbacks import BaseCallbackHandler

app = FastAPI(title="Xavion AI Web Interface")

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend_web/static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="frontend_web/templates")

class ChatRequest(BaseModel):
    message: str
    history: str = ""
    mode: str = "auto"
    debug: bool = False
    conversation_id: Optional[str] = None

class ConversationMetadata(BaseModel):
    id: str
    title: str
    last_interaction: float

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    conversations = []
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                conversations.append({
                    "id": data["id"],
                    "title": data.get("title", "New Conversation"),
                    "last_interaction": data.get("last_interaction", 0)
                })
        except Exception:
            continue
    
    # Sort by last interaction descending
    conversations.sort(key=lambda x: x["last_interaction"], reverse=True)
    return conversations

@app.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    file_path = os.path.join(DATA_DIR, f"{conv_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class WebStreamingHandler(BaseCallbackHandler):
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.queue = queue
        self.loop = loop

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        asyncio.run_coroutine_threadsafe(self.queue.put(token), self.loop)

    def on_llm_end(self, *args, **kwargs) -> None:
        asyncio.run_coroutine_threadsafe(self.queue.put(None), self.loop)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    handler = WebStreamingHandler(queue, loop)
    
    conv_id = request.conversation_id or str(uuid.uuid4())
    file_path = os.path.join(DATA_DIR, f"{conv_id}.json")
    
    # Load existing messages if it exists
    messages = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            messages = existing_data.get("messages", [])
    
    async def generate():
        # Start processing in background thread
        task = asyncio.create_task(asyncio.to_thread(
            process_message,
            request.message,
            request.history,
            intent_mode=request.mode,
            debug_mode=request.debug,
            callbacks=[handler]
        ))
        
        while True:
            token = await queue.get()
            if token is None:
                break
            yield f"data: {json.dumps({'token': token})}\n\n"
        
        # Get the final response info
        response, updated_history, debug_info = await task
        
        # Update messages list
        new_messages = list(messages)
        new_messages.append({"role": "user", "content": request.message})
        new_messages.append({"role": "assistant", "content": response})
        
        # Determine title (use first message if new)
        title = request.message[:40] + "..." if len(request.message) > 40 else request.message
        if messages:
            with open(file_path, 'r', encoding='utf-8') as f:
                title = json.load(f).get("title", title)

        # Save to disk
        conv_data = {
            "id": conv_id,
            "title": title,
            "last_interaction": time.time(),
            "messages": new_messages,
            "history": updated_history
        }
        
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conv_data, f, ensure_ascii=False, indent=2)
            
        yield f"data: {json.dumps({
            'done': True, 
            'history': updated_history, 
            'debug': debug_info,
            'conversation_id': conv_id,
            'title': title
        })}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

def start_server(port=8000):
    uvicorn.run(app, host="0.0.0.0", port=port)
