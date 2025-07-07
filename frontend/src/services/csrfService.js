import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

let csrfToken = null;

const getCsrfToken = async () => {
    if (csrfToken) {
        console.log('Using cached CSRF token:', csrfToken.substring(0, 20) + '...');
        return csrfToken;
    }

    try {
        console.log('Requesting CSRF token from:', `${API_URL}/csrf-token`);
        const response = await axios.get(`${API_URL}/csrf-token`, {
            withCredentials: true
        });
        console.log('CSRF token response:', response.data);
        csrfToken = response.data.csrf_token;
        console.log('💾 Stored CSRF token:', csrfToken ? `${csrfToken.substring(0, 20)}...` : 'null');
        return csrfToken;
    } catch (error) {
        console.error('Failed to get CSRF token:', error);
        console.error('Error response:', error.response?.data);
        return null;
    }
};

const clearCsrfToken = () => {
    console.log('Clearing CSRF token');
    csrfToken = null;
};

const refreshCsrfToken = async () => {
    console.log('Refreshing CSRF token');
    clearCsrfToken();
    return await getCsrfToken();
};

const addCsrfInterceptor = (axiosInstance) => {
    axiosInstance.interceptors.request.use(async (config) => {
        console.log('Interceptor - Request method:', config.method);
        console.log('Interceptor - Request URL:', config.url);
        
        // Ensure withCredentials is always set
        config.withCredentials = true;
        
        // Skip CSRF for GET requests
        if (config.method === 'get') {
            console.log('Skipping CSRF token for GET request');
        } else {
            console.log('Adding CSRF token to request');
            const token = await getCsrfToken();
            if (token) {
                config.headers['X-CSRFToken'] = token;
                console.log('Added CSRF token to headers');
            } else {
                console.warn('No CSRF token available for request');
            }
        }
        
        console.log('Final request headers:', config.headers);
        return config;
    });

    axiosInstance.interceptors.response.use(
        (response) => {
            console.log('Response received:', response.status, response.config.url);
            return response;
        },
        (error) => {
            console.error('Response error:', error.response?.status, error.config?.url);
            console.error('Error data:', error.response?.data);
            
            // If we get a CSRF error, clear the token and retry once
            if (error.response && error.response.status === 400 && 
                error.response.data && error.response.data.error === 'CSRF token validation failed') {
                console.log('CSRF token expired, clearing and will retry...');
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