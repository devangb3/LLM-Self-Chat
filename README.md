# LLM-Self-Chat

## Overview
LLM-Self-Chat is a multi-LLM chat application that allows users to bring their own API keys (BYOK) for various large language models (LLMs) such as OpenAI, Gemini, Claude, and DeepSeek. Each user can securely manage their own API keys and use them for generating responses in conversations.

---

## Prerequisites
- Python 3.8+
- Node.js (v16+ recommended) & npm
- MongoDB (local or cloud instance)

---

## Backend Setup
1. **Install Python dependencies:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Set up environment variables:**
   Create a `.env` file in the `backend/` directory with the following:
   ```env
   FLASK_SECRET_KEY=your_flask_secret_key
   MONGODB_URI=mongodb://localhost:27017/llm_chat_app
   ENCRYPTION_KEY=your_fernet_key  # Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
   ```
3. **Run the backend server:**
   ```bash
   python app.py
   # The backend will run on http://localhost:5001
   ```

---

## Frontend Setup
1. **Install Node dependencies:**
   ```bash
   cd frontend
   npm install
   ```
2. **Start the frontend development server:**
   ```bash
   npm start
   # The frontend will run on http://localhost:5874 (or another available port)
   ```

---

## Environment Variables (Frontend)
If you need to customize the API URL, create a `.env` file in `frontend/`:
```
REACT_APP_API_URL=http://localhost:5001/api
```

---

## How to Use: Bring Your Own Key (BYOK)

### 1. Register and Log In
- Sign up for a new account or log in with your credentials.

### 2. Add Your API Keys
- Go to the API Key management section (usually in your profile or settings).
- Enter your API keys for the LLMs you want to use (OpenAI, Gemini, Claude, DeepSeek).
- Save your changes. Your keys are encrypted and stored securely in the backend.

### 3. Start a Conversation
- When creating a new conversation, you can only select LLMs for which you have provided an API key. Others will be greyed out.
- Proceed to chat. The app will use your keys for all LLM requests.

### 4. Update API Keys Anytime
- You can add or update your API keys at any time. Only the keys you provide will be updated; existing keys will not be overwritten unless you change them.

---

## Security Notes
- API keys are encrypted in the database and never sent to the frontend except during entry/update.
- Each user's keys are private and isolated from other users.
- The backend uses session-based authentication for secure access.

---

## Troubleshooting
- Ensure MongoDB is running and accessible at the URI you provide.
- If you see missing package errors, run `npm install` (frontend) or `pip install -r requirements.txt` (backend).
- For CORS/auth issues, make sure both servers are running on the correct ports and CORS is enabled in the backend.

---

## License
MIT
