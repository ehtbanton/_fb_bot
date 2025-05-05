import os
import anthropic

"""
def set_up_claude_api():
    api_key = os.getenv("ANTHROPIC_API_KEY")  # Reads the variable
    if not api_key:
        raise ValueError("API key not found. Make sure ANTHROPIC_API_KEY is set.")
    return anthropic.Anthropic(api_key=api_key) # Creates the API client
"""

def ask_claude(prompt):

    api_key = os.getenv("ANTHROPIC_API_KEY")  # Reads the variable
    if not api_key:
        raise ValueError("API key not found. Make sure ANTHROPIC_API_KEY is set.")
    client = anthropic.Anthropic(api_key=api_key) # Creates the API client
        
    message = client.messages.create(
        #model="claude-3-7-sonnet-latest",
        model="claude-3-5-haiku-latest",
        max_tokens=8192,
        temperature=1,
        system="",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    text_response = "\n\n"+"".join(part.text for part in message.content)
    return text_response
