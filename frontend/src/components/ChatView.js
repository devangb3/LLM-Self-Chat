import React, { useEffect, useRef } from 'react';
import { Box, Paper, Typography, Avatar, Chip } from '@mui/material';
import { amber, blue, green, deepPurple } from '@mui/material/colors';

const getAvatarColor = (senderId) => {
  // Simple hash function to get a color based on senderId
  let hash = 0;
  for (let i = 0; i < senderId.length; i++) {
    hash = senderId.charCodeAt(i) + ((hash << 5) - hash);
  }
  const colors = [amber[500], blue[500], green[500], deepPurple[500]];
  return colors[Math.abs(hash) % colors.length];
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
      <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', p: 2, minHeight: '60vh' }}>
        <Typography variant="subtitle1" color="text.secondary">
          No messages yet. Send a message to start the conversation!
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
        minHeight: '60vh',
        backgroundColor: '#f4f6fb',
        py: 3,
        px: { xs: 0, sm: 2 },
        overflowY: 'auto',
      }}
    >
      <Box
        sx={{
          width: '100%',
          maxWidth: 700,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {messages.map((msg, index) => {
          const isUserAuditor = msg.sender_type === 'auditor';
          const isLLM = msg.sender_type === 'llm';
          // Use msg.llm_name if available and sender is LLM, otherwise msg.sender_id
          const senderDisplayName = isLLM ? (msg.llm_name || msg.sender_id) : msg.sender_id;
          const avatarChar = senderDisplayName ? senderDisplayName.charAt(0).toUpperCase() : '?';
          const messageDate = msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : '';

          // Differentiate message background for user/auditor and LLM
          const paperBg = isUserAuditor
            ? 'primary.main'
            : isLLM
            ? 'white'
            : 'grey.100';
          const paperColor = isUserAuditor ? 'primary.contrastText' : 'text.primary';
          const borderRadius = isUserAuditor
            ? '20px 20px 5px 20px'
            : isLLM
            ? '20px 20px 20px 5px'
            : '20px';

          return (
            <Box
              key={msg._id || index}
              sx={{
                display: 'flex',
                justifyContent: isUserAuditor ? 'flex-end' : 'flex-start',
                width: '100%',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  flexDirection: isUserAuditor ? 'row-reverse' : 'row',
                  width: 'fit-content',
                  maxWidth: '90%',
                }}
              >
                {!isUserAuditor && (
                  <Avatar
                    sx={{
                      bgcolor: getAvatarColor(senderDisplayName),
                      mr: isUserAuditor ? 0 : 1,
                      ml: isUserAuditor ? 1 : 0,
                    }}
                  >
                    {avatarChar}
                  </Avatar>
                )}
                <Paper
                  elevation={isUserAuditor ? 3 : 1}
                  sx={{
                    p: 2,
                    bgcolor: paperBg,
                    color: paperColor,
                    borderRadius: borderRadius,
                    boxShadow: isUserAuditor ? 3 : 1,
                    minWidth: 0,
                    maxWidth: { xs: '80vw', sm: '500px' },
                    wordWrap: 'break-word',
                  }}
                >
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>{msg.content}</Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                    {!isUserAuditor && (
                      <Chip
                        label={senderDisplayName}
                        size="small"
                        sx={{
                          mr: 1,
                          backgroundColor: getAvatarColor(senderDisplayName),
                          color: 'white',
                        }}
                      />
                    )}
                    <Typography
                      variant="caption"
                      color={isUserAuditor ? 'rgba(255,255,255,0.7)' : 'text.secondary'}
                      sx={{ ml: isUserAuditor ? 0 : 'auto' }}
                    >
                      {messageDate}
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            </Box>
          );
        })}
        <div ref={endOfMessagesRef} />
      </Box>
    </Box>
  );
};

export default ChatView; 