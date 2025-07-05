import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    Box, 
    Paper, 
    Typography, 
    CircularProgress, 
    Alert, 
    IconButton, 
    Divider, 
    Button,
    Drawer,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    AppBar,
    Toolbar,
    CssBaseline,
    useTheme
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SettingsIcon from '@mui/icons-material/Settings';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import LogoutIcon from '@mui/icons-material/Logout';

import { ColorModeContext } from '../contexts/ThemeContext';

import ChatView from '../components/ChatView';
import ConversationList from '../components/ConversationList';
import SystemPromptModal from '../components/SystemPromptModal';
import CreateConversationDialog from '../components/CreateConversationDialog';

import { getSocket } from '../services/socket';
import * as api from '../services/api';
import authService from '../services/authService';

const drawerWidth = 280;

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
    const [mobileOpen, setMobileOpen] = useState(false);
    
    const socket = useRef(null);
    const theme = useTheme();
    const colorMode = React.useContext(ColorModeContext);

    const handleSignOut = () => {
        authService.logout();
        navigate('/login');
    };

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
            setCurrentConversation(null);
            setMessages([]);
            setSystemPrompt('');
            return;
        }
        
        try {
            setLoading(true);
            const response = await api.getConversationDetails(convId);
            setCurrentConversation(response.data);
            setMessages(response.data.messages || []);
            setSystemPrompt(response.data.system_prompt || '');
            setError(null);
        } catch (err) {
            setError(err.response?.data?.error || `Failed to fetch conversation ${convId}`);
            console.error("Fetch conversation details error:", err);
            setCurrentConversation(null);
            setMessages([]);
            if (convId === paramConvId) navigate('/chat', { replace: true }); 
        } finally {
            setLoading(false);
        }
    }, [navigate, paramConvId]);

    useEffect(() => {
        fetchConversations();
    }, [fetchConversations]);

    useEffect(() => {
        if (paramConvId) {
            fetchConversationDetails(paramConvId);
        } else {
            setCurrentConversation(null);
            setMessages([]);
            setSystemPrompt('');
        }
    }, [paramConvId, fetchConversationDetails]);

    useEffect(() => {
        socket.current = getSocket();

        const handleMessageUpdate = (newMessage) => {
            if (currentConversation && newMessage.conversation_id === currentConversation.id) {
                setMessages((prevMessages) => [...prevMessages, newMessage]);
            }
        };

        const handleSystemPromptUpdated = (data) => {
            if (currentConversation && data.conversation_id === currentConversation.id && data.prompt !== undefined) { 
                setSystemPrompt(data.prompt);
                setCurrentConversation(prev => (prev ? {...prev, system_prompt: data.prompt} : null));
            }
        };

        socket.current.on('message_update', handleMessageUpdate);
        socket.current.on('system_prompt_updated', handleSystemPromptUpdated);
        socket.current.on('error', (err) => {
            setError(err.message || 'A socket error occurred.');
        });

        return () => {
            socket.current.off('message_update', handleMessageUpdate);
            socket.current.off('system_prompt_updated', handleSystemPromptUpdated);
            socket.current.off('error');
        };
    }, [currentConversation]);

    const handleTriggerNextLLM = () => {
        if (!currentConversation || !currentConversation.id) {
            setError('Please select a conversation first.');
            return;
        }
        const socket = getSocket();
        socket.emit('trigger_next_llm', { conversation_id: currentConversation.id });
    };

    const handleSelectConversation = (convId) => {
        if (convId) {
            navigate(`/chat/${convId}`);
            if (mobileOpen) setMobileOpen(false);
        }
    };

    const handleCreateConversation = async (convData) => {
        try {
            setLoading(true);
            const response = await api.createConversation(convData);
            await fetchConversations();
            if (response.data && response.data.id) {
                navigate(`/chat/${response.data.id}`);
            } else {
                setError('Failed to create conversation: No ID returned');
            }
            setIsCreateConvDialogOpen(false);
            setError(null);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to create conversation');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteConversation = async (conversationId) => {
        try {
            setLoading(true);
            await api.deleteConversation(conversationId);
            setConversations(prev => prev.filter(conv => conv.id !== conversationId));
            if (currentConversation && currentConversation.id === conversationId) {
                setCurrentConversation(null);
                setMessages([]);
                navigate('/chat');
            }
            setError(null);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to delete conversation');
        } finally {
            setLoading(false);
        }
    };
    
    const handleSetSystemPrompt = (newPrompt) => {
        if (!currentConversation || !socket.current) return;
        socket.current.emit('set_system_prompt', {
            conversation_id: currentConversation.id, 
            prompt: newPrompt 
        });
        setIsSystemPromptModalOpen(false);
    };

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const drawerContent = (
        <div>
            <Toolbar />
            <Divider />
            <List>
                <ListItem button onClick={() => setIsCreateConvDialogOpen(true)}>
                    <ListItemIcon>
                        <AddCircleOutlineIcon />
                    </ListItemIcon>
                    <ListItemText primary="New Conversation" />
                </ListItem>
            </List>
            <Divider />
            {loading && conversations.length === 0 && <CircularProgress sx={{m: 2}}/>}
            {error && !conversations.length && <Alert severity="error" sx={{m:2}}>{error}</Alert>}
            <ConversationList 
                conversations={conversations} 
                selectedConversationId={currentConversation?.id}
                onSelectConversation={handleSelectConversation}
                onDeleteConversation={handleDeleteConversation}
            />
        </div>
    );

    return (
        <Box sx={{ display: 'flex' }}>
            <CssBaseline />
            <AppBar
                position="fixed"
                sx={{
                    width: { sm: `calc(100% - ${drawerWidth}px)` },
                    ml: { sm: `${drawerWidth}px` },
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{ mr: 2, display: { sm: 'none' } }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
                        {currentConversation ? `Chat with: ${currentConversation.llm_participants?.join(', ') || 'N/A'}` : 'LLM Auditor Chat'}
                    </Typography>
                    <IconButton sx={{ ml: 1 }} onClick={colorMode.toggleColorMode} color="inherit">
                        {theme.palette.mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
                    </IconButton>
                    <Button color="inherit" onClick={handleSignOut} startIcon={<LogoutIcon />}>
                        Sign Out
                    </Button>
                </Toolbar>
            </AppBar>
            <Box
                component="nav"
                sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
                aria-label="mailbox folders"
            >
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{
                        keepMounted: true, // Better open performance on mobile.
                    }}
                    sx={{
                        display: { xs: 'block', sm: 'none' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                    }}
                >
                    {drawerContent}
                </Drawer>
                <Drawer
                    variant="permanent"
                    sx={{
                        display: { xs: 'none', sm: 'block' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                    }}
                    open
                >
                    {drawerContent}
                </Drawer>
            </Box>
            <Box
                component="main"
                sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` } }}
            >
                <Toolbar />
                {currentConversation ? (
                    <Paper elevation={0} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px - 48px)', p:0}}>
                        <ChatView messages={messages} currentUser="auditor" />
                        <Box sx={{ p: 2, borderTop: '1px solid divider', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                            <Button 
                                variant="contained" 
                                onClick={handleTriggerNextLLM}
                                startIcon={<PlayArrowIcon />}
                                sx={{mr: 2}}
                                disabled={loading || !currentConversation?.llm_participants?.length}
                            >
                                Next LLM
                            </Button>
                            <IconButton onClick={() => setIsSystemPromptModalOpen(true)} title="Set System Prompt">
                                <SettingsIcon />
                            </IconButton>
                        </Box>
                    </Paper>
                ) : (
                    <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
                        {loading ? <CircularProgress /> : 
                            error ? <Alert severity="error">{error}</Alert> :
                            <Typography variant="h6">Select a conversation to start chatting or create a new one.</Typography>
                        }
                    </Box>
                )}
            </Box>

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
                availableLLMs={["claude", "gemini", "chatgpt", "deepseek"]}
            />
        </Box>
    );
};

export default ChatPage;
 