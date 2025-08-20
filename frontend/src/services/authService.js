import axios from 'axios';
import { addCsrfInterceptor, clearCsrfToken, refreshCsrfToken } from './csrfService';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

console.log('🔧 Auth Service - API URL:', API_URL);

// Create a dedicated axios instance for auth with explicit credential settings
const authAxios = axios.create({
    baseURL: API_URL,
    withCredentials: true,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    }
});

axios.defaults.withCredentials = true;
axios.defaults.timeout = 10000;

addCsrfInterceptor(axios);
addCsrfInterceptor(authAxios);

const authService = {
    async register(email, password) {
        console.log('Auth Service - Registering user:', email);
        try {
            const response = await authAxios.post('/auth/register', {
                email,
                password
            });
            console.log('Auth Service - Registration successful:', response.data);
            return response.data;
        } catch (error) {
            console.error('Auth Service - Registration failed:', error.response?.data);
            throw error;
        }
    },

    async login(email, password) {
        console.log('Auth Service - Logging in user:', email);
        try {
            const response = await authAxios.post('/auth/login', {
                email,
                password
            });
            console.log('Auth Service - Login successful:', response.data);
            if (response.data.user) {
                localStorage.setItem('user', JSON.stringify(response.data.user));
                // Store JWT token for WebSocket authentication
                if (response.data.access_token) {
                    localStorage.setItem('accessToken', response.data.access_token);
                }
            }
            return response.data;
        } catch (error) {
            console.error('Auth Service - Login failed:', error.response?.data);
            throw error;
        }
    },

    async logout() {
        console.log('Auth Service - Logging out user');
        try {
            await authAxios.post('/auth/logout');
            console.log('Auth Service - Logout successful');
        } catch (error) {
            console.error('Auth Service - Logout error:', error);
        } finally {
            localStorage.removeItem('user');
            localStorage.removeItem('accessToken');
            clearCsrfToken();
        }
    },

    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    },

    getAccessToken() {
        return localStorage.getItem('accessToken');
    },

    isAuthenticated() {
        const user = this.getCurrentUser();
        const token = this.getAccessToken();
        return user && token && !this.isTokenExpired();
    },

    isTokenExpired() {
        const token = this.getAccessToken();
        if (!token) return true;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Date.now() / 1000;
            return payload.exp < currentTime;
        } catch (error) {
            console.error('Token parsing error:', error);
            return true;
        }
    },

    async getUserInfo() {
        const response = await authAxios.get('/auth/user');
        return response.data;
    },

    async updateApiKeys(apiKeys) {
        const user = this.getCurrentUser();
        if (!user) throw new Error('User not authenticated');

        const response = await authAxios.post('/auth/api-keys', apiKeys);
        return response.data;
    },

    // Force refresh CSRF token
    async refreshCsrfToken() {
        return await refreshCsrfToken();
    }
};

export default authService; 