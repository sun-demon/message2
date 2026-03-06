import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, User } from '../types';
import api from '../services/api';

interface AuthStore extends AuthState {
  login: (identifier: string, password: string, method: 'phone' | 'email') => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  setUser: (user: User | null) => void;
  updateUser: (userData: Partial<User>) => void;
}

interface RegisterData {
  username?: string;
  phone?: string;
  email?: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (identifier: string, password: string, method: 'phone' | 'email') => {
        try {
          const response = await api.post('/auth/login', {
            [method]: identifier,
            password
          });

          const { user, token } = response.data;

          // Сохраняем токен в localStorage для axios интерцепторов
          localStorage.setItem('token', token);

          set({
            user,
            token,
            isAuthenticated: true
          });
        } catch (error: any) {
          throw new Error(error.response?.data?.message || 'Ошибка входа');
        }
      },

      register: async (data: RegisterData) => {
        try {
          const response = await api.post('/auth/register', data);
          const { user, token } = response.data;

          localStorage.setItem('token', token);

          set({
            user,
            token,
            isAuthenticated: true
          });
        } catch (error: any) {
          throw new Error(error.response?.data?.message || 'Ошибка регистрации');
        }
      },

      logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('auth-storage');
        set({
          user: null,
          token: null,
          isAuthenticated: false
        });
      },

      setUser: (user: User | null) => {
        set({ user });
      },

      updateUser: (userData: Partial<User>) => {
        const currentUser = get().user;
        if (currentUser) {
          set({
            user: { ...currentUser, ...userData }
          });
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);