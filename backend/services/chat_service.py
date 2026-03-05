from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.chat import Chat
from models.user import User
from schemas.chat import ChatCreate


class ChatService:
    """Service layer for chat business logic"""
    
    # Helper methods
    
    @staticmethod
    def _validate_users_exist(db: Session, user_ids: List[int]) -> Tuple[List[int], List[int]]:
        """
        Validate that users exist.
        Returns (valid_ids, invalid_ids)
        """
        valid_ids = []
        invalid_ids = []
        
        for uid in user_ids:
            user = db.query(User).filter(User.id == uid).first()
            if user:
                valid_ids.append(uid)
            else:
                invalid_ids.append(uid)
        
        return valid_ids, invalid_ids
    
    @staticmethod
    def _get_chat_with_access_check(db: Session, chat_id: int, user_id: int) -> Chat:
        """Get chat and check if user is a member"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise ValueError("Chat not found")
        
        user = db.query(User).filter(User.id == user_id).first()
        if user not in chat.participants:
            raise ValueError("You are not a member of this chat")
        
        return chat
    
    @staticmethod
    def _check_creator_access(chat: Chat, user_id: int):
        """Check if user is the chat creator"""
        if chat.created_by != user_id:
            raise ValueError("Only the chat creator can perform this action")
    
    @staticmethod
    def _format_chat_response(chat: Chat, include_members: bool = False) -> Dict[str, Any]:
        """Format chat for response"""
        # Special display name for Saved Messages
        display_name = chat.name
        if chat.chat_type == "private" and len(chat.participants) == 1:
            display_name = "Saved Messages"
        
        result = {
            "id": chat.id,
            "name": display_name,
            "chat_type": chat.chat_type,
            "created_by": chat.created_by,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
            "member_count": len(chat.participants)
        }
        
        if include_members:
            result["members"] = [
                {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url,
                    "is_online": user.is_online
                }
                for user in chat.participants
            ]
        
        return result
    
    # Saved Messages
    
    @staticmethod
    def create_saved_messages_chat(db: Session, user: User) -> Chat:
        """
        Create Saved Messages chat for a user.
        Called automatically after user registration.
        """
        # Check if already exists
        existing = ChatService.get_saved_messages(db, user.id)
        if existing:
            return existing
        
        saved_chat = Chat(
            name=None,
            chat_type="private",
            created_by=user.id
        )
        db.add(saved_chat)
        db.flush()
        
        # Add only the user themselves
        saved_chat.participants.append(user)
        
        db.commit()
        db.refresh(saved_chat)
        return saved_chat
    
    @staticmethod
    def get_saved_messages(db: Session, user_id: int) -> Optional[Chat]:
        """Get existing Saved Messages chat for user"""
        return (
            db.query(Chat)
            .join(Chat.participants)
            .filter(
                Chat.chat_type == "private",
                Chat.participants.any(User.id == user_id)
            )
            .group_by(Chat.id)
            .having(func.count(Chat.id) == 1)
            .first()
        )
    
    # Chat CRUD
    
    @staticmethod
    def create_chat(
        db: Session, 
        chat_data: ChatCreate, 
        creator_id: int
    ) -> Dict[str, Any]:
        """
        Create a new chat.
        Returns formatted chat response.
        """
        # Validate chat type
        if chat_data.chat_type not in ["private", "group", "channel"]:
            raise ValueError("Invalid chat type. Must be 'private', 'group', or 'channel'")
        
        # Filter out creator from member_ids
        other_user_ids = [uid for uid in chat_data.member_ids if uid != creator_id]
        
        # Validate users exist
        valid_ids, invalid_ids = ChatService._validate_users_exist(db, other_user_ids)
        if invalid_ids:
            raise ValueError(f"Users with IDs {invalid_ids} do not exist")
        
        # Check if this is Saved Messages request
        if chat_data.chat_type == "private" and len(valid_ids) == 0:
            existing = ChatService.get_saved_messages(db, creator_id)
            if existing:
                return ChatService._format_chat_response(existing)
            
            new_chat = ChatService.create_saved_messages(db, 
                db.query(User).filter(User.id == creator_id).first())
            return ChatService._format_chat_response(new_chat)
        
        # Check if private chat with another user
        if chat_data.chat_type == "private":
            if len(valid_ids) != 1:
                raise ValueError("Private chat with another user must have exactly one member ID")
            
            # Check if chat already exists
            other_user_id = valid_ids[0]
            existing_chat = (
                db.query(Chat)
                .join(Chat.participants)
                .filter(
                    Chat.chat_type == "private",
                    Chat.participants.any(User.id == creator_id),
                    Chat.participants.any(User.id == other_user_id)
                )
                .group_by(Chat.id)
                .having(func.count(User.id) == 2)
                .first()
            )
            
            if existing_chat:
                return ChatService._format_chat_response(existing_chat)
            
            chat_name = None
        
        # Validate group/channel name
        elif chat_data.chat_type in ["group", "channel"]:
            if not chat_data.name:
                raise ValueError(f"{chat_data.chat_type} chat must have a name")
            chat_name = chat_data.name
        
        # Get member objects
        members = db.query(User).filter(User.id.in_(valid_ids)).all() if valid_ids else []
        
        # Create chat
        db_chat = Chat(
            name=chat_name,
            chat_type=chat_data.chat_type,
            created_by=creator_id
        )
        db.add(db_chat)
        db.flush()
        
        # Add creator
        creator = db.query(User).filter(User.id == creator_id).first()
        db_chat.participants.append(creator)
        
        # Add other members
        for member in members:
            db_chat.participants.append(member)
        
        db.commit()
        db.refresh(db_chat)
        db.refresh(db_chat, ['participants'])
        
        return ChatService._format_chat_response(db_chat)
    
    @staticmethod
    def get_user_chats(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all chats for a user"""
        chats = (
            db.query(Chat)
            .join(Chat.participants)
            .filter(User.id == user_id)
            .order_by(Chat.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [ChatService._format_chat_response(chat) for chat in chats]
    
    @staticmethod
    def get_chat_details(db: Session, chat_id: int, user_id: int) -> Dict[str, Any]:
        """Get detailed chat info with members"""
        chat = ChatService._get_chat_with_access_check(db, chat_id, user_id)
        return ChatService._format_chat_response(chat, include_members=True)
    
    # Member management
    
    @staticmethod
    def add_members(
        db: Session,
        chat_id: int,
        member_ids: List[int],
        requester_id: int
    ) -> Dict[str, Any]:
        """Add members to a group chat or channel"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise ValueError("Chat not found")
        
        # Check permissions
        ChatService._check_creator_access(chat, requester_id)
        
        # Validate chat type
        if chat.chat_type == "private":
            raise ValueError("Cannot add members to private chats")
        
        # Get existing members
        existing_ids = [user.id for user in chat.participants]
        
        # Find new members
        valid_ids, invalid_ids = ChatService._validate_users_exist(db, member_ids)
        if invalid_ids:
            raise ValueError(f"Users with IDs {invalid_ids} do not exist")
        
        new_ids = [uid for uid in valid_ids if uid not in existing_ids]
        if not new_ids:
            raise ValueError("All users are already members")
        
        # Add new members
        new_members = db.query(User).filter(User.id.in_(new_ids)).all()
        for member in new_members:
            chat.participants.append(member)
        
        db.commit()
        db.refresh(chat)
        
        return ChatService._format_chat_response(chat, include_members=True)
    
    @staticmethod
    def remove_member(
        db: Session,
        chat_id: int,
        user_id: int,
        requester_id: int
    ) -> Dict[str, Any]:
        """Remove a member from a group chat or channel"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise ValueError("Chat not found")
        
        # Check permissions
        ChatService._check_creator_access(chat, requester_id)
        
        # Validate chat type
        if chat.chat_type == "private":
            raise ValueError("Cannot remove members from private chats")
        
        # Cannot remove creator
        if user_id == chat.created_by:
            raise ValueError("Cannot remove the chat creator")
        
        # Find user to remove
        user_to_remove = db.query(User).filter(User.id == user_id).first()
        if not user_to_remove:
            raise ValueError("User not found")
        
        # Check if user is a member
        if user_to_remove not in chat.participants:
            raise ValueError("User is not a member of this chat")
        
        # Remove user
        chat.participants.remove(user_to_remove)
        db.commit()
        
        return {"message": "Member removed successfully"}
