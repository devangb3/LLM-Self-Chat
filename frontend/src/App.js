import React from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import ApiKeyManager from './components/ApiKeyManager';
import authService from './services/authService';
import ChatPage from './pages/ChatPage';
import { Box, AppBar, Toolbar, Typography, Container, Button } from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';

function MainLayout({ children }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authService.logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            LLM Auditor Chat
          </Typography>
          <Button 
            color="inherit" 
            onClick={handleLogout}
            startIcon={<LogoutIcon />}
          >
            Logout
          </Button>
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

// Protected Route component
const ProtectedRoute = ({ children }) => {
    const isAuthenticated = authService.isAuthenticated();
    if (!isAuthenticated) {
        return <Navigate to="/login" />;
    }
    return children;
};

function App() {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
                path="/api-keys"
                element={
                    <ProtectedRoute>
                        <MainLayout>
                            <ApiKeyManager />
                        </MainLayout>
                    </ProtectedRoute>
                }
            />
            <Route 
                path="/chat" 
                element={
                    <ProtectedRoute>
                        <MainLayout>
                            <ChatPage />
                        </MainLayout>
                    </ProtectedRoute>
                } 
            />
            <Route 
                path="/chat/:conversationId" 
                element={
                    <ProtectedRoute>
                        <MainLayout>
                            <ChatPage />
                        </MainLayout>
                    </ProtectedRoute>
                } 
            />
            <Route path="*" element={<Navigate to="/api-keys" />} />
        </Routes>
    );
}

export default App;
