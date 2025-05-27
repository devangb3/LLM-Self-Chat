# This package will contain the client integrations for different LLMs.
from .claude_client import get_claude_response
from .gemini_client import get_gemini_response
from .chatgpt_client import get_chatgpt_response
from .deepseek_client import get_deepseek_response

# You can also create a unified interface or factory function here if needed
# For example:
# def get_llm_response(llm_name, prompt, system_prompt=None, chat_history=None):
#     if llm_name == "claude":
#         return get_claude_response(prompt, system_prompt, chat_history)
#     elif llm_name == "gemini":
#         return get_gemini_response(prompt, system_prompt, chat_history)
#     # ... and so on
#     else:
#         raise ValueError(f"Unknown LLM: {llm_name}") 