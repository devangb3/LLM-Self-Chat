import anthropic

MODEL_NAME = "claude-3-5-haiku-20241022"

def get_claude_response(api_key, prompt, system_prompt="You are a helpful assistant.", chat_history=None, max_tokens=1024):
    if not api_key:
        return "Claude API key not configured."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        messages_for_api = []
        if chat_history:
            messages_for_api.extend(chat_history)
        
        messages_for_api.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages_for_api
        )
        if response.content and isinstance(response.content, list) and len(response.content) > 0:
            if hasattr(response.content[0], 'text'):
                 return response.content[0].text
        return "Error: No text content found in Claude's response."
    except Exception as e:
        print(f"Error getting Claude response: {e}")
        return f"Error from Claude: {str(e)}"

if __name__ == '__main__':
    if ANTHROPIC_API_KEY:
        test_prompt = "Hello, Claude! Tell me a fun fact about AI."
        print(f"Sending prompt to Claude: {test_prompt}")
        response = get_claude_response(test_prompt) # Default call
        history = [
            {"role": "user", "content": "What was my previous question?"},
            {"role": "assistant", "content": "You asked for a fun fact about AI."}
        ]
        response = get_claude_response(test_prompt, chat_history=history, system_prompt="You are a helpful AI historian.")
        print(f"Claude's response: {response}")

        history_test_prompt = "Based on our previous conversation, what should I ask next?"
        print(f"Sending prompt with history to Claude: {history_test_prompt}")
        response_hist = get_claude_response(history_test_prompt, chat_history=history)
        print(f"Claude's response (with history): {response_hist}")

    else:
        print("Skipping Claude test as API key is not set.")