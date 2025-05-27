import React from 'react';
import {
  Routes,
  Route,
  Navigate
} from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import { Box, AppBar, Toolbar, Typography, Container } from '@mui/material';

// Basic Layout Structure
function MainLayout({ children }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            LLM Auditor Chat
          </Typography>
        </Toolbar>
      </AppBar>
      <Container component="main" sx={{ flexGrow: 1, py: 3}}>
        {children}
      </Container>
      <Box component="footer" sx={{ py: 2, textAlign: 'center', backgroundColor: 'primary.main', color: 'white' }}>
        <Typography variant="body2">
          LLM Chat Application &copy; {new Date().getFullYear()}
        </Typography>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:conversationId" element={<ChatPage />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </MainLayout>
  );
}

export default App;
