# KDE AI Interface Multi-Backend Guide

This guide explains how to use the new multi-backend features in the KDE AI Interface, allowing you to switch between OpenAI and Ollama backends for AI chat functionality.

## Introduction

The KDE AI Interface now supports multiple AI backends:

1. **OpenAI API** - Cloud-based models like GPT-4o-mini through OpenAI's API
2. **Ollama** - Self-hosted, local models through the Ollama server

This flexibility allows you to choose between cloud-based models when you need maximum capabilities, or local models when you prefer privacy, offline use, or cost savings.

## Setup Requirements

### OpenAI Backend

To use the OpenAI backend, you need:

1. An OpenAI API key (get one at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys))
2. Internet connection
3. The OpenAI Python package (`pip install openai`)

### Ollama Backend

To use the Ollama backend, you need:

1. Ollama installed and running on your computer or a remote server ([https://ollama.com/download](https://ollama.com/download))
2. At least one model pulled through Ollama (e.g., `ollama pull llama2`)
3. The Requests Python package (`pip install requests`)

## Configuration

### Setting Up OpenAI

1. Launch the KDE AI Interface
2. Click "Set API Key" in the sidebar or go to "Backend Settings" > "OpenAI" tab
3. Enter your OpenAI API key
4. Click "Test OpenAI Connection" to verify connectivity
5. Select your preferred default model
6. Click "Save"

### Setting Up Ollama

1. Launch the KDE AI Interface
2. Click "Advanced Settings" in the sidebar or API key dialog
3. Go to the "Ollama" tab
4. Enable the Ollama backend by checking "Enable Ollama"
5. Enter your Ollama server URL (default: `http://localhost:11434`)
6. Enter your preferred model name (default: `llama2`)
7. Click "Test Ollama Connection" to verify connectivity
8. Click "Save"

## Switching Between Backends

You can switch between backends at any time:

1. In the main interface, click on the "Status and Model Info" dropdown
2. Under "Active Backend," select either "OpenAI" or "Ollama"
3. The available models dropdown will update to show models for the selected backend
4. Select your desired model from the dropdown

The interface will remember your backend preference between sessions.

## Context Features (Placeholders)

The interface includes several context-related features that are currently implemented as placeholders:

1. **Screen Capture** - Toggle button to enable screen content context (currently a placeholder)
2. **Audio Capture** - Toggle button to enable audio transcription context (currently a placeholder)
3. **RAG** - Toggle button to enable Retrieval-Augmented Generation from previous conversations (currently a placeholder)

These buttons will include the indicated context in your prompts as placeholder text. Future updates will implement the actual functionality.

## Conversations Management

The interface now includes a sidebar for managing multiple conversations:

1. **New Conversation** - Start a fresh conversation
2. **Conversation List** - View and select previous conversations
3. **Auto-Save** - Conversations are automatically saved when you exit the application

## Backend Settings

The "Backend Settings" dialog provides comprehensive configuration options:

1. **OpenAI Tab**
   - API Key configuration
   - Default model selection
   - API base URL (for custom endpoints)
   - Connection testing

2. **Ollama Tab**
   - Server URL configuration
   - Model selection
   - Enable/disable toggle
   - Connection testing

3. **MCP Servers Tab**
   - Configuration for Model Context Protocol servers
   - Connection testing for each server
   - Enable/disable toggles for individual servers

## Troubleshooting

### OpenAI Connection Issues

- Verify your API key is correct
- Check your internet connection
- Ensure the OpenAI Python package is installed
- Check the API base URL (should be `https://api.openai.com/v1`)

### Ollama Connection Issues

- Ensure Ollama is running (`ollama serve`)
- Verify you've pulled at least one model (`ollama pull llama2`)
- Check the server URL is correct
- Make sure the Requests Python package is installed
- Ensure your firewall isn't blocking access to the Ollama port (11434)

### General Issues

- Check the application logs for error messages
- Restart the application after changing backends
- Make sure you have the required Python packages installed
- Update to the latest version of the KDE AI Interface

## Future Enhancements

The following enhancements are planned for future updates:

1. Actual implementation of screen capture functionality
2. Actual implementation of audio transcription
3. Full RAG functionality with vector database integration
4. MCP integration with the new UI
5. Performance benchmarking between backends
6. Additional backend support (Mistral, Claude, etc.)