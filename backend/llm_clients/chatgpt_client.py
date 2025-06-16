import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables. ChatGPT client will not work.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

MODEL_NAME = "gpt-4o-mini-2024-07-18"

def get_chatgpt_response(prompt, system_prompt="You are a helpful assistant.", chat_history=None, max_tokens=5000):
    if not client:
        return "OpenAI API key not configured."
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if chat_history:
            messages.extend(chat_history)
            
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting ChatGPT response: {e}")
        return f"Error from ChatGPT: {str(e)}"

if __name__ == '__main__':
    if OPENAI_API_KEY:
        test_prompt = "Hello, ChatGPT! Can you write a short poem about coding?"
        print(f"Sending prompt to ChatGPT: {test_prompt}")
        response = get_chatgpt_response(test_prompt)
        print(f"ChatGPT's response:\n{response}")

        system = "You are a pirate captain."
        history = [
            {"role": "user", "content": "Ahoy there!"},
            {"role": "assistant", "content": "Arrr, matey! What be yer query?"}
        ]
        test_prompt_hist = "What's the weather like today?"
        print(f"\nSending prompt to Pirate ChatGPT: {test_prompt_hist}")
        response_hist = get_chatgpt_response(test_prompt_hist, system_prompt=system, chat_history=history)
        print(f"Pirate ChatGPT's response:\n{response_hist}")
    else:
        print("Skipping ChatGPT test as API key is not set.") 