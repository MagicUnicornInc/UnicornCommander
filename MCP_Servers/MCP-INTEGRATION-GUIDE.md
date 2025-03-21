# MCP Integration Guide for KDE AI Interface

This document explains how to use the Model Context Protocol (MCP) integration in the KDE AI Interface.

## Overview

The KDE AI Interface has been enhanced with MCP support, allowing it to interact with the following MCP servers:

1. **MCP Central Coordinator** - Manages all MCP servers and provides a unified access point
2. **KDE MCP Server** - Enables interaction with KDE desktop features
3. **Code Execution MCP Server** - Provides secure code execution capabilities
4. **Data Processing MCP Server** - Offers data analysis and visualization 
5. **Network Operations MCP Server** - Handles HTTP requests and file downloads

## Prerequisites

Before using the MCP features, ensure you have:

1. Node.js (v14 or later) installed
2. The MCP servers set up and running
3. Required Python packages (pandas, numpy, matplotlib, seaborn) for data visualization

## Setup

### 1. Install the MCP Servers

Go to the MCP Servers directory and install dependencies:

```bash
cd ~/GIT-Projects/MCP-Servers
npm install
```

### 2. Start the MCP Servers

You can start all servers at once:

```bash
npm run start:all
```

Or use the Python launcher script included in the KDE AI Interface:

```bash
cd ~/GIT-Projects/KDE\ AI\ Interface
./launch_mcp_servers.py --start
```

### 3. Enable MCP in KDE AI Interface

MCP is already enabled in the settings but you can verify with:

```python
from app_root.config.settings import SettingsManager
s = SettingsManager()
print(f"MCP enabled: {s.get('mcp/enabled')}")
```

If it's not enabled, you can enable it with:

```python
s.set('mcp/enabled', True)
s.save()
```

## Testing the Integration

### Using the Test Client

The KDE AI Interface includes a test client to verify the MCP integration:

```bash
cd ~/GIT-Projects/KDE\ AI\ Interface
source venv/bin/activate
python test_mcp_client.py
```

This will open a GUI with two tabs:
1. **LLM Chat** - For testing regular chat functionality
2. **MCP Operations** - For testing MCP server capabilities

### MCP Operations You Can Test

In the MCP Operations tab, you can:

1. **Get Capabilities** - Retrieve capabilities from all MCP servers
2. **KRunner Query** - Send a search query to KRunner
3. **List Home Directory** - List files in your home directory
4. **Send Test Notification** - Send a desktop notification through KDE

## Using MCP in Your Code

### Initializing the MCP Client

```python
from app_root.mcp.client import MCPCoordinatorClient

# Create a client connected to the central coordinator
coordinator_url = "http://localhost:8760"
mcp_client = MCPCoordinatorClient(coordinator_url=coordinator_url)
```

### Performing KDE Operations

```python
# Query KRunner
result = await mcp_client.query_krunner("firefox")

# List a directory
files = await mcp_client.list_directory("/home/yourusername")

# Read a file
content = await mcp_client.read_file("/home/yourusername/example.txt")

# Send a notification
await mcp_client.send_notification("Hello", "This is a test notification")
```

### Executing Code

```python
# Execute Python code
result = await mcp_client.execute_operation(
    "code", 
    "/api/execute", 
    "POST", 
    {
        "code": "print('Hello from MCP!')",
        "language": "python"
    }
)
```

### Processing Data

```python
# Analyze data
data = [{"x": 1, "y": 10}, {"x": 2, "y": 20}, {"x": 3, "y": 30}]
result = await mcp_client.execute_operation(
    "data", 
    "/api/analyze", 
    "POST", 
    {
        "data": data,
        "type": "summary"
    }
)

# Create a plot (after analyzing data)
dataset_id = result["datasetId"]
plot_result = await mcp_client.execute_operation(
    "data", 
    "/api/plot", 
    "POST", 
    {
        "datasetId": dataset_id,
        "type": "line",
        "options": {
            "xColumn": "x",
            "yColumn": "y",
            "title": "Example Plot"
        }
    }
)
```

### Making Network Requests

```python
# Make an HTTP request
response = await mcp_client.execute_operation(
    "network", 
    "/api/http", 
    "POST", 
    {
        "url": "https://api.github.com/zen",
        "method": "GET"
    }
)

# Download a file
download = await mcp_client.execute_operation(
    "network", 
    "/api/download", 
    "POST", 
    {
        "url": "https://example.com/file.pdf",
        "filename": "example.pdf"
    }
)
```

## Todo for Full Integration

To see the MCP integration in full action, the following tasks should be completed:

1. **Update Main Application UI:**
   - Add MCP-specific features to the main window interface
   - Create visualization components for data analysis results
   - Add file browser integration with the KDE MCP Server

2. **Enhance AI Capabilities:**
   - Modify the AI prompts to use MCP capabilities
   - Create special commands that trigger specific MCP operations
   - Implement context gathering through MCP (like reading files or capturing screenshots)

3. **Add KDE Integration Components:**
   - Create Plasma widgets that display data from MCP servers
   - Implement KRunner plugins that use the AI through MCP
   - Add context menu extensions for AI assistance

4. **Secure and Optimize:**
   - Implement proper authentication for MCP servers
   - Add caching for frequently accessed data
   - Optimize performance for large file operations

## Troubleshooting

If you encounter issues with the MCP integration:

1. **Check Server Status:**
   ```bash
   curl http://localhost:8760/api/status
   ```

2. **Verify Server Connections:**
   Check if all the required servers are running and reachable.

3. **Check Logs:**
   - Look at the MCP server console output for errors
   - Check the KDE AI Interface logs for connection issues

4. **Debugging Tips:**
   - Try individual server endpoints directly with curl
   - Use the test client to isolate problems
   - Verify network connectivity between components

## Resources

- **MCP Servers Documentation:** See the README.md in the MCP-Servers directory
- **MCP Protocol Specification:** See the Deep-Research-KDE.txt for details
- **API Documentation:** Check individual server capabilities at `http://localhost:8760/api/capabilities`