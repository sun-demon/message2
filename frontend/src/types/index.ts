// Типы на основе Telegram структур
export interface User {
  id: number;
  username?: string;
  phone?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  is_online: boolean;
  last_seen: string;
  is_bot: boolean;
  is_premium?: boolean;
}

export interface Chat {
  id: number;
  title?: string;
  name?: string; // для совместимости
  chat_type: 'private' | 'group' | 'channel' | 'supergroup';
  participants?: User[];
  participants_count?: number;
  avatar?: string;
  last_message?: Message;
  unread_count: number;
  is_online?: boolean; // для private чатов
  created_by?: number;
  created_at: string;
  updated_at: string;
  permissions?: ChatPermissions;
}

export interface ChatPermissions {
  send_messages: boolean;
  send_media: boolean;
  send_stickers: boolean;
  send_gifs: boolean;
  send_polls: boolean;
  add_members: boolean;
  pin_messages: boolean;
  change_info: boolean;
}

export interface Message {
  id: number;
  chat_id: number;
  sender_id: number;
  sender?: User;
  content: string;
  message_type: 'text' | 'image' | 'video' | 'gif' | 'voice' | 'file' | 'sticker';
  media?: MessageMedia;
  reply_to?: number;
  reply_message?: Message;
  forwarded_from?: number;
  reactions?: MessageReaction[];
  is_read: boolean;
  is_delivered: boolean;
  is_edited: boolean;
  is_deleted: boolean;
  created_at: string;  // в API используется created_at
  updated_at?: string;
  views?: number;
  edit_date?: string;
}

export interface MessageMedia {
  id: string;
  type: string;
  url?: string;
  thumbnail?: string;
  size?: number;
  duration?: number;
  width?: number;
  height?: number;
  mime_type?: string;
  file_name?: string;
}

export interface MessageReaction {
  emoji: string;
  count: number;
  user_ids: number[];
}

export interface TypingStatus {
  user_id: number;
  chat_id: number;
  action: 'typing' | 'upload_photo' | 'upload_video' | 'upload_audio' | 'upload_file';
}

export interface WebSocketMessage {
  type: 'new_message' | 'message_read' | 'typing_start' | 'typing_stop' | 
        'user_online' | 'user_offline' | 'user_joined' | 'user_left' |
        'message_edited' | 'message_deleted' | 'reaction_added';
  data: any;
  chat_id?: number;
  user_id?: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}