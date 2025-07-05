import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Button,
  Typography,
  Box
} from '@mui/material';

const SystemPromptModal = ({ open, onClose, currentPrompt, onSetPrompt, disabled }) => {
  const [prompt, setPrompt] = useState(currentPrompt || '');

  useEffect(() => {
    if (open) {
      setPrompt(currentPrompt || '');
    }
  }, [currentPrompt, open]);

  const handleSet = () => {
    onSetPrompt(prompt);
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>
        <Typography variant="h6" component="div">
          System Prompt
        </Typography>
      </DialogTitle>
      <DialogContent dividers>
        <Box component="form" noValidate autoComplete="off">
          <TextField
            autoFocus
            margin="dense"
            id="system-prompt"
            label="System Prompt"
            type="text"
            fullWidth
            multiline
            rows={8}
            variant="outlined"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={disabled}
            helperText="This prompt guides the behavior of the LLMs in the conversation."
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: '16px 24px' }}>
        <Button onClick={onClose} color="secondary">Cancel</Button>
        <Button onClick={handleSet} variant="contained" disabled={disabled || prompt === currentPrompt}>
          Set Prompt
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SystemPromptModal; 