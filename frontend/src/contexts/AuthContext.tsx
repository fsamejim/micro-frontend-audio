import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, LoginRequest, RegisterRequest, AuthContextType } from '../types/auth';
import { authService } from '../services/authService';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!token);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
    }, []);

    const initAuth = useCallback(async () => {
        console.log('initAuth called, token exists:', !!token);
        if (token) {
            try {
                console.log('Fetching current user...');
                const response = await authService.getCurrentUser();
                console.log('User fetch successful:', response);
                setUser(response);
                setIsAuthenticated(true);
            } catch (error) {
                console.error('Failed to get current user:', error);
                logout();
            }
        } else {
            console.log('No token, setting user to null');
            setUser(null);
            setIsAuthenticated(false);
        }
    }, [token, logout]);

    useEffect(() => {
        initAuth();
    }, [initAuth]);

    const login = async (credentials: LoginRequest) => {
        const response = await authService.login(credentials);
        localStorage.setItem('token', response.token);
        setToken(response.token);
        setUser(response.user);
        setIsAuthenticated(true);
        console.log('Login successful, user:', response.user);
    };

    const register = async (data: RegisterRequest) => {
        const response = await authService.register(data);
        localStorage.setItem('token', response.token);
        setToken(response.token);
        setUser(response.user);
        setIsAuthenticated(true);
    };

    const value = {
        user,
        token,
        login,
        register,
        logout,
        isAuthenticated
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}; 