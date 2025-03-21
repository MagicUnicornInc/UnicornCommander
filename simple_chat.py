#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import os

# Simulated responses
RESPONSES = {
    "hello": "Hello! How can I help you today?",
    "hi": "Hi there! What can I do for you?",
    "help": "I'm your KDE AI Assistant. You can ask me questions, and I'll provide answers.\n\nNote: This is a terminal simulation of the GUI interface.",
    "kde": "KDE is a powerful open-source desktop environment for Linux systems. It offers a customizable and feature-rich experience for users.",
    "weather": "I'm a demo interface and can't check the real weather. When connected to an AI model, I could help answer questions like this!",
    "bye": "Goodbye! Feel free to come back if you have more questions.",
    "exit": "Exiting KDE AI Assistant. Have a great day!",
    "quit": "Closing KDE AI Assistant. Goodbye!",
    "default": "This is a terminal simulation of the KDE AI Assistant interface. In the full version, I would be connected to an AI model through MCP."
}

# ANSI color codes
BLUE = "\033[94m"
GREEN = "\033[92m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"

def clear_screen():
    """Clear the terminal screen"""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except:
        # If we can't clear the screen, print some newlines
        print("\n" * 10)

def print_header():
    """Print the chat header"""
    try:
        width = min(80, os.get_terminal_size().columns)
    except (OSError, AttributeError):
        width = 80
    print(f"{BLUE}{BOLD}{'═' * width}{RESET}")
    print(f"{BLUE}{BOLD}{'KDE AI Assistant':^{width}}{RESET}")
    print(f"{BLUE}{BOLD}{'═' * width}{RESET}")
    print()

def print_message(message, is_user=False):
    """Print a message with appropriate styling"""
    if is_user:
        sender = f"{BLUE}{BOLD}You:{RESET}"
        color = WHITE
    else:
        sender = f"{GREEN}{BOLD}Assistant:{RESET}"
        color = GREEN
        
    print(f"{sender} {color}{message}{RESET}")
    print()

def simulate_typing(message, delay=0.03):
    """Simulate typing effect for assistant responses"""
    print(f"{GREEN}{BOLD}Assistant:{RESET} ", end="", flush=True)
    for char in message:
        print(f"{GREEN}{char}{RESET}", end="", flush=True)
        time.sleep(delay)
    print("\n")

def main():
    """Main chat interface"""
    clear_screen()
    print_header()
    
    # Welcome message
    print_message("Hello! How can I assist you today?")
    
    history = []
    
    while True:
        try:
            user_input = input(f"{BLUE}{BOLD}You:{RESET} ")
            print()  # Add a newline after user input
            
            if not user_input.strip():
                continue
                
            # Add to history
            history.append((user_input, True))
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                response = RESPONSES[user_input.lower()]
                print(f"{GREEN}{BOLD}Assistant:{RESET} ", end="", flush=True)
                time.sleep(0.5)
                simulate_typing(response, 0.02)
                break
            
            # Simulate "thinking"
            print(f"{GREEN}{BOLD}Assistant:{RESET} Thinking...", end="", flush=True)
            time.sleep(0.8)
            print("\r" + " " * 50 + "\r", end="", flush=True)  # Clear the "Thinking..." text
            
            # Generate response
            response = None
            for key, value in RESPONSES.items():
                if key in user_input.lower():
                    response = value
                    break
                    
            if not response:
                response = RESPONSES["default"]
                
            # Simulate typing effect
            simulate_typing(response, 0.02)
            
            # Add to history
            history.append((response, False))
            
        except KeyboardInterrupt:
            print("\n\nExiting KDE AI Assistant. Goodbye!")
            break
            
    print(f"{BLUE}{BOLD}{'═' * 80}{RESET}")
    print(f"{BLUE}{BOLD}{'Thank you for using KDE AI Assistant!':^80}{RESET}")
    print(f"{BLUE}{BOLD}{'═' * 80}{RESET}")

if __name__ == "__main__":
    main()