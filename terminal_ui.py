#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import threading
import curses
from curses import wrapper

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

# Colors
HEADER_COLOR = 1
USER_MSG_COLOR = 2
ASSISTANT_MSG_COLOR = 3
INPUT_COLOR = 4
HIGHLIGHT_COLOR = 5

class Message:
    def __init__(self, text, is_user=False):
        self.text = text
        self.is_user = is_user
        self.timestamp = time.time()

class TerminalUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.messages = []
        self.current_input = ""
        self.cursor_pos = 0
        self.max_height, self.max_width = stdscr.getmaxyx()
        self.input_start_y = self.max_height - 3
        self.setup_colors()
        self.welcome()
        
    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(HEADER_COLOR, curses.COLOR_BLUE, -1)
        curses.init_pair(USER_MSG_COLOR, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(ASSISTANT_MSG_COLOR, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(INPUT_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(HIGHLIGHT_COLOR, curses.COLOR_BLACK, curses.COLOR_WHITE)
        
    def welcome(self):
        welcome_msg = "Hello! How can I assist you today?"
        self.add_message(welcome_msg, is_user=False)
        
    def add_message(self, text, is_user=False):
        self.messages.append(Message(text, is_user))
        self.redraw()
        
    def redraw(self):
        self.stdscr.clear()
        self.draw_header()
        self.draw_messages()
        self.draw_input_area()
        self.stdscr.refresh()
        
    def draw_header(self):
        header_text = "KDE AI Assistant"
        x = (self.max_width - len(header_text)) // 2
        self.stdscr.attron(curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
        self.stdscr.addstr(0, x, header_text)
        self.stdscr.attroff(curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
        self.stdscr.addstr(1, 0, "─" * self.max_width)
        
    def draw_messages(self):
        y = 2
        available_height = self.input_start_y - y - 1
        
        # If we have more messages than can fit, show only the most recent ones
        start_idx = max(0, len(self.messages) - available_height)
        
        for i, msg in enumerate(self.messages[start_idx:]):
            if y >= self.input_start_y - 1:
                break
                
            color = USER_MSG_COLOR if msg.is_user else ASSISTANT_MSG_COLOR
            prefix = "You: " if msg.is_user else "Assistant: "
            
            # Split message into lines that fit the screen width
            wrapped_lines = self.wrap_text(msg.text, self.max_width - 3)
            
            for j, line in enumerate(wrapped_lines):
                if y >= self.input_start_y - 1:
                    break
                    
                if j == 0:  # First line includes the prefix
                    self.stdscr.attron(curses.color_pair(color))
                    self.stdscr.addstr(y, 1, f"{prefix}{line}")
                    self.stdscr.attroff(curses.color_pair(color))
                else:
                    self.stdscr.attron(curses.color_pair(color))
                    self.stdscr.addstr(y, len(prefix) + 1, line)
                    self.stdscr.attroff(curses.color_pair(color))
                    
                y += 1
                
            y += 1  # Add space between messages
    
    def wrap_text(self, text, width):
        lines = []
        for line in text.split('\n'):
            while len(line) > width:
                # Find the last space before the width limit
                space_pos = line[:width].rfind(' ')
                if space_pos == -1:  # No space found, hard break
                    lines.append(line[:width])
                    line = line[width:]
                else:
                    lines.append(line[:space_pos])
                    line = line[space_pos+1:]
            lines.append(line)
        return lines
            
    def draw_input_area(self):
        self.stdscr.addstr(self.input_start_y - 1, 0, "─" * self.max_width)
        prompt = "Type your message (Ctrl+C to exit): "
        self.stdscr.addstr(self.input_start_y, 1, prompt)
        
        # Input area
        input_x = len(prompt) + 1
        visible_input = self.current_input
        
        # If input is too long, show a portion with cursor visible
        if len(prompt) + len(visible_input) >= self.max_width - 2:
            # Ensure cursor is visible
            if self.cursor_pos > len(visible_input) - (self.max_width - input_x - 5):
                start = self.cursor_pos - (self.max_width - input_x - 5)
                visible_input = visible_input[start:]
                visible_input = "..." + visible_input
                cursor_x = input_x + 3 + (self.cursor_pos - start)
            else:
                visible_input = visible_input[:self.max_width - input_x - 5] + "..."
                cursor_x = input_x + self.cursor_pos
        else:
            cursor_x = input_x + self.cursor_pos
        
        self.stdscr.attron(curses.color_pair(INPUT_COLOR))
        self.stdscr.addstr(self.input_start_y, input_x, visible_input)
        self.stdscr.attroff(curses.color_pair(INPUT_COLOR))
        
        # Position cursor
        self.stdscr.move(self.input_start_y, cursor_x)
            
    def handle_input(self):
        while True:
            try:
                key = self.stdscr.getch()
                
                if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
                    if self.current_input.strip():
                        message = self.current_input
                        self.add_message(message, is_user=True)
                        self.current_input = ""
                        self.cursor_pos = 0
                        
                        # Handle commands and generate responses
                        if message.lower() in ["exit", "quit"]:
                            self.add_message(RESPONSES[message.lower()], is_user=False)
                            time.sleep(1)
                            return
                            
                        # Generate response
                        self.generate_response(message)
                        
                elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
                    if self.cursor_pos > 0:
                        self.current_input = self.current_input[:self.cursor_pos-1] + self.current_input[self.cursor_pos:]
                        self.cursor_pos -= 1
                        self.redraw()
                        
                elif key == curses.KEY_DC:  # Delete key
                    if self.cursor_pos < len(self.current_input):
                        self.current_input = self.current_input[:self.cursor_pos] + self.current_input[self.cursor_pos+1:]
                        self.redraw()
                        
                elif key == curses.KEY_LEFT:  # Left arrow
                    if self.cursor_pos > 0:
                        self.cursor_pos -= 1
                        self.redraw()
                        
                elif key == curses.KEY_RIGHT:  # Right arrow
                    if self.cursor_pos < len(self.current_input):
                        self.cursor_pos += 1
                        self.redraw()
                        
                elif key == curses.KEY_HOME:  # Home key
                    self.cursor_pos = 0
                    self.redraw()
                    
                elif key == curses.KEY_END:  # End key
                    self.cursor_pos = len(self.current_input)
                    self.redraw()
                    
                elif 32 <= key <= 126:  # Printable ASCII characters
                    self.current_input = self.current_input[:self.cursor_pos] + chr(key) + self.current_input[self.cursor_pos:]
                    self.cursor_pos += 1
                    self.redraw()
                    
            except KeyboardInterrupt:
                return
                
    def simulate_typing(self, message, delay=0.03):
        """Simulate typing effect for assistant responses"""
        temp_msg = ""
        for char in message:
            temp_msg += char
            self.messages[-1].text = temp_msg
            self.redraw()
            time.sleep(delay)
    
    def generate_response(self, user_message):
        # Add a placeholder while "thinking"
        self.add_message("Thinking...", is_user=False)
        
        # Simulate response generation delay
        time.sleep(0.5)
        
        # Check for keywords in user message
        response = None
        for key, value in RESPONSES.items():
            if key in user_message.lower():
                response = value
                break
                
        if not response:
            response = RESPONSES["default"]
            
        # Update the placeholder with the actual response
        self.messages[-1].text = ""
        self.redraw()
        
        # Simulate typing effect in a separate thread to keep UI responsive
        threading.Thread(target=self.simulate_typing, args=(response,), daemon=True).start()
                

def main(stdscr):
    # Set up curses
    curses.curs_set(1)  # Show cursor
    stdscr.clear()
    
    # Create and run the UI
    ui = TerminalUI(stdscr)
    ui.handle_input()

if __name__ == "__main__":
    wrapper(main)