import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
  Button,
} from '@mui/material';

const SystemPromptModal = ({ open, onClose, currentPrompt, onSetPrompt, disabled }) => {
  const [prompt, setPrompt] = useState(currentPrompt || '');

  useEffect(() => {
    // Update internal state if the currentPrompt prop changes (e.g., when conversation changes)
    setPrompt(currentPrompt || '');
  }, [currentPrompt, open]); // also re-sync when modal opens

  const handleSet = () => {
    onSetPrompt(prompt);
    // onClose(); // Usually handled by parent after successful submission in ChatPage
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>Set System Prompt</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{mb: 2}}>
          Set the system prompt that will guide the behavior of the LLMs in this conversation.
        </DialogContentText>
        <TextField
          autoFocus
          margin="dense"
          id="system-prompt"
          label="System Prompt"
          type="text"
          fullWidth
          multiline
          rows={6}
          variant="outlined"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={disabled}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSet} variant="contained" disabled={disabled || prompt === currentPrompt}>
          Set Prompt
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SystemPromptModal; 