from google import genai
from google.genai import types

MODEL_NAME = "gemini-2.5-flash-preview-05-20" 

def get_gemini_response(api_key, prompt, system_prompt=None, chat_history=None):
    if not api_key:
        return "Gemini API key not configured."
    try:
        client = genai.Client(api_key=api_key)
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
