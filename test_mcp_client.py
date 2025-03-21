#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import asyncio
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QTabWidget, QComboBox
from PyQt5.QtCore import Qt

# Add the project root to the Python path
sys.path.insert(0, ".")

# Import the MCPClient
from app_root.mcp.client import MCPClient, MCPCoordinatorClient
from app_root.config.settings import SettingsManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCP-Test")

class MCPClientTestWidget(QWidget):
    """Test widget for the MCPClient"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCP Client Test")
        self.resize(800, 600)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create LLM tab
        llm_tab = QWidget()
        llm_layout = QVBoxLayout(llm_tab)
        tabs.addTab(llm_tab, "LLM Chat")
        
        # Add status label to LLM tab
        self.llm_status_label = QLabel("Initializing...")
        llm_layout.addWidget(self.llm_status_label)
        
        # Create input box for LLM tab
        self.llm_input_text = QTextEdit()
        self.llm_input_text.setPlaceholderText("Type your message here...")
        self.llm_input_text.setMaximumHeight(100)
        llm_layout.addWidget(self.llm_input_text)
        
        # Create send button for LLM tab
        self.llm_send_button = QPushButton("Send to Ollama")
        self.llm_send_button.clicked.connect(self.send_llm_message)
        llm_layout.addWidget(self.llm_send_button)
        
        # Create output box for LLM tab
        self.llm_output_text = QTextEdit()
        self.llm_output_text.setReadOnly(True)
        self.llm_output_text.setPlaceholderText("Response will appear here...")
        llm_layout.addWidget(self.llm_output_text)
        
        # Create MCP tab
        mcp_tab = QWidget()
        mcp_layout = QVBoxLayout(mcp_tab)
        tabs.addTab(mcp_tab, "MCP Operations")
        
        # Add status label to MCP tab
        self.mcp_status_label = QLabel("Initializing MCP...")
        mcp_layout.addWidget(self.mcp_status_label)
        
        # Create server selector
        self.server_combo = QComboBox()
        self.server_combo.addItems(["kde", "code", "data", "network"])
        mcp_layout.addWidget(self.server_combo)
        
        # Create operation buttons
        self.capabilities_button = QPushButton("Get Capabilities")
        self.capabilities_button.clicked.connect(self.get_mcp_capabilities)
        mcp_layout.addWidget(self.capabilities_button)
        
        self.krunner_button = QPushButton("KRunner Query (firefox)")
        self.krunner_button.clicked.connect(lambda: self.run_mcp_operation("krunner"))
        mcp_layout.addWidget(self.krunner_button)
        
        self.list_dir_button = QPushButton("List Home Directory")
        self.list_dir_button.clicked.connect(lambda: self.run_mcp_operation("list_dir"))
        mcp_layout.addWidget(self.list_dir_button)
        
        self.notification_button = QPushButton("Send Test Notification")
        self.notification_button.clicked.connect(lambda: self.run_mcp_operation("notification"))
        mcp_layout.addWidget(self.notification_button)
        
        # Create output box for MCP tab
        self.mcp_output_text = QTextEdit()
        self.mcp_output_text.setReadOnly(True)
        self.mcp_output_text.setPlaceholderText("MCP operation results will appear here...")
        mcp_layout.addWidget(self.mcp_output_text)
        
        # Initialize the clients
        self.settings = SettingsManager()
        
        # Initialize the LLM client
        self.mcp_client = MCPClient(server_url=self.settings.get("model/server_url"))
        
        # Connect LLM signals
        self.mcp_client.message_started.connect(self.on_llm_message_started)
        self.mcp_client.message_chunk.connect(self.on_llm_message_chunk)
        self.mcp_client.message_completed.connect(self.on_llm_message_completed)
        self.mcp_client.message_error.connect(self.on_llm_message_error)
        
        # Initialize the MCP coordinator client
        self.coordinator_url = self.settings.get("mcp/central_coordinator_url")
        self.coordinator_client = MCPCoordinatorClient(coordinator_url=self.coordinator_url)
        
        # Connect MCP signals
        self.coordinator_client.operation_started.connect(self.on_mcp_operation_started)
        self.coordinator_client.operation_result.connect(self.on_mcp_operation_result)
        self.coordinator_client.operation_error.connect(self.on_mcp_operation_error)
        
        # Update status
        self.llm_status_label.setText("LLM Ready")
        
        # Check if MCP is enabled
        if self.settings.get("mcp/enabled", False):
            self.mcp_status_label.setText(f"MCP Coordinator: {self.coordinator_url}")
        else:
            self.mcp_status_label.setText("MCP is disabled. Enable it in settings first.")
            self.capabilities_button.setEnabled(False)
            self.krunner_button.setEnabled(False)
            self.list_dir_button.setEnabled(False)
            self.notification_button.setEnabled(False)
    
    def send_llm_message(self):
        """Send the message to the LLM client"""
        # Get the message
        message = self.llm_input_text.toPlainText().strip()
        if not message:
            return
            
        # Clear the output text
        self.llm_output_text.clear()
        
        # Disable the send button
        self.llm_send_button.setEnabled(False)
        
        # Set model parameters
        model_params = {
            "model": "llama3:8b",  # Using the specific model name that's available
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048
        }
        
        # Send the message
        self.mcp_client.send_message_slot(message, model_params)
    
    def on_llm_message_started(self):
        """Handle LLM message generation started"""
        self.llm_status_label.setText("Generating response...")
        self.llm_output_text.setText("Thinking...")
    
    def on_llm_message_chunk(self, chunk):
        """Handle LLM message chunk received"""
        # Get the current text
        current_text = self.llm_output_text.toPlainText()
        
        # If it's the placeholder text, replace it
        if current_text == "Thinking...":
            self.llm_output_text.setText(chunk)
        else:
            # Otherwise, append the chunk
            self.llm_output_text.setText(current_text + chunk)
            
        # Move cursor to the end
        cursor = self.llm_output_text.textCursor()
        cursor.movePosition(cursor.End)
        self.llm_output_text.setTextCursor(cursor)
    
    def on_llm_message_completed(self, full_response):
        """Handle LLM message generation completed"""
        self.llm_status_label.setText("Response complete")
        self.llm_send_button.setEnabled(True)
    
    def on_llm_message_error(self, error_message):
        """Handle LLM message generation error"""
        self.llm_status_label.setText(f"Error: {error_message}")
        self.llm_output_text.setText(f"ERROR: {error_message}")
        self.llm_send_button.setEnabled(True)
    
    def get_mcp_capabilities(self):
        """Get MCP server capabilities"""
        self.mcp_output_text.clear()
        self.mcp_output_text.setText("Fetching MCP capabilities...")
        
        # Call in a separate thread
        self.run_async(self.coordinator_client.get_capabilities())
    
    def run_mcp_operation(self, operation_type):
        """Run an MCP operation"""
        self.mcp_output_text.clear()
        self.mcp_output_text.setText(f"Running {operation_type} operation...")
        
        if operation_type == "krunner":
            # Call KRunner query
            self.run_async(self.coordinator_client.query_krunner("firefox"))
        elif operation_type == "list_dir":
            # Call directory listing
            self.run_async(self.coordinator_client.list_directory("/home/ucadmin"))
        elif operation_type == "notification":
            # Call KDE notification
            self.run_async(self.coordinator_client.send_notification(
                "MCP Test",
                "This is a test notification from the KDE AI Interface MCP client."
            ))
    
    def on_mcp_operation_started(self):
        """Handle MCP operation started"""
        self.mcp_status_label.setText("MCP operation in progress...")
    
    def on_mcp_operation_result(self, result):
        """Handle MCP operation result"""
        self.mcp_status_label.setText("MCP operation completed")
        self.mcp_output_text.setText(f"Result:\n{str(result)}")
    
    def on_mcp_operation_error(self, error_message):
        """Handle MCP operation error"""
        self.mcp_status_label.setText(f"MCP Error: {error_message}")
        self.mcp_output_text.setText(f"ERROR: {error_message}")
    
    def run_async(self, coro):
        """Run an async coroutine"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    def closeEvent(self, event):
        """Handle close event"""
        # Close the clients
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.gather(
                self.mcp_client.close(),
                self.coordinator_client.close()
            ))
        except Exception as e:
            print(f"Error closing clients: {e}")
            
        event.accept()
        
def main():
    """Main function"""
    # Create the application
    app = QApplication(sys.argv)
    
    # Create and show the widget
    widget = MCPClientTestWidget()
    widget.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()