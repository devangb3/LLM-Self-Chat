import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables. Gemini client will not work.")
    # raise ValueError("GEMINI_API_KEY not found in environment variables")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# For text-only input
MODEL_NAME = "gemini-2.5-flash-preview-05-20" # Or other preferred model like gemini-1.5-pro-latest
model = genai.GenerativeModel(MODEL_NAME) if GEMINI_API_KEY else None

def get_gemini_response(prompt, system_prompt=None, chat_history=None):
    if not model:
        return "Gemini API key not configured."
    try:
        # Gemini API uses a slightly different way to handle system prompts and history.
        # System prompt can be part of the initial message or handled via specific instructions.
        # For conversational context, you start a chat session.

        # Simplified for single turn, will need to adapt for chat history
        # The new Gemini API (google.generativeai) has a simpler interface for system prompts
        # It can be set at the model level or passed with each request.

        # Let's assume `prompt` is the latest user message.
        # `chat_history` would be a list of Content objects (alternating user/model roles)

        messages_for_api = []
        if system_prompt:
            # The new API prefers system instructions within the model config or initial message.
            # For this example, we'll prepend it if given, or rely on model tuning.
            # This might need adjustment based on how `GenerativeModel` handles system prompts.
            # For now, we are not directly using system_prompt in the generate_content call below for gemini-pro
            # as it's typically set during model initialization or a different parameter for chat.
            # Refer to Gemini API documentation for the most current way to set system prompts.
            pass # System prompt handling needs to be more specific for Gemini's chat model

        if chat_history:
            # Convert our internal history to Gemini's format
            # Example: chat_history = [{"role": "user", "parts": ["Hello"]}, {"role": "model", "parts": ["Hi there!"]}]
            messages_for_api.extend(chat_history)

        messages_for_api.append({"role": "user", "parts": [prompt]})
        
        # If using the chat interface (recommended for multi-turn)
        # chat = model.start_chat(history=chat_history_formatted_for_gemini)
        # response = chat.send_message(prompt)

        # For a single generation or stateless interaction:
        full_prompt_content = messages_for_api # This will be a list of dicts
        
        # If system_prompt is provided, initialize a new model instance with it.
        # This is one way to provide system instructions with the new API for gemini-pro.
        # Alternatively, structure the `full_prompt_content` to include system instructions.
        current_model = model
        if system_prompt:
            # This might be too simplistic, check Gemini docs for `system_instruction` in `GenerativeModel`
            # For `gemini-pro`, system prompts are often part of the initial conversational turns.
            # Or, use `genai.GenerativeModel(MODEL_NAME, system_instruction=system_prompt)` if available and preferred.
            # For now, we'll assume the system prompt guides the overall behavior and prepend it to the history if not directly supported.
            # Let's just pass it to the `generation_config` if that's how it's handled, or prepend.         
            # For simplicity, the below example does not explicitly use the system_prompt yet.
            # More complex handling is required here for system prompts with gemini-pro.
            pass 

        # Log the exact payload being sent to Gemini
        print(f"[Gemini Client] Generating content with messages_for_api: {full_prompt_content}")
        response = current_model.generate_content(full_prompt_content)
        return response.text
    except Exception as e:
        print(f"Error getting Gemini response: {e}")
        # Try to access error details if available
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