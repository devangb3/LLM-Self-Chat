import React from 'react';
import { List, ListItem, ListItemButton, ListItemText, Typography, Box, Tooltip, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

const ConversationList = ({ conversations, selectedConversationId, onSelectConversation, onDeleteConversation }) => {
  console.log('ConversationList props:', { conversations, selectedConversationId }); // Debug log

  if (!conversations || conversations.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="subtitle2" color="text.secondary">
          No conversations yet. Click the '+' icon to create one.
        </Typography>
      </Box>
    );
  }

  const handleDelete = (e, conversationId) => {
    e.stopPropagation(); // Prevent triggering the ListItemButton click
    console.log('Delete clicked for conversation:', conversationId); // Debug log
    if (window.confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
      onDeleteConversation(conversationId);
    }
  };

  const handleSelect = (conversationId) => {
    console.log('Select clicked for conversation:', conversationId); // Debug log
    onSelectConversation(conversationId);
  };

  return (
    <List sx={{ overflowY: 'auto', flexGrow: 1, p: 0 }}>
      {conversations.map((conv) => {
        // Ensure we have a valid id
        if (!conv.id) {
          console.error('Conversation missing id:', conv);
          return null;
        }
        
        return (
          <ListItem
            key={conv.id}
            disablePadding
            secondaryAction={
              <IconButton 
                edge="end" 
                aria-label="delete"
                onClick={(e) => handleDelete(e, conv.id)}
                size="small"
                sx={{ 
                  opacity: 0.7,
                  '&:hover': {
                    opacity: 1,
                    color: 'error.main'
                  }
                }}
              >
                <DeleteIcon />
              </IconButton>
            }
          >
            <ListItemButton 
              selected={selectedConversationId === conv.id}
              onClick={() => handleSelect(conv.id)}
            >
              <ListItemText 
                primaryTypographyProps={{ noWrap: true }} 
                secondaryTypographyProps={{ noWrap: true, component: 'span' }}
                primary={conv.name || `Chat with ${conv.llm_participants?.join(', ') || 'N/A'}`}
                secondary={
                  <Tooltip title={conv.system_prompt}>
                    <Typography variant="body2" noWrap component="span">
                      System: {conv.system_prompt ? `${conv.system_prompt.substring(0, 30)}...` : 'Default'}
                    </Typography>
                  </Tooltip>
                }
              />
            </ListItemButton>
          </ListItem>
        );
      })}
    </List>
  );
};

export default ConversationList; 