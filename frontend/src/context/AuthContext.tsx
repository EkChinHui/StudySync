/**
 * Authentication Context Provider
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '../api/client';

interface User {
  id: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');
    const userEmail = localStorage.getItem('user_email');

    if (token && userId && userEmail) {
      setUser({ id: userId, email: userEmail });
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await auth.login(email, password);
    const { access_token, user_id } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user_id', user_id);
    localStorage.setItem('user_email', email);

    setUser({ id: user_id, email });
  };

  const register = async (email: string, password: string) => {
    const response = await auth.register(email, password);
    const { access_token, user_id } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user_id', user_id);
    localStorage.setItem('user_email', email);

    setUser({ id: user_id, email });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
