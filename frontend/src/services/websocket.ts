import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;

  connect(token: string) {
    this.socket = io('ws://localhost:8000', {
      query: { token },
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  joinChat(chatId: number) {
    this.socket?.emit('join_chat', { chat_id: chatId });
  }

  leaveChat(chatId: number) {
    this.socket?.emit('leave_chat', { chat_id: chatId });
  }

  sendMessage(chatId: number, content: string) {
    this.socket?.emit('send_message', {
      message: {
        chat_id: chatId,
        content,
        message_type: 'text',
      },
    });
  }

  startTyping(chatId: number) {
    this.socket?.emit('typing_start', { chat_id: chatId });
  }

  stopTyping(chatId: number) {
    this.socket?.emit('typing_stop', { chat_id: chatId });
  }

  onNewMessage(callback: (message: any) => void) {
    this.socket?.on('new_message', callback);
  }

  onUserJoined(callback: (data: any) => void) {
    this.socket?.on('user_joined', callback);
  }

  onUserLeft(callback: (data: any) => void) {
    this.socket?.on('user_left', callback);
  }

  onTypingStart(callback: (data: any) => void) {
    this.socket?.on('typing_start', callback);
  }

  onTypingStop(callback: (data: any) => void) {
    this.socket?.on('typing_stop', callback);
  }
}

export const wsService = new WebSocketService();
