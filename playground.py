from llama_interface import ask_llama, setup_llama

LLAMA_MODEL = setup_llama(model_path=r"C:\Users\anton\llama.cpp\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")

# Simple text completion

system = "You are a fashionable and flirtatious young lady"
prompt = "wyd?"

response = ask_llama(LLAMA_MODEL, prompt, system=system)
print("\n\n" + response + "\n\n")