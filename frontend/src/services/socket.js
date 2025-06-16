import io from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5001';

let socket;

export const getSocket = () => {
  if (!socket) {
    socket = io(SOCKET_URL, {
      // transports: ['websocket'], // Optional: forces websocket transport
      // autoConnect: false, // Optional: manage connection manually
    });

    socket.on('connect', () => {
      console.log('Socket connected:', socket.id);
    });

    socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
    });

    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
    });

    socket.on('response', (data) => {
      console.log('Socket event "response":', data);
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