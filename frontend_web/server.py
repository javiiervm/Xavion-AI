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

# Mount static files
app.mount("/static", StaticFiles(directory="frontend_web/static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="frontend_web/templates")

class ChatRequest(BaseModel):
    message: str
    history: str = ""
    mode: str = "auto"
    debug: bool = False

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
        yield f"data: {json.dumps({'done': True, 'history': updated_history, 'debug': debug_info})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

def start_server(port=8000):
    uvicorn.run(app, host="0.0.0.0", port=port)
