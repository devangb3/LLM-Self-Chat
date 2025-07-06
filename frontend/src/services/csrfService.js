import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

let csrfToken = null;

const getCsrfToken = async () => {
    try {
        const response = await axios.get(`${API_URL}/csrf-token`);
        csrfToken = response.data.csrf_token;
        return csrfToken;
    } catch (error) {
        console.error('Failed to get CSRF token:', error);
        return null;
    }
};

const clearCsrfToken = () => {
    csrfToken = null;
};

const refreshCsrfToken = async () => {
    clearCsrfToken();
    return await getCsrfToken();
};

// Create axios interceptor for CSRF token handling
const addCsrfInterceptor = (axiosInstance) => {
    axiosInstance.interceptors.request.use(async (config) => {
        if (config.method !== 'get' && !config.url.includes('socket')) {
            const token = await getCsrfToken();
            if (token) {
                config.headers['X-CSRFToken'] = token;
            }
        }
        return config;
    });

    axiosInstance.interceptors.response.use(
        (response) => response,
        (error) => {
            // If we get a CSRF error, clear the token
            if (error.response && error.response.status === 400 && 
                error.response.data && error.response.data.error === 'CSRF token validation failed') {
                console.log('CSRF token expired, clearing...');
                clearCsrfToken();
            }
            return Promise.reject(error);
        }
    );
};

export {
    getCsrfToken,
    clearCsrfToken,
    refreshCsrfToken,
    addCsrfInterceptor
}; 