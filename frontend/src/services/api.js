import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for debugging
apiClient.interceptors.response.use(
  response => {
    if (response.config.url.includes('/conversations')) {
      console.log('Conversation API Response:', {
        method: response.config.method.toUpperCase(),
        url: response.config.url,
        data: response.data,
        conversationIds: Array.isArray(response.data) 
          ? response.data.map(conv => conv._id || conv.id)
          : response.data._id || response.data.id
      });
    }
    return response;
  },
  error => {
    console.error('API Error:', error.config.method.toUpperCase(), error.config.url, error.response?.data);
    return Promise.reject(error);
  }
);

// Conversation Endpoints
export const createConversation = (data) => apiClient.post('/conversations', data);
export const getConversations = () => apiClient.get('/conversations');
export const getConversationDetails = (conversationId) => apiClient.get(`/conversations/${conversationId}`);
export const deleteConversation = (conversationId) => apiClient.delete(`/conversations/${conversationId}`);

// Potentially other endpoints can be added here, e.g., for user authentication if needed later.

export default apiClient; 