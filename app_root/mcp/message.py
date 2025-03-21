#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Message:
    """Message representation for conversation history"""
    
    # Message roles
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"
    
    def __init__(self, role, content, message_id=None, timestamp=None):
        """Initialize a message"""
        self.role = role
        self.content = content
        self.message_id = message_id
        
        # Set timestamp if not provided
        if timestamp is None:
            import time
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp
    
    @classmethod
    def create_user_message(cls, content, message_id=None):
        """Create a user message"""
        return cls(cls.ROLE_USER, content, message_id)
    
    @classmethod
    def create_assistant_message(cls, content, message_id=None):
        """Create an assistant message"""
        return cls(cls.ROLE_ASSISTANT, content, message_id)
    
    @classmethod
    def create_system_message(cls, content, message_id=None):
        """Create a system message"""
        return cls(cls.ROLE_SYSTEM, content, message_id)
    
    def to_dict(self):
        """Convert message to a dictionary"""
        return {
            "role": self.role,
            "content": self.content,
            "id": self.message_id,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a message from a dictionary"""
        return cls(
            role=data.get("role", cls.ROLE_USER),
            content=data.get("content", ""),
            message_id=data.get("id"),
            timestamp=data.get("timestamp")
        )
    
    def to_mcp_format(self):
        """Convert message to MCP protocol format"""
        return {
            "role": self.role,
            "content": self.content
        }


class Conversation:
    """Representation of a conversation history"""
    
    def __init__(self, messages=None, conversation_id=None):
        """Initialize a conversation"""
        self.messages = messages or []
        self.conversation_id = conversation_id
    
    def add_message(self, message):
        """Add a message to the conversation"""
        self.messages.append(message)
    
    def add_user_message(self, content):
        """Add a user message to the conversation"""
        message = Message.create_user_message(content)
        self.add_message(message)
        return message
    
    def add_assistant_message(self, content):
        """Add an assistant message to the conversation"""
        message = Message.create_assistant_message(content)
        self.add_message(message)
        return message
    
    def add_system_message(self, content):
        """Add a system message to the conversation"""
        message = Message.create_system_message(content)
        self.add_message(message)
        return message
    
    def clear(self):
        """Clear all messages from the conversation"""
        self.messages = []
    
    def to_mcp_format(self):
        """Convert conversation to MCP protocol format"""
        return [msg.to_mcp_format() for msg in self.messages]
    
    def to_dict(self):
        """Convert conversation to a dictionary"""
        return {
            "id": self.conversation_id,
            "messages": [msg.to_dict() for msg in self.messages]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a conversation from a dictionary"""
        conversation = cls(conversation_id=data.get("id"))
        
        messages = data.get("messages", [])
        for msg_data in messages:
            conversation.add_message(Message.from_dict(msg_data))
        
        return conversation
    
    def save_to_file(self, file_path):
        """Save conversation to a JSON file"""
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path):
        """Load conversation from a JSON file"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)