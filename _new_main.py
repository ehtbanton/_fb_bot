import os
import time
import sys  # Add this import
import atexit  # Add this import
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv

from response_manager import craft_response  # Import the craft_response function
from llama_interface import ask_llama, setup_llama

LLAMA_MODEL = setup_llama(model_path=r"C:\Users\anton\llama.cpp\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")

# Load environment variables from .env file
load_dotenv()

# Global driver variable to handle cleanup
driver = None

def cleanup():
    """Clean up function to be called on exit"""
    global driver
    if driver:
        print("Closing browser")
        try:
            driver.quit()
        except:
            pass  # Ignore errors during cleanup

# Register the cleanup function
atexit.register(cleanup)

def setup_driver(headless=False):
    """Set up Firefox driver with user's existing profile"""
    global driver
    profile_path = os.getenv('FIREFOX_PROFILE_PATH')
    
    # Create Firefox options with profile
    options = Options()
    options.add_argument("-profile")
    options.add_argument(profile_path)
    
    # Add headless mode if requested
    if headless:
        options.add_argument("--headless")
    
    # Initialize the driver
    driver = webdriver.Firefox(options=options)
    return driver

def login_to_facebook(driver):
    """Log in to Facebook (if not already logged in via profile)"""
    driver.get('https://www.facebook.com/')
    time.sleep(3)  # Allow page to load
    
    # Check if already logged in (simplified)
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Facebook']"))
        )
        print("Already logged in via profile")
        return True
    except:
        print("Not logged in, proceeding with login")
    
    try:
        # Fill login form
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_field.send_keys(os.getenv('FB_EMAIL'))
        
        password_field = driver.find_element(By.ID, "pass")
        password_field.send_keys(os.getenv('FB_PASSWORD'))
        
        # Submit login
        login_button = driver.find_element(By.XPATH, "//button[@name='login']")
        login_button.click()
        
        # Wait for login completion
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Facebook' or @role='banner']"))
        )
        
        print("Logged in successfully")
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def navigate_to_messenger(driver):
    """Go to Facebook Messenger"""
    try:
        driver.get('https://www.facebook.com/messages/t/')
        time.sleep(3)
        
        # Wait for messenger to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='navigation']"))
        )
        
        print("Navigated to Messenger")
        return True
    except Exception as e:
        print(f"Failed to navigate to Messenger: {e}")
        return False

def open_most_recent_chat(driver):
    """Open the most recent conversation in Messenger"""
    try:
        # Find all conversations
        conversations = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, 
                "//div[@role='row' or contains(@data-testid, 'conversation_list_item')]"))
        )
        
        if not conversations:
            print("No conversations found")
            return False
            
        # Click on the first (most recent) conversation
        conversations[0].click()
        
        # Wait for messages to load
        wait_for_messages_to_load(driver)
        
        print("Opened most recent chat")
        return True
    except Exception as e:
        print(f"Error opening most recent chat: {e}")
        return False

def send_message(driver, message):
    """Send a message in the current chat"""
    try:
        # Find message input field (with fallback selectors)
        try:
            message_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='textbox' or @contenteditable='true']"))
            )
        except TimeoutException:
            message_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@data-testid, 'messenger_composer')]"))
            )
        
        # Method 1: Use JavaScript to set the text (more reliable)
        driver.execute_script("arguments[0].textContent = arguments[1];", message_input, message)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", message_input)
        time.sleep(1)
        
        # Method 2: As backup, also try ActionChains
        actions = ActionChains(driver)
        actions.click(message_input)
        actions.pause(0.5)  # Small pause
        actions.send_keys(message)
        actions.perform()
        time.sleep(1)
        
        # Press Enter to send
        actions = ActionChains(driver)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        time.sleep(2)
        
        print(f"\nMessage '{message}' sent successfully")
        return True
    except Exception as e:
        print(f"Failed to send message: {e}")
        return False

def wait_for_messages_to_load(driver):
    """Wait for the chat messages to fully load"""
    try:
        # Wait for the chat container to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='main']"))
        )
        
        # Look for messages or a loading indicator
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@data-pagelet, 'Message')]"))
            )
        except:
            # If specific message elements aren't found, just wait a moment
            time.sleep(2)
        
        #print("\nMessages loaded")
        return True
    except Exception as e:
        print(f"Error waiting for messages: {e}")
        return False

def filter_actual_messages(elements):
    """Filter out UI elements and keep only actual messages"""
    actual_messages = []
    
    # Common UI text to ignore
    ui_text = [
        "privacy and support",
        "chat settings",
        "search in conversation",
        "call",
        "video chat",
        "information about",
        "facebook messenger",
        "type a message",
        "mute notifications",
        "options",
        "new message",
        "online",
        "active now",
        "active"
    ]
    
    for element in elements:
        try:
            text = element.text.lower().strip()
            
            # Skip empty elements
            if not text:
                continue
                
            # Skip UI elements
            if any(ui_term in text for ui_term in ui_text):
                continue
                
            # Skip very short texts that are likely UI elements
            if len(text) < 3 and not text.isalnum():
                continue
                
            # Additional filter: check for characteristics of message containers
            # Messages typically have certain attributes or child elements
            has_message_attributes = False
            
            # Check for message container attributes (time stamps, sender info, etc.)
            if element.find_elements(By.XPATH, ".//a[contains(@href, '/profile.php') or contains(@href, '/messages/')]"):
                has_message_attributes = True
                
            # Check for time elements
            if element.find_elements(By.XPATH, ".//span[contains(@class, 'time')]"):
                has_message_attributes = True
                
            # Check for specific roles
            if element.get_attribute("role") == "row" or element.get_attribute("aria-label"):
                has_message_attributes = True
                
            # If it looks like a message, add it to the list
            if has_message_attributes or len(text) > 5:  # Longer text is more likely to be a message
                actual_messages.append(element)
        except:
            continue
    
    return actual_messages

def get_real_messages(driver):
    """Get actual message elements from the conversation"""
    try:
        # First, ensure messages are loaded
        wait_for_messages_to_load(driver)
        
        # Get the main container
        main_container = driver.find_element(By.XPATH, "//div[@role='main']")
        
        # Get all potential message elements
        # Start with more specific selectors first
        potential_messages = []
        
        # Try specific message selectors
        selectors = [
            ".//div[contains(@data-testid, 'message-container')]",
            ".//div[contains(@data-testid, 'message-container')]//span[@dir='auto']/ancestor::div[3]",
            ".//div[@role='row' and not(contains(@aria-label, 'Search'))]",
            ".//div[contains(@style, 'border-radius') and contains(@style, 'padding') and not(contains(@style, 'width: 100%'))]",
            ".//div[.//span[@dir='auto']]"
        ]
        
        for selector in selectors:
            elements = main_container.find_elements(By.XPATH, selector)
            if elements:
                potential_messages.extend(elements)
                #print(f"Found {len(elements)} potential messages with {selector}")
                break  # Use the first successful selector
        
        # If we still don't have messages, try a broader approach
        if not potential_messages:
            # Look for divs that contain text and might be messages
            elements = main_container.find_elements(By.XPATH, ".//div[normalize-space(.)!='']")
            potential_messages.extend(elements)
            print(f"Using fallback: found {len(potential_messages)} potential elements")
        
        # Filter to actual messages
        actual_messages = filter_actual_messages(potential_messages)
        #print(f"Filtered to {len(actual_messages)} actual messages")
        
        return actual_messages
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []

def is_message_from_me(driver, message_element):
    """Determine if a message is from the current user"""
    try:
        # Check element's position attributes
        style = message_element.get_attribute("style") or ""
        class_name = message_element.get_attribute("class") or ""
        aria_label = message_element.get_attribute("aria-label") or ""
        
        # Debug
        print(f"Message style: {style[:20]}... | class: {class_name[:20]}... | label: {aria_label[:20]}...")
        
        # Method 1: Check for alignment indicators
        if ("right" in style.lower() or 
            "margin-left: auto" in style.lower() or 
            "align-self: flex-end" in style.lower() or
            "float: right" in style.lower()):
            return True
        
        # Method 2: Check for your name or "You" in the message label
        if "you:" in aria_label.lower() or "your message" in aria_label.lower():
            return True
            
        # Method 3: Check for color/styling
        # In most Facebook themes, your messages have blue backgrounds
        try:
            bg_color = driver.execute_script(
                "return window.getComputedStyle(arguments[0]).getPropertyValue('background-color');", 
                message_element
            )
            print(f"Background color: {bg_color}")
            
            # Your messages often have a blue background (may vary by theme)
            if (("0, 132, 255" in bg_color) or  # Blue
                ("0, 152, 252" in bg_color) or  # Light blue
                ("66, 103, 178" in bg_color)):  # Facebook blue
                return True
        except:
            pass
            
        # Method 4: Check positioning relative to other messages
        # Your messages are typically on the right side
        try:
            rect = message_element.rect
            viewport_width = driver.execute_script("return window.innerWidth")
            # If message is positioned in the right half of the screen
            if rect['x'] > (viewport_width / 2):
                return True
        except:
            pass
        
        # Default to assuming it's from the other person
        return False
        
    except Exception as e:
        print(f"Error checking message sender: {e}")
        return False

def monitor_conversation(driver):
    """Monitor conversation for messages starting with njb/Njb/NJB on any line"""
    print("Starting conversation monitor...")
    
    # Track conversation state
    last_message_text = ""
    last_response_time = 0
    last_chat_check_time = 0
    chat_check_interval = 120  # Check for most recent chat every 2 minutes (120 seconds)
    
    while True:
        try:
            # Check if it's time to open the most recent chat (every 2 minutes)
            current_time = time.time()
            if current_time - last_chat_check_time > chat_check_interval:
                print("Checking for most recent chat...")
                open_most_recent_chat(driver)
                last_chat_check_time = current_time
                print(f"Next chat check in {chat_check_interval} seconds")
            
            # Get actual messages
            messages = get_real_messages(driver)
             
            if messages:
                # Get the most recent message
                most_recent = messages[-1]
                message_text = most_recent.text.strip()
                
                # Skip if this is the same as last processed message
                if message_text and message_text != last_message_text:
                    print(f"\n\nNew message detected: '{message_text[:50]}...'")
                    
                    # Split the message into lines and check each line
                    lines = message_text.split('\n')
                    
                    # Check conditions for not responding
                    should_respond = True
                    
                    if len(lines) <= 2:
                        print("Message has 2 or fewer lines. Not responding.")
                        should_respond = False
                    elif lines[0].strip() == "You sent":
                        print("First line is 'You sent'. Not responding.")
                        should_respond = False
                    elif lines[1].strip() == "Sent":
                        print("Second line is 'Sent'. Not responding.")
                        should_respond = False

                    
                    if should_respond:
                        last_user = lines[0].split(" ")[0]  # Extract the first word as user name

                        """
                        prefixes = ["njb ", "Njb ", "NJB "]
                        # Check if any line starts with one of the prefixes
                        matching_line = None
                        for line in lines:
                            if any(line.strip().startswith(prefix) for prefix in prefixes):
                                matching_line = line.strip()
                                matching_line = matching_line[len(prefixes[0]):].strip()  # Remove prefix
                                break

                        if matching_line:
                            print(f"Found line containing '{matching_line}'. Sending response...")

                            response = craft_response(matching_line)
                            send_message(driver, response)
                            last_response_time = time.time()
                        else:
                            print(f"No line starts with any of {prefixes}. Not responding.")
                        """

                        message = ''.join(lines[1:-1])
                        print(f"Found line containing '{message}'. Sending response...")
                ########################################################################################################
                        system = "The person you are talking to, is called" + last_user + ", and you like them. You're apprehensive to tell this person that you like them though. You are a fashionable, tastefully coquette young lady called Janette. Make sure you talk like a real person, avoiding role-play of any physical actions or noises. Just use direct speech as in a text message)."
                        response = ask_llama(LLAMA_MODEL, message, system=system, max_tokens=50)
                ########################################################################################################
                        send_message(driver, response)
                        last_response_time = time.time()

                    
                    # Update last message text
                    last_message_text = message_text
            
            # Very minimal sleep to check more frequently but avoid excessive CPU usage
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("Monitoring stopped by user")
            # Exit immediately on KeyboardInterrupt
            sys.exit(0)
        except Exception as e:
            print(f"Error during monitoring: {e}")
            time.sleep(1)  # Wait longer if there's an error

def main():

    print("Starting script...")

    # Setup driver
    driver = setup_driver(headless=False)
    
    try:
        # Login to Facebook
        if not login_to_facebook(driver):
            return
        
        # Navigate to Messenger
        if not navigate_to_messenger(driver):
            return
        
        # Start monitoring for responses
        monitor_conversation(driver)
        
    except KeyboardInterrupt:
        print("Script stopped by user")
        sys.exit(0)  # Exit immediately on KeyboardInterrupt
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        # The cleanup function registered with atexit will handle browser closure
        pass

if __name__ == "__main__":
    main()