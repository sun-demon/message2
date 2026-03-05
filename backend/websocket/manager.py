import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections, chat presence, and real-time messaging.
    """
    
    def __init__(self):
        # Active WebSocket connections: {user_id: websocket}
        self.active_connections: Dict[int, WebSocket] = {}
        
        # Users currently in chats: {chat_id: set(user_ids)}
        self.chat_presence: Dict[int, Set[int]] = {}
        
        # Users currently typing: {chat_id: set(user_ids)}
        self.typing_users: Dict[int, Set[int]] = {}
        
        # Ping intervals to keep connections alive
        self.ping_interval = 30  # seconds
    
    # Connection management
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Start ping loop for this connection
        asyncio.create_task(self._ping_loop(user_id))
        
        print(f"🟢 User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: int):
        """Remove a disconnected user"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove user from all chats
        for chat_id in list(self.chat_presence.keys()):
            self.chat_presence[chat_id].discard(user_id)
        
        # Remove user from typing status
        for chat_id in list(self.typing_users.keys()):
            self.typing_users[chat_id].discard(user_id)
        
        print(f"🔴 User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def _ping_loop(self, user_id: int):
        """Send periodic pings to keep connection alive"""
        while user_id in self.active_connections:
            try:
                await self.send_to_user(user_id, {"type": "ping"})
                await asyncio.sleep(self.ping_interval)
            except:
                # If ping fails, connection is dead
                self.disconnect(user_id)
                break
    
    # Sending messages
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send a message to a specific user (with error handling)"""
        print(f"📤 Attempting to send to user {user_id}: {message.get('type', 'unknown')}")
        
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                print(f"✅ Sent to user {user_id}")
                return True
            except Exception as e:
                print(f"❌ Error sending to user {user_id}: {e}")
                self.disconnect(user_id)
                return False
        else:
            print(f"⚠️ User {user_id} not connected")
            return False
    
    async def broadcast_to_chat(
        self, 
        chat_id: int, 
        message: dict, 
        exclude_user: Optional[int] = None
    ):
        """Send a message to all users in a chat (safe from disconnections)"""
        if chat_id not in self.chat_presence:
            return
        
        # Create a copy of users to iterate safely
        users = list(self.chat_presence[chat_id])
        
        for user_id in users:
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(user_id, message)
    
    async def broadcast_to_all(self, message: dict):
        """Send a message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)
    
    # Chat presence
    
    async def join_chat(self, user_id: int, chat_id: int):
        """User enters a chat"""
        print(f"🔵 join_chat called: user={user_id}, chat={chat_id}")
        
        if chat_id not in self.chat_presence:
            self.chat_presence[chat_id] = set()
            print(f"  Created new presence set for chat {chat_id}")
        
        if user_id in self.chat_presence[chat_id]:
            print(f"  User {user_id} already in chat {chat_id}")
            return
        
        self.chat_presence[chat_id].add(user_id)
        print(f"  Added user {user_id} to chat {chat_id}. Now {len(self.chat_presence[chat_id])} users")
        
        # Notify others
        users = list(self.chat_presence[chat_id])
        print(f"  Notifying {len(users)} users in chat {chat_id}")
        
        for uid in users:
            if uid != user_id:
                print(f"  Notifying user {uid} about new user {user_id}")
                await self.send_to_user(uid, {
                    "type": "user_joined",
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    async def leave_chat(self, user_id: int, chat_id: int):
        """User leaves a chat"""
        if chat_id in self.chat_presence:
            self.chat_presence[chat_id].discard(user_id)
            
            # Clean up empty chat
            if not self.chat_presence[chat_id]:
                del self.chat_presence[chat_id]
            
            # Notify others in chat
            await self.broadcast_to_chat(
                chat_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                exclude_user=user_id
            )
            
            print(f"👋 User {user_id} left chat {chat_id}")
    
    # Typing indicators
    
    async def start_typing(self, user_id: int, chat_id: int):
        """User started typing"""
        if chat_id not in self.typing_users:
            self.typing_users[chat_id] = set()
        
        self.typing_users[chat_id].add(user_id)
        
        await self.broadcast_to_chat(
            chat_id,
            {
                "type": "typing_start",
                "user_id": user_id,
                "chat_id": chat_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            exclude_user=user_id
        )
        
        # Auto-stop typing after 5 seconds
        async def auto_stop():
            await asyncio.sleep(5)
            await self.stop_typing(user_id, chat_id)
        
        asyncio.create_task(auto_stop())
    
    async def stop_typing(self, user_id: int, chat_id: int):
        """User stopped typing"""
        if chat_id in self.typing_users:
            self.typing_users[chat_id].discard(user_id)
            
            # Clean up empty typing set
            if not self.typing_users[chat_id]:
                del self.typing_users[chat_id]
        
        await self.broadcast_to_chat(
            chat_id,
            {
                "type": "typing_stop",
                "user_id": user_id,
                "chat_id": chat_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            exclude_user=user_id
        )
    
    # Message handling
    
    async def send_new_message(self, message_data: dict, chat_id: int, sender_id: int):
        """Broadcast a new message to all chat participants"""
        print(f"📢 Broadcasting new message in chat {chat_id} from user {sender_id}")
        print(f"  Current presence in chat {chat_id}: {self.chat_presence.get(chat_id, set())}")
        
        if chat_id in self.chat_presence:
            users = list(self.chat_presence[chat_id])
            print(f"  Sending to {len(users)} users: {users}")
            
            for user_id in users:
                if user_id != sender_id:
                    print(f"  -> Sending to user {user_id}")
                    await self.send_to_user(user_id, {
                        "type": "new_message",
                        "chat_id": chat_id,
                        "sender_id": sender_id,
                        "message": message_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        else:
            print(f"  ⚠️ No presence for chat {chat_id}")
    
    async def mark_messages_read(self, user_id: int, chat_id: int, message_ids: list):
        """Mark messages as read and notify others"""
        await self.broadcast_to_chat(
            chat_id,
            {
                "type": "messages_read",
                "user_id": user_id,
                "chat_id": chat_id,
                "message_ids": message_ids,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            exclude_user=user_id
        )


# Global instance
manager = ConnectionManager()
