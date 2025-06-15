import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';

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
        <div className="max-w-2xl mx-auto p-4">
            <h2 className="text-2xl font-bold mb-4">Manage API Keys</h2>
            
            {message && (
                <div className="mb-4 p-4 bg-green-100 text-green-700 rounded">
                    {message}
                </div>
            )}
            
            {error && (
                <div className="mb-4 p-4 bg-red-100 text-red-700 rounded">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                {Object.entries(apiKeys).map(([key, value]) => {
                    const modelName = key.replace('_api_key', '');
                    const isAvailable = availableModels[modelName];
                    
                    return (
                        <div key={key} className={`p-4 rounded ${isAvailable ? 'bg-green-50' : 'bg-gray-50'}`}>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {modelName.charAt(0).toUpperCase() + modelName.slice(1)} API Key
                                {isAvailable && (
                                    <span className="ml-2 text-green-600">✓ Available</span>
                                )}
                            </label>
                            <input
                                type="password"
                                name={key}
                                value={value}
                                onChange={handleChange}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder={`Enter ${modelName} API key`}
                            />
                        </div>
                    );
                })}

                <div className="flex space-x-4">
                    <button
                        type="submit"
                        className="flex-1 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Save API Keys
                    </button>
                    <button
                        type="button"
                        onClick={handleSkip}
                        className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Skip for Now
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ApiKeyManager; 