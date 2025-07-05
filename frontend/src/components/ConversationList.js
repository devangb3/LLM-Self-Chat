import React from 'react';
import { List, ListItem, ListItemButton, ListItemText, Typography, Box, Tooltip, IconButton, Divider, ListItemIcon } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import ChatIcon from '@mui/icons-material/Chat';

const ConversationList = ({ conversations, selectedConversationId, onSelectConversation, onDeleteConversation }) => {

  if (!conversations || conversations.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No conversations yet.
        </Typography>
      </Box>
    );
  }

  const handleDelete = (e, conversationId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      onDeleteConversation(conversationId);
    }
  };

  return (
    <List sx={{ overflowY: 'auto', flexGrow: 1, p: 0 }}>
      {conversations.map((conv) => (
        <React.Fragment key={conv.id}>
          <ListItem
            disablePadding
            secondaryAction={
              <IconButton 
                edge="end" 
                aria-label="delete"
                onClick={(e) => handleDelete(e, conv.id)}
              >
                <DeleteIcon />
              </IconButton>
            }
          >
            <ListItemButton 
              selected={selectedConversationId === conv.id}
              onClick={() => onSelectConversation(conv.id)}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.light',
                  color: 'primary.contrastText',
                  '&:hover': {
                    backgroundColor: 'primary.main',
                  }
                }
              }}
            >
              <ListItemIcon sx={{minWidth: 36, color: 'inherit'}}>
                <ChatIcon />
              </ListItemIcon>
              <ListItemText 
                primary={conv.name || `Conversation`}
                secondary={conv.llm_participants?.join(', ')}
                primaryTypographyProps={{ noWrap: true, fontWeight: 'medium' }} 
                secondaryTypographyProps={{ noWrap: true }}
              />
            </ListItemButton>
          </ListItem>
          <Divider variant="inset" component="li" />
        </React.Fragment>
      ))}
    </List>
  );
};

export default ConversationList; 