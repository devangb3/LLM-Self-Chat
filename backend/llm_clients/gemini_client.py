import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables. Gemini client will not work.")
    # raise ValueError("GEMINI_API_KEY not found in environment variables")
else:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash-preview-05-20" 
model = genai.GenerativeModel(MODEL_NAME) if GEMINI_API_KEY else None

def get_gemini_response(prompt, system_prompt=None, chat_history=None):
    if not model:
        return "Gemini API key not configured."
    try:
        
        messages_for_api = []
        if system_prompt:
            pass

        if chat_history:
            messages_for_api.extend(chat_history)

        messages_for_api.append({"role": "user", "parts": [prompt]})
        
       

        full_prompt_content = messages_for_api
        
        current_model = model

        print(f"[Gemini Client] Generating content with messages_for_api: {full_prompt_content}")
        response = current_model.generate_content(full_prompt_content)
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
        # Example with a system prompt (adapt as needed based on API specifics)
        system_instruction = "You are a futuristic AI. Be creative."
        # response = get_gemini_response(test_prompt, system_prompt=system_instruction)
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