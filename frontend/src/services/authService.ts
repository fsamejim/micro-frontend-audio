import axios from 'axios';
import { LoginRequest, RegisterRequest, AuthResponse, User } from '../types/auth';

const API_BASE_URL = '/api';
const API_URL = `${API_BASE_URL}/auth`;

// Function to set auth token in axios headers
const setAuthToken = (token: string | null) => {
    if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete axios.defaults.headers.common['Authorization'];
    }
};

export const authService = {
    login: async (credentials: LoginRequest): Promise<AuthResponse> => {
        const response = await axios.post(`${API_URL}/login`, credentials);
        const { token } = response.data;
        
        // Set token in localStorage and axios headers
        localStorage.setItem('token', token);
        setAuthToken(token);
        
        return response.data;
    },

    register: async (data: RegisterRequest): Promise<AuthResponse> => {
        const response = await axios.post(`${API_URL}/register`, data);
        const { token } = response.data;
        
        // Set token in localStorage and axios headers
        localStorage.setItem('token', token);
        setAuthToken(token);
        
        return response.data;
    },

    getCurrentUser: async (): Promise<User> => {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('No token found');
        }

        try {
            const response = await axios.get(`${API_URL}/me`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching current user:', error);
            localStorage.removeItem('token'); // Remove invalid token
            throw new Error('Authentication failed. Please log in again.');
        }
    }
};

// Axios interceptor for adding token to requests
axios.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
); 