import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

axios.defaults.withCredentials = true;

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

    logout() {
        localStorage.removeItem('user');
        localStorage.removeItem('accessToken');
        return axios.post(`${API_URL}/auth/logout`);
    },

    getCurrentUser() {
        return JSON.parse(localStorage.getItem('user'));
    },

    getAccessToken() {
        return localStorage.getItem('accessToken');
    },

    isAuthenticated() {
        const user = this.getCurrentUser();
        const token = this.getAccessToken();
        return !!(user && token);
    },

    // Check if token is expired (basic check)
    isTokenExpired() {
        const token = this.getAccessToken();
        if (!token) return true;
        
        try {
            // Decode JWT token to check expiration
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Date.now() / 1000;
            return payload.exp < currentTime;
        } catch (error) {
            console.error('Error checking token expiration:', error);
            return true;
        }
    },

    // Refresh token by re-authenticating
    async refreshToken() {
        const user = this.getCurrentUser();
        if (!user) {
            throw new Error('No user found for token refresh');
        }
        
        try {
            // For now, we'll just re-authenticate the user
            // In a real app, you might have a dedicated refresh endpoint
            const response = await axios.post(`${API_URL}/auth/login`, {
                email: user.email,
                password: '' // You'd need to store password securely or use refresh tokens
            });
            
            if (response.data.access_token) {
                localStorage.setItem('accessToken', response.data.access_token);
                return response.data.access_token;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.logout();
            throw error;
        }
    },

    async updateApiKeys(apiKeys) {
        const user = this.getCurrentUser();
        if (!user) throw new Error('User not authenticated');

        const response = await axios.post(`${API_URL}/auth/api-keys`, apiKeys);
        return response.data;
    },

    async getUserInfo() {
        const user = this.getCurrentUser();
        if (!user) throw new Error('User not authenticated');

        const response = await axios.get(`${API_URL}/auth/user`);
        return response.data;
    }
};

export default authService; 