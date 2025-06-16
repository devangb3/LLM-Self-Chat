import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Grid, Paper, Typography, CircularProgress, Alert, IconButton, Divider, Button } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings'; // For system prompt modal
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'; // For new conversation
import PlayArrowIcon from '@mui/icons-material/PlayArrow'; // For "Next LLM" button

import ChatView from '../components/ChatView';
import ConversationList from '../components/ConversationList';
import SystemPromptModal from '../components/SystemPromptModal';
import CreateConversationDialog from '../components/CreateConversationDialog';

import { getSocket } from '../services/socket';
import * as api from '../services/api';

const ChatPage = () => {
  const { conversationId: paramConvId } = useParams();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [systemPrompt, setSystemPrompt] = useState('');

  const [isSystemPromptModalOpen, setIsSystemPromptModalOpen] = useState(false);
  const [isCreateConvDialogOpen, setIsCreateConvDialogOpen] = useState(false);
  
  const socket = useRef(null);

  const fetchConversations = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.getConversations();
      setConversations(response.data || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch conversations');
      console.error("Fetch conversations error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchConversationDetails = useCallback(async (convId) => {
    if (!convId) {
      console.log("[ChatPage] fetchConversationDetails: No convId provided, clearing state");
      setCurrentConversation(null);
      setMessages([]);
      setSystemPrompt('');
      return;
    }
    
    console.log("[ChatPage] fetchConversationDetails: Fetching details for convId:", convId, "Type:", typeof convId);
    try {
      setLoading(true);
      const response = await api.getConversationDetails(convId);
      console.log("[ChatPage] fetchConversationDetails: Response:", response.data);
      setCurrentConversation(response.data);
      setMessages(response.data.messages || []);
      setSystemPrompt(response.data.system_prompt || '');
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || `Failed to fetch conversation ${convId}`);
      console.error("Fetch conversation details error:", err);
      setCurrentConversation(null); // Reset if fetch fails
      setMessages([]);
      // If the failed convId was from the URL param, navigate away to a clean state
      if (convId === paramConvId) navigate('/chat', { replace: true }); 
    } finally {
      setLoading(false);
    }
  }, [navigate, paramConvId]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    // This effect specifically handles fetching details when the URL parameter (paramConvId) changes.
    if (paramConvId) {
        console.log("[ChatPage] useEffect[paramConvId]: URL parameter detected:", paramConvId);
        fetchConversationDetails(paramConvId);
    } else {
        // If there's no conversation ID in the URL, ensure we clear out any existing selected conversation details.
        // This handles navigating from /chat/some-id to /chat.
        console.log("[ChatPage] useEffect[paramConvId]: No URL parameter, clearing current conversation details.");
        setCurrentConversation(null);
        setMessages([]);
        setSystemPrompt('');
    }
  }, [paramConvId, fetchConversationDetails]);

  useEffect(() => {
    socket.current = getSocket();

    const handleMessageUpdate = (newMessage) => {
      console.log('Received message_update:', newMessage);
      // Check if the message belongs to the current conversation
      if (currentConversation && newMessage.conversation_id === currentConversation.id) {
        setMessages((prevMessages) => [...prevMessages, newMessage]);
      }
    };

    const handleSystemPromptUpdated = (data) => {
        console.log('Received system_prompt_updated:', data);
        // Ensure update is for the current conversation and data is valid
        if (currentConversation && data.conversation_id === currentConversation.id && data.prompt !== undefined) { 
            setSystemPrompt(data.prompt);
            // Optionally update the conversation object itself if it holds the system prompt
            setCurrentConversation(prev => (prev ? {...prev, system_prompt: data.prompt} : null));
        }
    };

    socket.current.on('message_update', handleMessageUpdate);
    socket.current.on('system_prompt_updated', handleSystemPromptUpdated);
    socket.current.on('error', (err) => {
        console.error("Socket error received:", err);
        setError(err.message || 'A socket error occurred.');
    });

    return () => {
      socket.current.off('message_update', handleMessageUpdate);
      socket.current.off('system_prompt_updated', handleSystemPromptUpdated);
      socket.current.off('error');
      // Consider if socket needs to be disconnected here or managed globally
    };
  }, [currentConversation, fetchConversationDetails]);

  const handleTriggerNextLLM = () => {
    if (!currentConversation || !currentConversation.id) {
        setError('Please select a conversation first.');
        return;
    }
    const socket = getSocket();
    console.log(`Emitting trigger_next_llm for conversation_id: ${currentConversation.id}`);
    socket.emit('trigger_next_llm', { conversation_id: currentConversation.id });
  };

  const handleSelectConversation = (convId) => {
    if (convId) {
        console.log("[ChatPage] handleSelectConversation: Selected convId:", convId, "Type:", typeof convId);
        navigate(`/chat/${convId}`);
    }
  };

  const handleCreateConversation = async (convData) => {
    try {
      setLoading(true);
      const response = await api.createConversation(convData);
      console.log('Create conversation response:', response.data); // Debug log
      
      await fetchConversations();
      
      if (response.data && response.data.id) {
        navigate(`/chat/${response.data.id}`);
      } else {
        console.error('No conversation ID in response:', response.data);
        setError('Failed to create conversation: No ID returned');
      }
      
      setIsCreateConvDialogOpen(false);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create conversation');
      console.error("Create conversation error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConversation = async (conversationId) => {
    try {
      console.log('Deleting conversation:', conversationId); // Debug log
      setLoading(true);
      const response = await api.deleteConversation(conversationId);
      console.log('Delete response:', response); // Debug log
      
      setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation(null);
        setMessages([]);
        navigate('/chat');
      }
      
      setError(null);
    } catch (err) {
      console.error('Delete conversation error:', err);
      setError(err.response?.data?.error || 'Failed to delete conversation');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSetSystemPrompt = (newPrompt) => {
    if (!currentConversation || !socket.current) return;
    console.log(`Setting system prompt for ${currentConversation.id} to: ${newPrompt}`);
    socket.current.emit('set_system_prompt', {
        conversation_id: currentConversation.id, 
        prompt: newPrompt 
    });
    setIsSystemPromptModalOpen(false);
  };

  if (loading && !currentConversation && !conversations.length) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}><CircularProgress /></Box>;
  }

  return (
    <Box sx={{ flexGrow: 1, display: 'flex', height: 'calc(100vh - 64px - 50px)' }}> {/* Adjust height based on AppBar/Footer */} 
      <Grid container spacing={0} sx={{ height: '100%' }}>
        <Grid item xs={12} sm={4} md={3} sx={{ 
            borderRight: { sm: '1px solid divider' }, 
            display: 'flex', 
            flexDirection: 'column', 
            height: '100%'
        }}>
          <Paper elevation={1} sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <Typography variant="h6">Conversations</Typography>
            <IconButton onClick={() => setIsCreateConvDialogOpen(true)} title="New Conversation">
                <AddCircleOutlineIcon />
            </IconButton>
          </Paper>
          <Divider />
          {loading && conversations.length === 0 && <CircularProgress sx={{m: 2}}/>}
          {error && !conversations.length && <Alert severity="error" sx={{m:2}}>{error}</Alert>}
          <ConversationList 
            conversations={conversations} 
            selectedConversationId={currentConversation?.id}
            onSelectConversation={handleSelectConversation}
            onDeleteConversation={handleDeleteConversation}
          />
        </Grid>

        <Grid item xs={12} sm={8} md={9} sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          {currentConversation ? (
            <Paper elevation={0} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', p:0}}>
              <Box sx={{p: 2, borderBottom: '1px solid divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <Typography variant="h6">
                  Chat with: {currentConversation.llm_participants?.join(', ') || 'N/A'}
                </Typography>
                <IconButton onClick={() => setIsSystemPromptModalOpen(true)} title="Set System Prompt">
                    <SettingsIcon />
                </IconButton>
              </Box>
              <ChatView messages={messages} currentUser="auditor" />
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%', padding: 1 }}>
                <Button 
                    variant="contained" 
                    onClick={handleTriggerNextLLM}
                    startIcon={<PlayArrowIcon />}
                    sx={{mr: 2}}
                    disabled={loading || !currentConversation?.llm_participants?.length}
                >
                    Next LLM
                </Button>
                <Button 
                    variant="outlined" 
                    onClick={() => {
                        setSystemPrompt(systemPrompt);
                        setIsSystemPromptModalOpen(true);
                    }}
                    startIcon={<SettingsIcon />}
                >
                    Set System Prompt
                </Button>
              </Box>
            </Paper>
          ) : (
            <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column' }}>
              {loading ? <CircularProgress /> : 
                error ? <Alert severity="error">{error}</Alert> :
                <Typography variant="h6">Select a conversation to start chatting or create a new one.</Typography>
              }
            </Box>
          )}
        </Grid>
      </Grid>

      <SystemPromptModal 
        open={isSystemPromptModalOpen} 
        onClose={() => setIsSystemPromptModalOpen(false)} 
        currentPrompt={systemPrompt} 
        onSetPrompt={handleSetSystemPrompt} 
        disabled={!currentConversation}
      />
      <CreateConversationDialog
        open={isCreateConvDialogOpen}
        onClose={() => setIsCreateConvDialogOpen(false)}
        onCreate={handleCreateConversation}
        availableLLMs={["claude", "gemini", "chatgpt", "deepseek"]} // Should come from backend ideally
      />
      {error && <Alert severity="error" sx={{mt: 2, position: 'fixed', bottom: 60, left: '50%', transform: 'translateX(-50%)'}}>{error}</Alert>}
    </Box>
  );
};

export default ChatPage; 