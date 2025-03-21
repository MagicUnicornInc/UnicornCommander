#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time

# ANSI color codes
BLUE = "\033[94m"
GREEN = "\033[92m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header():
    """Print the chat header"""
    width = 80
    print(f"{BLUE}{BOLD}{'═' * width}{RESET}")
    print(f"{BLUE}{BOLD}{'KDE AI Assistant':^{width}}{RESET}")
    print(f"{BLUE}{BOLD}{'═' * width}{RESET}")
    print()

def print_user_message(message):
    """Print a user message"""
    print(f"{BLUE}{BOLD}You:{RESET} {WHITE}{message}{RESET}")
    print()

def print_assistant_message(message, typing_effect=True):
    """Print an assistant message with optional typing effect"""
    if typing_effect:
        print(f"{GREEN}{BOLD}Assistant:{RESET} ", end="", flush=True)
        for char in message:
            print(f"{GREEN}{char}{RESET}", end="", flush=True)
            time.sleep(0.01)
        print("\n")
    else:
        print(f"{GREEN}{BOLD}Assistant:{RESET} {GREEN}{message}{RESET}")
        print()

def main():
    """Run a demo conversation"""
    print_header()
    
    # Initial greeting
    print_assistant_message("Hello! How can I assist you today?")
    time.sleep(1)
    
    # First user question
    print_user_message("What is KDE?")
    time.sleep(0.5)
    
    # Assistant response
    print(f"{GREEN}{BOLD}Assistant:{RESET} Thinking...", end="", flush=True)
    time.sleep(1)
    print("\r" + " " * 50 + "\r", end="", flush=True)  # Clear the "Thinking..." text
    print_assistant_message("KDE is a powerful open-source desktop environment for Linux systems. It offers a customizable and feature-rich experience for users.")
    time.sleep(1.5)
    
    # Second user question
    print_user_message("How do I use this AI assistant?")
    time.sleep(0.5)
    
    # Assistant response
    print(f"{GREEN}{BOLD}Assistant:{RESET} Thinking...", end="", flush=True)
    time.sleep(1)
    print("\r" + " " * 50 + "\r", end="", flush=True)
    print_assistant_message("This KDE AI Assistant provides a seamless way to interact with AI models through a native KDE interface.\n\nYou can:\n1. Press Alt+Space to show/hide the interface\n2. Type your questions or requests\n3. Get real-time responses\n4. Configure various AI models in the settings\n\nThe interface integrates with your KDE desktop theme and supports markdown formatting and code syntax highlighting.")
    time.sleep(2)
    
    # Third user question
    print_user_message("Can it integrate with other KDE applications?")
    time.sleep(0.5)
    
    # Assistant response
    print(f"{GREEN}{BOLD}Assistant:{RESET} Thinking...", end="", flush=True)
    time.sleep(1)
    print("\r" + " " * 50 + "\r", end="", flush=True)
    print_assistant_message("Yes! The KDE AI Interface is designed to integrate with the KDE Plasma desktop environment and can interact with other KDE applications.\n\nFuture enhancements will include:\n- Context-aware suggestions based on current applications\n- File and content analysis from Dolphin file manager\n- Integration with KRunner for enhanced search capabilities\n- Plugin system for extended capabilities with other KDE applications")
    time.sleep(2)
    
    # Fourth user question
    print_user_message("Thanks for the information!")
    time.sleep(0.5)
    
    # Assistant response
    print(f"{GREEN}{BOLD}Assistant:{RESET} Thinking...", end="", flush=True)
    time.sleep(0.5)
    print("\r" + " " * 50 + "\r", end="", flush=True)
    print_assistant_message("You're welcome! Feel free to ask if you have any other questions about the KDE AI Interface or KDE in general.")
    time.sleep(1.5)
    
    # Final message
    width = 80
    print(f"{BLUE}{BOLD}{'═' * width}{RESET}")
    print(f"{BLUE}{BOLD}{'This is a demonstration of the KDE AI Interface':^{width}}{RESET}")
    print(f"{BLUE}{BOLD}{'The actual interface would provide a floating window similar to ChatGPT\'s desktop app':^{width}}{RESET}")
    print(f"{BLUE}{BOLD}{'═' * width}{RESET}")

if __name__ == "__main__":
    main()