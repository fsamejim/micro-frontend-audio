import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types/auth';

interface DashboardAuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  logout: () => void;
}

const AuthContext = createContext<DashboardAuthContextType | undefined>(undefined);

export const DashboardAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    // Check if user is authenticated by looking for token in localStorage
    const token = localStorage.getItem('token');
    if (token) {
      // In a real implementation, you'd decode the JWT or make an API call
      // For now, we'll create a mock user based on auth state
      setUser({
        id: 1,
        username: 'user',
        email: 'user@example.com'
      });
      setIsAuthenticated(true);
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
    // Navigate to login page in shell app
    window.location.href = '/auth/login';
  };

  const value = {
    user,
    isAuthenticated,
    logout,
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
    throw new Error('useAuth must be used within a DashboardAuthProvider');
  }
  return context;
};