import axios from 'axios';
import type { AuthResponse, LoginRequest, RegisterRequest, User, Chat, Message } from '../types';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Adding a token to each request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authApi = {
  login: (data: LoginRequest) => 
    api.post<AuthResponse>('/auth/login', data),
  
  register: (data: RegisterRequest) => 
    api.post<User>('/auth/register', data),
  
  getMe: () => 
    api.get<User>('/auth/me'),
};

// Chats API
export const chatsApi = {
  getMyChats: () => 
    api.get<Chat[]>('/chats'),
  
  getChat: (id: number) => 
    api.get<Chat>(`/chats/${id}`),
  
  createChat: (data: any) => 
    api.post<Chat>('/chats', data),
};

// Messages API
export const messagesApi = {
  getMessages: (chatId: number, skip = 0, limit = 50) => 
    api.get<Message[]>(`/messages/chats/${chatId}/messages?skip=${skip}&limit=${limit}`),
  
  sendMessage: (data: any) => 
    api.post<Message>('/messages', data),
};

export default api;
