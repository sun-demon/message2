from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints.auth import router as auth_router
from api.endpoints.chats import router as chats_router
from api.endpoints.messages import router as messages_router
from core.security import get_current_user_ws
from db.session import SessionLocal
from websocket.handlers import WebSocketHandler
from websocket.manager import manager

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="message2 API", version="0.1.0")

# Configuring CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In develop may "*", after other
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "message2 API", "status": "running"}


@app.get("/ping")
async def ping():
    return {"ping": "pong"}


app.include_router(auth_router)
app.include_router(chats_router)
app.include_router(messages_router)


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    # Authenticate
    user = await get_current_user_ws(token)
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    # Initialize handler with manager
    handler = WebSocketHandler(manager)
    
    # Connect
    await manager.connect(websocket, user.id)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            # Create DB session for operations that need it
            db = SessionLocal()
            try:
                if msg_type == "join_chat":
                    await handler.handle_join_chat(user.id, data, db)
                elif msg_type == "leave_chat":
                    await handler.handle_leave_chat(user.id, data)
                elif msg_type == "typing_start":
                    await handler.handle_typing_start(user.id, data)
                elif msg_type == "typing_stop":
                    await handler.handle_typing_stop(user.id, data)
                elif msg_type == "send_message":
                    await handler.handle_send_message(user.id, data, db)
                elif msg_type == "mark_read":
                    await handler.handle_mark_read(user.id, data)
                elif msg_type == "ping":
                    await handler.handle_ping(user.id)
            finally:
                db.close()
                
    except WebSocketDisconnect:
        manager.disconnect(user.id)
        # Notify others
        await manager.broadcast_to_all({
            "type": "user_offline",
            "user_id": user.id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


#  Start point for launching of python main.py (optional)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
