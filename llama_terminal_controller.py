
import socket
import subprocess
import threading
import time
import sys
import os

# Connect to the main script
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
attempts = 0
while attempts < 5:
    try:
        client.connect(('localhost', 9998))
        break
    except:
        attempts += 1
        time.sleep(1)
        
if attempts == 5:
    print("Failed to connect to main script")
    sys.exit(1)

print("Connected to main Python script!")

# Format the command
llama_cmd = [
    r"C:\Users\anton\llama.cpp\build\bin\Release\llama-cli.exe",
    "-m", r"C:\Users\anton\llama.cpp\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    "-ngl", str(33),
    "-c", str(4096),
    "-t", str(6)
]

print("Starting Llama with command:")
print(" ".join(llama_cmd))

# Start llama-cli process
try:
    llama_process = subprocess.Popen(
        llama_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Redirect stderr to stdout to capture all output
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NO_WINDOW  # Don't create another window
    )
    print("Llama CLI process created with PID:", llama_process.pid)
except Exception as e:
    error_msg = f"Failed to start Llama CLI: {e}"
    print(error_msg)
    client.send(("ERROR: " + error_msg).encode())
    client.close()
    sys.exit(1)

# Check if process started correctly
time.sleep(2)
if llama_process.poll() is not None:
    error_msg = f"Llama CLI exited immediately with code {llama_process.returncode}"
    print(error_msg)
    client.send(("ERROR: " + error_msg).encode())
    client.close()
    sys.exit(1)

print("Llama CLI is now running...")
client.send("INIT: Llama process started, waiting for initialization...".encode())

# Function to read stdout from llama-cli process
def read_output():
    accumulated_output = ""
    init_complete = False
    
    while True:
        output_line = llama_process.stdout.readline()
        if not output_line and llama_process.poll() is not None:
            # Process has ended
            client.send(("TERMINATED: Llama process ended with code " + 
                        str(llama_process.returncode)).encode())
            break
            
        if output_line:
            print(output_line.strip())  # Echo to terminal for debugging
            accumulated_output += output_line
            
            # Check if the model has finished initializing
            if not init_complete and "llama_model_load: " in output_line:
                init_complete = True
                print("Llama model initialized successfully!")
                client.send("READY: Model initialized and ready for prompts".encode())
                accumulated_output = ""  # Clear the initialization text
                continue
                
            # Check for completion indicators
            if "llama_print_timings" in output_line:
                # Response is complete
                client.send(("RESPONSE: " + accumulated_output).encode())
                accumulated_output = ""
                
# Start output reader in a thread
output_thread = threading.Thread(target=read_output, daemon=True)
output_thread.start()

# Main loop to receive commands and send to llama-cli
while True:
    try:
        # Wait for command from the main script
        command = client.recv(4096).decode().strip()
        
        if command.lower() == "exit":
            llama_process.terminate()
            print("Terminating Llama process...")
            break
            
        # Send command to llama-cli
        print(f"Sending command to Llama: {command}")
        llama_process.stdin.write(command + "\n")
        llama_process.stdin.flush()
        
    except Exception as e:
        print(f"Error: {e}")
        break

# Clean up
client.close()
if llama_process.poll() is None:  # If process is still running
    llama_process.terminate()
    time.sleep(1)
    if llama_process.poll() is None:  # If it's still running after terminate
        llama_process.kill()  # Force kill
print("Terminal controller exiting...")
