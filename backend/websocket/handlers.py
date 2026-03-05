from typing import Any, Dict

from sqlalchemy.orm import Session

from services.chat_service import ChatService
from services.message_service import MessageService
from schemas.message import MessageCreate, MessageResponse


class WebSocketHandler:
    """
    Handles different WebSocket message types.
    Separates message handling logic from connection management.
    """
    
    def __init__(self, manager):
        self.manager = manager
    
    async def handle_join_chat(self, user_id: int, data: Dict[str, Any], db: Session):
        """Handle join_chat with access check"""
        chat_id = data.get("chat_id")
        if not chat_id:
            return
        
        from services.chat_service import ChatService
        
        try:
            # Check if user is a member
            chat = ChatService.get_chat_details(db, chat_id, user_id)
            
            # Join the chat room
            await self.manager.join_chat(user_id, chat_id)
            
            # Send confirmation back to user
            await self.manager.send_to_user(user_id, {
                "type": "chat_joined",
                "chat_id": chat_id,
                "message": "You are now receiving updates from this chat"
            })
            
        except ValueError as e:
            # Send error back to user
            await self.manager.send_to_user(user_id, {
                "type": "error",
                "error": f"Cannot join chat: {str(e)}"
            })
    
    async def handle_leave_chat(self, user_id: int, data: Dict[str, Any]):
        """Handle leave_chat message"""
        chat_id = data.get("chat_id")
        if chat_id:
            await self.manager.leave_chat(user_id, chat_id)
    
    async def handle_typing_start(self, user_id: int, data: Dict[str, Any]):
        """Handle typing_start message"""
        chat_id = data.get("chat_id")
        if chat_id:
            await self.manager.start_typing(user_id, chat_id)
    
    async def handle_typing_stop(self, user_id: int, data: Dict[str, Any]):
        """Handle typing_stop message"""
        chat_id = data.get("chat_id")
        if chat_id:
            await self.manager.stop_typing(user_id, chat_id)
    
    async def handle_send_message(
        self, 
        user_id: int, 
        data: Dict[str, Any], 
        db: Session
    ):
        """Handle send_message - uses MessageService"""
        print(f"📨 WebSocket got send_message from user {user_id}")
        
        message_data = data.get("message")
        if not message_data:
            await self.manager.send_to_user(user_id, {
                "type": "error",
                "error": "No message data provided"
            })
            return
        
        try:
            # Convert dict to Pydantic schema
            message_create = MessageCreate(**message_data)
            
            # Create message in database
            new_message = MessageService.create_message(db, message_create, user_id)

            # Convert to dict with ISO format dates
            message_dict = {
                "id": new_message.id,
                "chat_id": new_message.chat_id,
                "sender_id": new_message.sender_id,
                "content": new_message.content,
                "message_type": new_message.message_type,
                "created_at": new_message.created_at.isoformat(),  # ← явно в строку!
                "updated_at": new_message.updated_at.isoformat(),  # ← явно в строку!
                "is_edited": new_message.is_edited,
                "reply_to": new_message.reply_to,
                "reactions": new_message.reactions
            }
            
            # Broadcast to chat
            await self.manager.send_new_message(
                message_data=message_dict,  # ← теперь всё сериализуемо!
                chat_id=message_data["chat_id"],
                sender_id=user_id
            )
            
        except ValueError as e:
            await self.manager.send_to_user(user_id, {
                "type": "error",
                "error": str(e)
            })
    
    async def handle_mark_read(self, user_id: int, data: Dict[str, Any]):
        """Handle mark_read message"""
        chat_id = data.get("chat_id")
        message_ids = data.get("message_ids", [])
        if chat_id and message_ids:
            await self.manager.mark_messages_read(user_id, chat_id, message_ids)
    
    async def handle_ping(self, user_id: int):
        """Handle ping - respond with pong"""
        await self.manager.send_to_user(user_id, {"type": "pong"})
