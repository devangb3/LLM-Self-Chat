import os
from google import genai
from google.genai import types


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables. Gemini client will not work.")
    # raise ValueError("GEMINI_API_KEY not found in environment variables")

MODEL_NAME = "gemini-2.5-flash-preview-05-20" 
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def get_gemini_response(prompt, system_prompt=None, chat_history=None):
    if not client:
        return "Gemini API key not configured."
    try:
        # Build the conversation history as a string
        conversation = []
        
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                parts = msg.get("parts", [])
                if isinstance(parts, list):
                    content = " ".join(str(p) for p in parts)
                else:
                    content = str(parts)
                conversation.append(f"{role}: {content}")

        # Add the current prompt
        conversation.append(f"user: {prompt}")
        
        # Join all messages with newlines
        full_prompt_content = "\n".join(conversation)
        
        current_client = client

        print(f"[Gemini Client] Generating content with prompt: {full_prompt_content}")
        response = current_client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt_content,
            config=types.GenerateContentConfig(system_instruction=system_prompt)
        )
        return response.text
    except Exception as e:
        print(f"Error getting Gemini response: {e}")
        if hasattr(e, 'message'):
            return f"Error from Gemini: {e.message}"
        return f"Error from Gemini: {str(e)}"

if __name__ == '__main__':
    if GEMINI_API_KEY:
        test_prompt = "Hello, Gemini! What is the future of AI?"
        print(f"Sending prompt to Gemini: {test_prompt}")
        system_instruction = "You are a futuristic AI. Be creative."
        response = get_gemini_response(test_prompt)
        print(f"Gemini's response: {response}")

        # Test with simple history
        history = [
            {"role": "user", "parts": ["Hi"]},
            {"role": "model", "parts": ["Hello! How can I help you today?"]}
        ]
        test_prompt_with_history = "Tell me more about large language models."
        print(f"Sending prompt to Gemini with history: {test_prompt_with_history}")
        response_hist = get_gemini_response(test_prompt_with_history, chat_history=history)
        print(f"Gemini's response (with history): {response_hist}")
    else:
        print("Skipping Gemini test as API key is not set.") 