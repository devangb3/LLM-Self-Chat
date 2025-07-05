import io from 'socket.io-client';
import authService from './authService';

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5001';

let socket;

export const getSocket = () => {
  if (!socket) {
    const accessToken = authService.getAccessToken();
    
    if (!accessToken) {
      console.warn('No access token available for WebSocket connection');
      return null;
    }

    if (authService.isTokenExpired()) {
      console.warn('Access token is expired');
      authService.logout();
      return null;
    }

    socket = io(SOCKET_URL, {
      query: {
        token: accessToken
      },
      autoConnect: true,
      transports: ['websocket', 'polling']
    });

    socket.on('connect', () => {
      console.log('Socket connected:', socket.id);
    });

    socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
    });

    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      if (error.message === 'Authentication required') {
        console.log('Authentication failed, clearing tokens');
        authService.logout();
        window.location.href = '/login';
      }
    });

    socket.on('response', (data) => {
      console.log('Socket event "response":', data);
      if (data.authenticated === false) {
        console.warn('WebSocket connection not authenticated');
      }
    });

    socket.on('error', (error) => {
      console.error('Socket error:', error);
      if (error.message === 'Authentication required') {
        console.log('Authentication failed, clearing tokens');
        authService.logout();
        window.location.href = '/login';
      }
    });
  }
  return socket;
};

export const disconnectSocket = () => {
  if (socket && socket.connected) {
    socket.disconnect();
    console.log('Socket explicitly disconnected.');
  }
  socket = null;
};

export const reconnectSocket = () => {
  disconnectSocket();
  return getSocket();
};

export const getAuthenticatedSocket = () => {
  if (!authService.isAuthenticated()) {
    console.warn('User not authenticated, cannot create WebSocket connection');
    return null;
  }
  
  if (authService.isTokenExpired()) {
    console.warn('Token expired, cannot create WebSocket connection');
    authService.logout();
    return null;
  }
  
  return getSocket();
};

// export const sendMessage = (messageData) => {
//   const currentSocket = getSocket();
//   if (currentSocket) {
//     currentSocket.emit('new_message', messageData);
//   }
// };

// export const onMessageUpdate = (callback) => {
//   const currentSocket = getSocket();
//   if (currentSocket) {
//     currentSocket.on('message_update', callback);
//     return () => currentSocket.off('message_update', callback); // Cleanup function
//   }
//   return () => {}; // Return an empty cleanup if socket isn't ready
// }; 