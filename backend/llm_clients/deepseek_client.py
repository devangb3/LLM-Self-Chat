import os
import requests # Using requests for now, replace if a specific SDK is available

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions" # Example URL, please verify

if not DEEPSEEK_API_KEY:
    print("Warning: DEEPSEEK_API_KEY not found in environment variables. Deepseek client will not work.")

MODEL_NAME = "deepseek-chat"

def get_deepseek_response(prompt, system_prompt="You are a helpful assistant.", chat_history=None, max_tokens=1024):
    if not DEEPSEEK_API_KEY:
        return "Deepseek API key not configured."
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    
    if system_prompt and (not chat_history or not any(msg.get("role") == "system" for msg in chat_history)):
        messages.append({"role": "system", "content": system_prompt})
    
    if chat_history: 
        messages.extend(chat_history)
        
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        response_json = response.json()
        if response_json.get("choices") and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"]
        else:
            return f"Error from Deepseek: Unexpected response format - {response_json}"
            
    except requests.exceptions.RequestException as e:
        print(f"Error getting Deepseek response: {e}")
        if e.response is not None:
            return f"Error from Deepseek: {e.response.status_code} - {e.response.text}"
        return f"Error from Deepseek: {str(e)}"
    except Exception as e:
        print(f"Generic error in Deepseek client: {e}")
        return f"Error from Deepseek: {str(e)}"

if __name__ == '__main__':
    if DEEPSEEK_API_KEY:
        test_prompt = "Hello, Deepseek! Write a python function to sort a list."
        print(f"Sending prompt to Deepseek: {test_prompt}")
        response = get_deepseek_response(test_prompt)
        print(f"Deepseek's response:\n{response}")

        system = "You are a master programmer who loves Python."
        history = [
            {"role": "system", "content": system},
            {"role": "user", "content": "What is your favorite programming language?"},
            {"role": "assistant", "content": "Python, of course! It's versatile and elegant."}
        ]
        test_prompt_hist = "Can you show me an example of a list comprehension?"
        print(f"\nSending prompt to Programmer Deepseek: {test_prompt_hist}")
        response_hist = get_deepseek_response(test_prompt_hist, system_prompt=system, chat_history=history)
        print(f"Programmer Deepseek's response:\n{response_hist}")
    else:
        print("Skipping Deepseek test as API key is not set.") 