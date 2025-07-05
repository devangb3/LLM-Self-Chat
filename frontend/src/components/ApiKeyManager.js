import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import {
    Container,
    Box,
    Typography,
    TextField,
    Button,
    Alert,
    Paper,
    Grid,
    Chip
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const ApiKeyManager = () => {
    const [apiKeys, setApiKeys] = useState({
        claude_api_key: '',
        gemini_api_key: '',
        openai_api_key: '',
        deepseek_api_key: ''
    });
    const [availableModels, setAvailableModels] = useState({});
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        loadUserInfo();
    }, []);

    const loadUserInfo = async () => {
        try {
            const userInfo = await authService.getUserInfo();
            setAvailableModels(userInfo.available_models);
        } catch (err) {
            setError('Failed to load user information');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await authService.updateApiKeys(apiKeys);
            setMessage('API keys updated successfully');
            setError('');
            await loadUserInfo();
            // Redirect to home page after a short delay
            setTimeout(() => {
                navigate('/chat');
            }, 1000);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to update API keys');
            setMessage('');
        }
    };

    const handleSkip = () => {
        navigate('/chat');
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setApiKeys(prev => ({
            ...prev,
            [name]: value
        }));
    };

    return (
        <Container maxWidth="md">
            <Paper sx={{ p: 4, mt: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Manage API Keys
                </Typography>
                
                {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

                <Box component="form" onSubmit={handleSubmit} noValidate>
                    <Grid container spacing={3}>
                        {Object.entries(apiKeys).map(([key, value]) => {
                            const modelName = key.replace('_api_key', '');
                            const isAvailable = availableModels[modelName];
                            
                            return (
                                <Grid item xs={12} sm={6} key={key}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        <Typography variant="h6" component="h2">
                                            {modelName.charAt(0).toUpperCase() + modelName.slice(1)}
                                        </Typography>
                                        {isAvailable && (
                                            <Chip 
                                                icon={<CheckCircleIcon />} 
                                                label="Available" 
                                                color="success" 
                                                size="small" 
                                                sx={{ ml: 1 }} 
                                            />
                                        )}
                                    </Box>
                                    <TextField
                                        type="password"
                                        fullWidth
                                        name={key}
                                        value={value}
                                        onChange={handleChange}
                                        label={`${modelName.charAt(0).toUpperCase() + modelName.slice(1)} API Key`}
                                        placeholder={`Enter ${modelName} API key`}
                                    />
                                </Grid>
                            );
                        })}
                    </Grid>

                    <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                        <Button
                            type="button"
                            onClick={handleSkip}
                            variant="outlined"
                        >
                            Skip for Now
                        </Button>
                        <Button
                            type="submit"
                            variant="contained"
                        >
                            Save API Keys
                        </Button>
                    </Box>
                </Box>
            </Paper>
        </Container>
    );
};

export default ApiKeyManager; 