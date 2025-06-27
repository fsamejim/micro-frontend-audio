import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types/auth';

interface AudioAuthContextType {
  user: User | null;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AudioAuthContextType | undefined>(undefined);

export const AudioAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    // Check if user is authenticated by looking for token in localStorage
    const token = localStorage.getItem('token');
    if (token) {
      // In a real implementation, you'd decode the JWT or make an API call
      // For now, we'll create a mock user
      setUser({
        id: 1,
        username: 'user',
        email: 'user@example.com'
      });
      setIsAuthenticated(true);
    }
  }, []);

  const value = {
    user,
    isAuthenticated,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AudioAuthProvider');
  }
  return context;
};