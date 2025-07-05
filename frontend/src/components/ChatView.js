import React, { useEffect, useRef } from 'react';
import { Box, Paper, Typography, Avatar, Chip, Stack } from '@mui/material';
import { blue, green, purple, orange } from '@mui/material/colors';

const stringToColor = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    let color = '#';
    for (let i = 0; i < 3; i++) {
        const value = (hash >> (i * 8)) & 0xFF;
        color += ('00' + value.toString(16)).substr(-2);
    }
    return color;
};

const ChatView = ({ messages, currentUser }) => {
    const endOfMessagesRef = useRef(null);

    const scrollToBottom = () => {
        endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    if (!messages || messages.length === 0) {
        return (
            <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                    No messages yet.
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
            <Stack spacing={2}>
                {messages.map((msg, index) => {
                    const isUser = msg.sender_type === 'auditor';
                    const senderName = isUser ? 'Auditor' : msg.llm_name || 'LLM';
                    const avatarColor = isUser ? blue[500] : stringToColor(senderName);
                    
                    return (
                        <Box
                            key={msg.id || index}
                            sx={{
                                display: 'flex',
                                justifyContent: isUser ? 'flex-end' : 'flex-start',
                            }}
                        >
                            <Box sx={{ display: 'flex', alignItems: 'flex-start', maxWidth: '80%' }}>
                                {!isUser && (
                                    <Avatar sx={{ bgcolor: avatarColor, mr: 1.5 }}>
                                        {senderName.charAt(0).toUpperCase()}
                                    </Avatar>
                                )}
                                <Paper
                                    elevation={1}
                                    sx={{
                                        p: 1.5,
                                        bgcolor: isUser ? 'primary.main' : 'background.paper',
                                        color: isUser ? 'primary.contrastText' : 'text.primary',
                                        borderRadius: isUser ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
                                    }}
                                >
                                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                                        {msg.content}
                                    </Typography>
                                    <Typography
                                        variant="caption"
                                        sx={{
                                            display: 'block',
                                            textAlign: 'right',
                                            mt: 0.5,
                                            color: isUser ? 'rgba(255,255,255,0.7)' : 'text.secondary',
                                        }}
                                    >
                                        {new Date(msg.created_at).toLocaleTimeString()}
                                    </Typography>
                                </Paper>
                                {isUser && (
                                    <Avatar sx={{ bgcolor: avatarColor, ml: 1.5 }}>
                                        A
                                    </Avatar>
                                )}
                            </Box>
                        </Box>
                    );
                })}
            </Stack>
            <div ref={endOfMessagesRef} />
        </Box>
    );
};

export default ChatView; 