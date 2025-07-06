import axios from 'axios';
import { addCsrfInterceptor, clearCsrfToken, refreshCsrfToken } from './csrfService';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

axios.defaults.withCredentials = true;

// Add CSRF interceptor to the default axios instance
addCsrfInterceptor(axios);

const authService = {
    async register(email, password) {
        const response = await axios.post(`${API_URL}/auth/register`, {
            email,
            password
        });
        return response.data;
    },

    async login(email, password) {
        const response = await axios.post(`${API_URL}/auth/login`, {
            email,
            password
        });
        if (response.data.user) {
            localStorage.setItem('user', JSON.stringify(response.data.user));
            // Store JWT token for WebSocket authentication
            if (response.data.access_token) {
                localStorage.setItem('accessToken', response.data.access_token);
            }
        }
        return response.data;
    },

    async logout() {
        try {
            await axios.post(`${API_URL}/auth/logout`);
        } catch (error) {
            console.error('Logout error:', error);
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
        const response = await axios.get(`${API_URL}/auth/user`);
        return response.data;
    },

    async updateApiKeys(apiKeys) {
        const user = this.getCurrentUser();
        if (!user) throw new Error('User not authenticated');

        const response = await axios.post(`${API_URL}/auth/api-keys`, apiKeys);
        return response.data;
    },

    // Force refresh CSRF token
    async refreshCsrfToken() {
        return await refreshCsrfToken();
    }
};

export default authService; 