from llama_cpp import Llama
import random

def setup_llama(model_path, n_gpu_layers=-1, seed=None, n_ctx=2048, chat_format="chatml-function-calling"):
    if seed is None:
        seed = random.random()
        
    return Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        seed=seed,
        n_ctx=n_ctx,
        chat_format=chat_format
    )

def ask_llama(llm, prompt, system=None, max_tokens=None, tools=None, tool_choice=None):
    # Create messages list
    messages = []
    
    # Add system message if provided
    if system:
        messages.append({
            "role": "system",
            "content": system
        })
    
    # Add user message
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Generate completion with max_tokens parameter if provided
    response = llm.create_chat_completion(
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        max_tokens=max_tokens  # Add this parameter to limit response size
    )
    
    # Extract and return only the text content
    if "choices" in response and len(response["choices"]) > 0:
        # Extract the assistant's message content
        if "message" in response["choices"][0]:
            if "content" in response["choices"][0]["message"] and response["choices"][0]["message"]["content"]:
                return response["choices"][0]["message"]["content"]
            # For function calling responses
            elif "tool_calls" in response["choices"][0]["message"]:
                return str(response["choices"][0]["message"]["tool_calls"])
    
    # Fallback if response format is unexpected
    return str(response)