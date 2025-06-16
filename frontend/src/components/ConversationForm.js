import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';

const ConversationForm = () => {
    const [formData, setFormData] = useState({
        name: '',
        system_prompt: '',
        llm_participants: []
    });
    const [availableModels, setAvailableModels] = useState({});
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
            const response = await fetch('http://localhost:5001/api/conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    ...formData,
                    start_conversation: true
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create conversation');
            }

            const data = await response.json();
            navigate(`/chat/${data.id}`);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleLLMSelect = (llm) => {
        if (!availableModels[llm]) {
            return;
        }

        setFormData(prev => ({
            ...prev,
            llm_participants: prev.llm_participants.includes(llm)
                ? prev.llm_participants.filter(p => p !== llm)
                : [...prev.llm_participants, llm]
        }));
    };

    const allModels = ['claude', 'gemini', 'chatgpt', 'deepseek'];

    return (
        <div className="max-w-2xl mx-auto p-4">
            <h2 className="text-2xl font-bold mb-4">Create New Conversation</h2>
            
            {error && (
                <div className="mb-4 p-4 bg-red-100 text-red-700 rounded">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Conversation Name
                    </label>
                    <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        required
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        System Prompt
                    </label>
                    <textarea
                        name="system_prompt"
                        value={formData.system_prompt}
                        onChange={handleChange}
                        rows="4"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        required
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select LLM Participants
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                        {allModels.map(llm => (
                            <button
                                key={llm}
                                type="button"
                                onClick={() => handleLLMSelect(llm)}
                                disabled={!availableModels[llm]}
                                className={`p-2 rounded-md text-sm font-medium ${
                                    formData.llm_participants.includes(llm)
                                        ? 'bg-indigo-600 text-white'
                                        : availableModels[llm]
                                            ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            : 'bg-gray-50 text-gray-400 cursor-not-allowed'
                                }`}
                            >
                                {llm.charAt(0).toUpperCase() + llm.slice(1)}
                                {!availableModels[llm] && (
                                    <span className="ml-2 text-xs">(No API key)</span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={formData.llm_participants.length === 0}
                    className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                        formData.llm_participants.length === 0
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-indigo-600 hover:bg-indigo-700'
                    } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                >
                    Create Conversation
                </button>
            </form>
        </div>
    );
};

export default ConversationForm; 