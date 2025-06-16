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
        }
        return response.data;
    },

    logout() {
        localStorage.removeItem('user');
        return axios.post(`${API_URL}/auth/logout`);
    },

    getCurrentUser() {
        return JSON.parse(localStorage.getItem('user'));
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