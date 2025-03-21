# MCP Quick Start Guide

This guide provides the fastest way to see the MCP integration in action with the KDE AI Interface.

## Step 1: Install Node.js Dependencies

```bash
cd ~/GIT-Projects/MCP-Servers
npm install
```

## Step 2: Start the MCP Servers

```bash
# From the MCP-Servers directory
npm run start:all
```

You should see console output indicating that all servers have started:
- Central Coordinator on port 8760
- KDE Server on port 8765
- Code Execution Server on port 8766
- Data Processing Server on port 8767
- Network Operations Server on port 8768

## Step 3: Enable MCP in KDE AI Interface

```bash
cd ~/GIT-Projects/KDE\ AI\ Interface
source venv/bin/activate

# Run this Python code to enable MCP
python -c "from app_root.config.settings import SettingsManager; s = SettingsManager(); s.set('mcp/enabled', True); s.save(); print('MCP enabled!')"
```

## Step 4: Launch the Test Client

```bash
# From the KDE AI Interface directory (with venv activated)
python test_mcp_client.py
```

This will open a graphical test client with two tabs:

### Tab 1: LLM Chat
- Use this tab to test regular chat functionality with your LLM

### Tab 2: MCP Operations
- Use this tab to test MCP functionality:
  - **Get Capabilities** button: Retrieves capabilities from all MCP servers
  - **KRunner Query (firefox)** button: Sends a search query for "firefox" to KRunner
  - **List Home Directory** button: Lists files in your home directory
  - **Send Test Notification** button: Sends a test desktop notification

## Step 5: Verify MCP Server Operation

Open your web browser and navigate to:

```
http://localhost:8760/api/status
```

You should see a JSON response showing the status of all MCP servers.

## Step 6: Test Individual Server Features Directly

### KDE Server - List Directory

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"path":"'$HOME'"}' \
     http://localhost:8765/api/fs/list
```

### Code Execution Server - Run Python Code

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"code":"print(\"Hello from MCP!\")","language":"python"}' \
     http://localhost:8766/api/execute
```

### Data Processing Server - Analyze Simple Data

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"data":[{"x":1,"y":10},{"x":2,"y":20},{"x":3,"y":30}],"type":"summary"}' \
     http://localhost:8767/api/analyze
```

### Network Server - Make Simple HTTP Request

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"url":"https://api.github.com/zen"}' \
     http://localhost:8768/api/http
```

## What's Next?

For the next steps to fully integrate MCP into the KDE AI Interface, see the `MCP-INTEGRATION-GUIDE.md` document which details:

1. How to use MCP in your code
2. The remaining tasks to complete the integration
3. Advanced features and customization options

## Troubleshooting

If the test client doesn't show MCP functionality:

1. Verify all servers are running with:
   ```bash
   curl http://localhost:8760/api/status
   ```

2. Ensure MCP is enabled in settings:
   ```bash
   python -c "from app_root.config.settings import SettingsManager; s = SettingsManager(); print(f'MCP enabled: {s.get(\"mcp/enabled\")}')"
   ```

3. Check for errors in server console outputs

4. Restart the servers and test client if needed