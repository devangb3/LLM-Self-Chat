import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogActions,
  DialogContent,
  Typography,
  DialogTitle,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  Box,
  MenuItem,
  Checkbox,
  ListItemText,
  OutlinedInput,
  Switch,
  FormControlLabel
} from '@mui/material';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const CreateConversationDialog = ({ open, onClose, onCreate, availableLLMs }) => {
  const [conversationName, setConversationName] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful assistant.');
  const [selectedLLMs, setSelectedLLMs] = useState([availableLLMs[0] || 'chatgpt']);
  const [startConversation, setStartConversation] = useState(true);

  useEffect(() => {
    if (open) {
      setConversationName('');
      setSystemPrompt('You are a helpful assistant.');
      setSelectedLLMs([availableLLMs[0] || 'chatgpt']);
      setStartConversation(true);
    }
  }, [open, availableLLMs]);

  const handleCreate = () => {
    if (selectedLLMs.length === 0) {
        alert("Please select at least one LLM participant.")
        return;
    }
    onCreate({
      name: conversationName.trim() || null,
      system_prompt: systemPrompt,
      llm_participants: selectedLLMs,
      start_conversation: startConversation,
    });
  };

  const handleLLMChange = (event) => {
    const { target: { value } } = event;
    setSelectedLLMs(
      typeof value === 'string' ? value.split(',') : value,
    );
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>
        <Typography variant="h6" component="div">
          New Conversation
        </Typography>
      </DialogTitle>
      <DialogContent dividers>
        <Box component="form" noValidate autoComplete="off">
          <TextField
            autoFocus
            margin="dense"
            id="conversation-name"
            label="Conversation Name (Optional)"
            type="text"
            fullWidth
            variant="outlined"
            value={conversationName}
            onChange={(e) => setConversationName(e.target.value)}
            sx={{ mb: 3 }}
          />
          <TextField
            margin="dense"
            id="new-system-prompt"
            label="System Prompt"
            type="text"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            sx={{ mb: 3 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="llm-participants-label">LLM Participants</InputLabel>
            <Select
              labelId="llm-participants-label"
              id="llm-participants-select"
              multiple
              value={selectedLLMs}
              onChange={handleLLMChange}
              input={<OutlinedInput label="LLM Participants" />}
              renderValue={(selected) => selected.join(', ')}
              MenuProps={MenuProps}
            >
              {availableLLMs.map((name) => (
                <MenuItem key={name} value={name}>
                  <Checkbox checked={selectedLLMs.indexOf(name) > -1} />
                  <ListItemText primary={name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControlLabel
              control={<Switch checked={startConversation} onChange={(e) => setStartConversation(e.target.checked)} />}
              label="Let the first LLM start the conversation"
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: '16px 24px' }}>
        <Button onClick={onClose} color="secondary">Cancel</Button>
        <Button onClick={handleCreate} variant="contained" disabled={selectedLLMs.length === 0}>
          Create
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateConversationDialog; 