from llama_cpp import Llama

# Use a very small model just for testing
llm = Llama(
    model_path=r"C:\Users\anton\llama.cpp\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    n_gpu_layers=1,  # Just try 1 layer to test
    verbose=True  # This will show CUDA initialization messages
)

# Just run a simple inference
result = llm("Testing CUDA", max_tokens=10)
print(result)