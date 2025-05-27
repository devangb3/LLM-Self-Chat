import React from 'react';
import { List, ListItem, ListItemButton, ListItemText, Typography, Box, Tooltip } from '@mui/material';

const ConversationList = ({ conversations, selectedConversationId, onSelectConversation }) => {
  if (!conversations || conversations.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="subtitle2" color="text.secondary">
          No conversations yet. Click the '+' icon to create one.
        </Typography>
      </Box>
    );
  }

  return (
    <List sx={{ overflowY: 'auto', flexGrow: 1, p: 0 }}>
      {conversations.map((conv) => (
        <ListItem key={conv.id} disablePadding>
          <ListItemButton 
            selected={selectedConversationId === conv.id}
            onClick={() => onSelectConversation(conv.id)}
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
      ))}
    </List>
  );
};

export default ConversationList; 