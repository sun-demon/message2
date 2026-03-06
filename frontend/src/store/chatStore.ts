import { create } from 'zustand';
import type { Chat, Message } from '../types';
import { chatsApi, messagesApi } from '../services/api';
import { wsService } from '../services/websocket';

// Defining the status interface
interface ChatState {
  // Condition
  chats: Chat[];
  currentChat: Chat | null;
  messages: Record<number, Message[]>;  // messages[chatId] = messages
  onlineUsers: Set<number>;
  typingUsers: Record<number, Set<number>>;  // typingUsers[chatId] = Set(userIds)
  isLoading: boolean;
  error: string | null;

  // Actions
  loadChats: () => Promise<void>;
  selectChat: (chatId: number) => Promise<void>;
  loadMessages: (chatId: number) => Promise<void>;
  sendMessage: (chatId: number, content: string) => void;
  addMessage: (message: Message) => void;
  setTyping: (chatId: number, isTyping: boolean) => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  chats: [],
  currentChat: null,
  messages: {},
  onlineUsers: new Set(),
  typingUsers: {},
  isLoading: false,
  error: null,

  // Upload a list of chats
  loadChats: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await chatsApi.getMyChats();
      set({ chats: response.data, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to load chats', 
        isLoading: false 
      });
    }
  },

  // Select a chat and upload messages
  selectChat: async (chatId: number) => {
    const { chats, loadMessages } = get();
    const chat = chats.find(c => c.id === chatId) || null;
    set({ currentChat: chat });
    
    if (chat) {
      // Joining the WebSocket chat room
      wsService.joinChat(chatId);
      await loadMessages(chatId);
    }
  },

  // Upload Chat messages
  loadMessages: async (chatId: number) => {
    set({ isLoading: true });
    try {
      const response = await messagesApi.getMessages(chatId);
      set((state: ChatState) => ({
        messages: { ...state.messages, [chatId]: response.data },
        isLoading: false
      }));
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to load messages',
        isLoading: false 
      });
    }
  },

  // Send a message
  sendMessage: (chatId: number, content: string) => {
    wsService.sendMessage(chatId, content);
  },

  // Add a new message (from WebSocket)
  addMessage: (message: Message) => {
    set((state: ChatState) => ({
      messages: {
        ...state.messages,
        [message.chat_id]: [
          ...(state.messages[message.chat_id] || []),
          message
        ]
      }
    }));
  },

  // Send printing status
  setTyping: (chatId: number, isTyping: boolean) => {
    if (isTyping) {
      wsService.startTyping(chatId);
    } else {
      wsService.stopTyping(chatId);
    }
  },

  // Clear the error
  clearError: () => set({ error: null }),
}));

// WebSocket subscriptions (initialize after creating the store)
export const initWebSocket = () => {
  const store = useChatStore.getState();
  
  wsService.onNewMessage((message) => {
    store.addMessage(message);
  });

  wsService.onUserJoined((data) => {
    console.log('User joined:', data);
    // The list of online users can be updated
  });

  wsService.onUserLeft((data) => {
    console.log('User left:', data);
  });

  wsService.onTypingStart(({ user_id, chat_id }) => {
    useChatStore.setState((state: ChatState) => {
      const typing = new Set(state.typingUsers[chat_id] || []);
      typing.add(user_id);
      return {
        typingUsers: { ...state.typingUsers, [chat_id]: typing }
      };
    });
  });

  wsService.onTypingStop(({ user_id, chat_id }) => {
    useChatStore.setState((state: ChatState) => {
      const typing = new Set(state.typingUsers[chat_id] || []);
      typing.delete(user_id);
      return {
        typingUsers: { ...state.typingUsers, [chat_id]: typing }
      };
    });
  });
};
