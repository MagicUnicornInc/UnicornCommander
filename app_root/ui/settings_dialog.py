#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    # Try PyQt6 first (used in main app)
    from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QLabel, QLineEdit, QPushButton, QCheckBox,
                              QFormLayout, QSpinBox, QDoubleSpinBox,
                              QComboBox, QGroupBox, QDialogButtonBox, QMessageBox)
    from PyQt6.QtCore import Qt, QSettings
    QT6 = True
except ImportError:
    # Fallback to PyQt5 if needed
    from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QLabel, QLineEdit, QPushButton, QCheckBox,
                              QFormLayout, QSpinBox, QDoubleSpinBox,
                              QComboBox, QGroupBox, QDialogButtonBox, QMessageBox)
    from PyQt5.QtCore import Qt, QSettings
    QT6 = False

from app_root.config.settings import SettingsManager


class SettingsDialog(QDialog):
    """Dialog for configuring application settings"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        
        self.setWindowTitle("Settings")
        self.resize(500, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_model_tab()
        self.create_appearance_tab()
        self.create_shortcuts_tab()
        
        # Add button box
        if QT6:
            self.button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
        else:
            self.button_box = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Load current settings
        self.load_settings()
    
    def create_general_tab(self):
        """Create the general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Startup settings
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout(startup_group)
        
        self.startup_checkbox = QCheckBox("Start on system startup")
        self.tray_checkbox = QCheckBox("Start minimized to system tray")
        
        startup_layout.addWidget(self.startup_checkbox)
        startup_layout.addWidget(self.tray_checkbox)
        
        # Session settings
        session_group = QGroupBox("Session")
        session_layout = QFormLayout(session_group)
        
        self.history_spin = QSpinBox()
        self.history_spin.setMinimum(0)
        self.history_spin.setMaximum(100)
        self.history_spin.setSpecialValueText("No limit")
        session_layout.addRow("Maximum conversation history:", self.history_spin)
        
        # Add groups to tab
        layout.addWidget(startup_group)
        layout.addWidget(session_group)
        layout.addStretch(1)
        
        self.tab_widget.addTab(tab, "General")
    
    def create_model_tab(self):
        """Create the model settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # MCP Server settings
        server_group = QGroupBox("MCP Server")
        server_layout = QFormLayout(server_group)
        
        self.server_url = QLineEdit()
        server_layout.addRow("Server URL:", self.server_url)
        
        self.api_key = QLineEdit()
        if QT6:
            self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            self.api_key.setEchoMode(QLineEdit.Password)
        server_layout.addRow("API Key:", self.api_key)
        
        # Add Ollama-specific controls
        ollama_group = QGroupBox("Ollama")
        ollama_layout = QFormLayout(ollama_group)
        
        self.ollama_url = QLineEdit()
        self.ollama_url.setPlaceholderText("http://localhost:11434")
        ollama_layout.addRow("Ollama URL:", self.ollama_url)
        
        # Model parameters
        model_group = QGroupBox("Model Parameters")
        model_layout = QFormLayout(model_group)
        
        self.model_combo = QComboBox()
        self.model_combo.addItem("llama3")
        self.model_combo.addItem("llama3:8b")
        self.model_combo.addItem("llama3:70b")
        self.model_combo.addItem("mistral")
        self.model_combo.addItem("gemma:2b")
        self.model_combo.addItem("gemma:7b")
        self.model_combo.setEditable(True)
        self.model_combo.setCurrentText("llama3")
        model_layout.addRow("Model:", self.model_combo)
        
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(0.7)
        model_layout.addRow("Temperature:", self.temperature)
        
        # Ollama-specific parameters
        self.top_p = QDoubleSpinBox()
        self.top_p.setRange(0.0, 1.0)
        self.top_p.setSingleStep(0.05)
        self.top_p.setValue(0.9)
        model_layout.addRow("Top P:", self.top_p)
        
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(1, 32768)
        self.max_tokens.setValue(4096)
        model_layout.addRow("Max Tokens:", self.max_tokens)
        
        # Test connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_ollama_connection)
        
        # Add groups to tab
        layout.addWidget(server_group)
        layout.addWidget(ollama_group)
        layout.addWidget(model_group)
        layout.addWidget(self.test_button)
        layout.addStretch(1)
        
        self.tab_widget.addTab(tab, "Model")
    
    def create_appearance_tab(self):
        """Create the appearance settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.system_theme_radio = QCheckBox("Use system theme (follows KDE settings)")
        self.dark_mode_checkbox = QCheckBox("Force dark mode")
        
        theme_layout.addWidget(self.system_theme_radio)
        theme_layout.addWidget(self.dark_mode_checkbox)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        font_layout.addRow("Font size:", self.font_size_spin)
        
        # Add groups to tab
        layout.addWidget(theme_group)
        layout.addWidget(font_group)
        layout.addStretch(1)
        
        self.tab_widget.addTab(tab, "Appearance")
    
    def create_shortcuts_tab(self):
        """Create the keyboard shortcuts tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        shortcut_group = QGroupBox("Keyboard Shortcuts")
        shortcut_layout = QFormLayout(shortcut_group)
        
        self.toggle_shortcut = QLineEdit("Alt+Space")
        shortcut_layout.addRow("Toggle interface:", self.toggle_shortcut)
        
        self.settings_shortcut = QLineEdit("Alt+,")
        shortcut_layout.addRow("Open settings:", self.settings_shortcut)
        
        # Add groups to tab
        layout.addWidget(shortcut_group)
        layout.addStretch(1)
        
        self.tab_widget.addTab(tab, "Shortcuts")
    
    def load_settings(self):
        """Load current settings into the dialog"""
        # General tab
        self.startup_checkbox.setChecked(self.settings_manager.get("general/start_on_startup", False))
        self.tray_checkbox.setChecked(self.settings_manager.get("general/start_minimized", False))
        self.history_spin.setValue(self.settings_manager.get("general/max_history", 50))
        
        # Model tab
        self.server_url.setText(self.settings_manager.get("model/server_url", ""))
        self.api_key.setText(self.settings_manager.get("model/api_key", ""))
        self.temperature.setValue(self.settings_manager.get("model/temperature", 0.7))
        
        # Appearance tab
        self.system_theme_radio.setChecked(self.settings_manager.get("appearance/use_system_theme", True))
        self.dark_mode_checkbox.setChecked(self.settings_manager.get("appearance/force_dark_mode", False))
        self.font_size_spin.setValue(self.settings_manager.get("appearance/font_size", 12))
        
        # Shortcuts tab
        self.toggle_shortcut.setText(self.settings_manager.get("shortcuts/toggle", "Alt+Space"))
        self.settings_shortcut.setText(self.settings_manager.get("shortcuts/settings", "Alt+,"))
    
    def test_ollama_connection(self):
        """Test connection to the Ollama server"""
        import asyncio
        import aiohttp
        
        async def test_connection():
            url = self.ollama_url.text() or "http://localhost:11434"
            test_url = f"{url.rstrip('/')}/api/tags"
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(test_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            models = data.get("models", [])
                            if models:
                                model_names = [model.get("name", "") for model in models]
                                return True, f"Connection successful! Available models: {', '.join(model_names)}"
                            else:
                                return True, "Connection successful, but no models found."
                        else:
                            return False, f"Connection failed with status code: {response.status}"
            except aiohttp.ClientConnectorError:
                return False, "Could not connect to Ollama server. Make sure the URL is correct and the server is running."
            except Exception as e:
                return False, f"Error connecting to Ollama server: {str(e)}"
        
        # Run the async test in the event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        success, message = loop.run_until_complete(test_connection())
        
        # Show result message
        if success:
            QMessageBox.information(self, "Connection Test", message)
        else:
            QMessageBox.warning(self, "Connection Test", message)
            
    def load_settings(self):
        """Load current settings into the dialog"""
        # General tab
        self.startup_checkbox.setChecked(self.settings_manager.get("general/start_on_startup", False))
        self.tray_checkbox.setChecked(self.settings_manager.get("general/start_minimized", False))
        self.history_spin.setValue(self.settings_manager.get("general/max_history", 50))
        
        # Model tab
        self.server_url.setText(self.settings_manager.get("model/server_url", ""))
        self.api_key.setText(self.settings_manager.get("model/api_key", ""))
        self.ollama_url.setText(self.settings_manager.get("model/ollama_url", "http://localhost:11434"))
        
        # Set model parameters
        self.model_combo.setCurrentText(self.settings_manager.get("model/ollama_model", "llama3"))
        self.temperature.setValue(self.settings_manager.get("model/temperature", 0.7))
        self.top_p.setValue(self.settings_manager.get("model/top_p", 0.9))
        self.max_tokens.setValue(self.settings_manager.get("model/max_tokens", 4096))
        
        # Appearance tab
        self.system_theme_radio.setChecked(self.settings_manager.get("appearance/use_system_theme", True))
        self.dark_mode_checkbox.setChecked(self.settings_manager.get("appearance/force_dark_mode", False))
        self.font_size_spin.setValue(self.settings_manager.get("appearance/font_size", 12))
        
        # Shortcuts tab
        self.toggle_shortcut.setText(self.settings_manager.get("shortcuts/toggle", "Alt+Space"))
        self.settings_shortcut.setText(self.settings_manager.get("shortcuts/settings", "Alt+,"))
    
    def accept(self):
        """Save settings when OK is clicked"""
        # General tab
        self.settings_manager.set("general/start_on_startup", self.startup_checkbox.isChecked())
        self.settings_manager.set("general/start_minimized", self.tray_checkbox.isChecked())
        self.settings_manager.set("general/max_history", self.history_spin.value())
        
        # Model tab
        self.settings_manager.set("model/server_url", self.server_url.text())
        self.settings_manager.set("model/api_key", self.api_key.text())
        self.settings_manager.set("model/ollama_url", self.ollama_url.text())
        self.settings_manager.set("model/ollama_model", self.model_combo.currentText())
        self.settings_manager.set("model/temperature", self.temperature.value())
        self.settings_manager.set("model/top_p", self.top_p.value())
        self.settings_manager.set("model/max_tokens", self.max_tokens.value())
        
        # Appearance tab
        self.settings_manager.set("appearance/use_system_theme", self.system_theme_radio.isChecked())
        self.settings_manager.set("appearance/force_dark_mode", self.dark_mode_checkbox.isChecked())
        self.settings_manager.set("appearance/font_size", self.font_size_spin.value())
        
        # Shortcuts tab
        self.settings_manager.set("shortcuts/toggle", self.toggle_shortcut.text())
        self.settings_manager.set("shortcuts/settings", self.settings_shortcut.text())
        
        # Save all settings
        self.settings_manager.save()
        
        # Close dialog
        super().accept()