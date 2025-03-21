#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
try:
    # Try PyQt6 first (used in main app)
    from PyQt6.QtCore import QSettings
except ImportError:
    # Fallback to PyQt5 if needed
    from PyQt5.QtCore import QSettings
import keyring


class SettingsManager:
    """Manager for application settings"""
    
    def __init__(self):
        """Initialize settings manager"""
        self.settings = QSettings()
        self.keyring_service = "kde_ai_interface"
        
        # Ensure settings are initialized with defaults if needed
        self.initialize_defaults()
    
    def initialize_defaults(self):
        """Initialize default settings if not already set"""
        defaults = {
            # General settings
            "general/start_on_startup": False,
            "general/start_minimized": False,
            "general/max_history": 50,
            
            # Model settings
            "model/server_url": "http://localhost:11434",
            "model/temperature": 0.7,
            
            # Appearance settings
            "appearance/use_system_theme": True,
            "appearance/force_dark_mode": False,
            "appearance/font_size": 12,
            
            # Shortcut settings
            "shortcuts/toggle": "Alt+Space",
            "shortcuts/settings": "Alt+,",
            
            # MCP settings
            "mcp/context_window": 4096,
            "mcp/max_tokens": 1024,
            "mcp/central_coordinator_url": "http://localhost:8760",
            "mcp/kde_server_url": "http://localhost:8765",
            "mcp/code_server_url": "http://localhost:8766", 
            "mcp/data_server_url": "http://localhost:8767",
            "mcp/network_server_url": "http://localhost:8768",
            "mcp/enabled": False
        }
        
        # Set defaults if not already set
        for key, value in defaults.items():
            if not self.settings.contains(key):
                self.settings.setValue(key, value)
    
    def get(self, key, default=None):
        """Get a setting value"""
        # Special case for secure data
        if key == "model/api_key":
            return self.get_secure("api_key")
            
        value = self.settings.value(key, default)
        
        # Handle boolean values correctly (QSettings can return them as strings)
        if isinstance(default, bool) and not isinstance(value, bool):
            return value.lower() == "true"
            
        return value
    
    def set(self, key, value):
        """Set a setting value"""
        # Special case for secure data
        if key == "model/api_key":
            self.set_secure("api_key", value)
            return
            
        self.settings.setValue(key, value)
    
    def get_secure(self, key):
        """Get a secure setting value from the system keyring"""
        try:
            value = keyring.get_password(self.keyring_service, key)
            return value if value else ""
        except Exception:
            # Fallback to normal settings if keyring fails
            return self.settings.value(f"secure/{key}", "")
    
    def set_secure(self, key, value):
        """Set a secure setting value in the system keyring"""
        try:
            keyring.set_password(self.keyring_service, key, value)
        except Exception:
            # Fallback to normal settings if keyring fails
            self.settings.setValue(f"secure/{key}", value)
    
    def save(self):
        """Explicitly save settings"""
        self.settings.sync()
    
    def clear(self):
        """Clear all settings"""
        self.settings.clear()
        try:
            keyring.delete_password(self.keyring_service, "api_key")
        except Exception:
            pass