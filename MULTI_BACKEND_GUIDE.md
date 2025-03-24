# UnicornCommander KDE AI Interface Multi-Backend Guide

This guide explains how to use the multi-backend features in the UnicornCommander KDE AI Interface, allowing you to switch between OpenAI and Ollama backends for AI chat functionality, with additional memory features and agent capabilities.

## Introduction

The KDE AI Interface supports multiple AI backends:

1. **OpenAI API** - Cloud-based models like GPT-4o-mini through OpenAI's API
2. **Ollama** - Self-hosted, local models through the Ollama server
3. **AMD Ryzen AI** - Hardware-accelerated models using XDNA NPU (see README_RYZEN_AI_SETUP.md)

This flexibility allows you to choose between cloud-based models when you need maximum capabilities, local models when you prefer privacy, offline use, or cost savings, and hardware-accelerated models for optimal performance on supported devices.

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

## Memory and Context Features

The interface includes several advanced memory and context-related features:

1. **Long-Term Memory** - Toggle to enable semantic vector memory across conversations
2. **Conversation Memory** - Toggle to use current conversation history as context
3. **RAG** - Toggle button to enable Retrieval-Augmented Generation that enhances responses with relevant context from memory
4. **Screen Capture** - Toggle button to enable screen content context (currently a placeholder)

The memory system uses vector embeddings to store and retrieve semantically similar information, enhancing the AI's ability to recall previous interactions and maintain context across sessions.

## Conversations Management

The interface now includes a sidebar for managing multiple conversations:

1. **New Conversation** - Start a fresh conversation
2. **Conversation List** - View and select previous conversations
3. **Auto-Save** - Conversations are automatically saved when you exit the application

## Backend Settings

The "Settings" dialog provides comprehensive configuration options:

1. **General Tab**
   - System prompt configuration
   - Temperature and max tokens settings
   - Streaming response toggle
   - Dark mode toggle

2. **OpenAI Tab**
   - API Key configuration
   - Default model selection
   - API base URL (for custom endpoints)
   - Connection testing

3. **Ollama Tab**
   - Server URL configuration
   - Model selection and pull functionality
   - Connection testing
   - Model downloading capability

4. **Memory Tab**
   - Vector database configuration (Qdrant/ChromaDB)
   - Embedding model selection
   - Database connection settings
   - Cloud instance toggle

5. **MCP Servers Tab** (in unified interface)
   - Configuration for Model Context Protocol servers
   - Connection testing for each server
   - Agent permission settings

## Troubleshooting

### OpenAI Connection Issues

- Verify your API key is correct
- Check your internet connection
- Ensure the OpenAI Python package is installed
- Check the API base URL (should be `https://api.openai.com/v1`)

### Ollama Connection Issues

- Ensure Ollama is running (`ollama serve`)
- Verify you've pulled at least one model (`ollama pull llama3`)
- Check the server URL is correct
- Make sure the Requests Python package is installed
- Ensure your firewall isn't blocking access to the Ollama port (11434)

### Memory System Issues

- **Vector Database Connection**:
  - For Qdrant: Ensure Qdrant is running and accessible at the configured URL
  - For ChromaDB: Check the ChromaDB installation and permissions
  - Fallback: The system will automatically fall back to using JSON storage
 
- **PostgreSQL Connection**:
  - Verify database credentials are correct
  - Check PostgreSQL service is running
  - Confirm database permissions are set correctly
  - Fallback: The system will use simpler storage methods if unavailable

- **Redis Connection**:
  - Check Redis server is running
  - Verify correct port configuration
  - Fallback: The system will function without caching

### Agent System Issues

- **MCP Servers Not Running**:
  - Start the MCP servers with `launch_mcp_servers.py`
  - Check the MCP server logs for specific errors
  - Agents will fall back to basic functionality without tool access

- **Tool Execution Fails**:
  - Check MCP server permissions
  - Verify the agent has the required permissions
  - Check network connectivity between the interface and MCP servers

### General Issues

- Check the application logs for error messages
- Restart the application after changing backends
- Make sure you have the required Python packages installed
- Update to the latest version of the UnicornCommander KDE AI Interface
- For memory issues, check the storage paths have correct permissions

## Memory System Setup

The memory system utilizes vector databases and structured storage for enhanced functionality:

### Vector Database Options

1. **Qdrant** (Recommended for production)
   ```bash
   # Using Docker
   docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
   ```

2. **ChromaDB** (Simpler alternative)
   ```bash
   pip install chromadb
   ```

3. **JSON** (Fallback, no setup required)

### Structured Storage Options

1. **PostgreSQL** (For structured data)
   ```bash
   # Create database
   sudo -u postgres createdb kde_ai_interface
   sudo -u postgres createuser -P youruser
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kde_ai_interface TO youruser;"
   ```

2. **Redis** (For caching)
   ```bash
   # Start Redis
   sudo systemctl start redis
   ```

## Agent System

The unified interface includes an agent system with specialized agent types:

1. **Default Assistant** - Basic assistant without additional tools
2. **KDE Helper** - Interacts with KDE desktop via MCP
3. **Code Assistant** - Can execute code and provide results
4. **Data Analyst** - Analyzes data provided in the context
5. **Network Agent** - Performs network operations

To use these agents, the MCP servers need to be running. See the MCP-INTEGRATION-GUIDE.md for details.

## Future Enhancements

The following enhancements are planned for future updates:

1. Full implementation of screen capture functionality
2. Audio transcription and processing
3. Agent workspace for complex interactions
4. Enhanced MCP integration with desktop functionality
5. Performance benchmarking between backends
6. Additional backend support (Mistral, Claude, etc.)
7. Fine-tuning support for custom models