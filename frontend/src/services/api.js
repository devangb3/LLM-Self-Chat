import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Conversation Endpoints
export const createConversation = (data) => apiClient.post('/conversations', data);
export const getConversations = () => apiClient.get('/conversations');
export const getConversationDetails = (conversationId) => apiClient.get(`/conversations/${conversationId}`);

// Potentially other endpoints can be added here, e.g., for user authentication if needed later.

export default apiClient; 