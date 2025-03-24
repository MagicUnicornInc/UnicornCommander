# Agent System for KDE AI Interface

This directory contains the agent components for the KDE AI Interface, providing specialized AI agents with different capabilities for a more powerful and versatile assistant experience.

## Components

- **agent_manager.py**: Main agent management system that handles different agent types
- **agent_workspace.py**: (Coming soon) Provides a workspace environment for agents

## Agent Types

### 1. Direct Agent
- Basic assistant without additional tools
- Suitable for general queries and conversations
- Lowest resource utilization

### 2. KDE Desktop Agent
- Interacts with KDE desktop via MCP
- Can search, find, and open applications
- Access KRunner functionality

### 3. Code Execution Agent
- Executes code blocks via MCP
- Supports multiple programming languages
- Returns execution results

### 4. Data Analysis Agent
- Analyzes data provided in the context
- Generates summaries and insights
- Creates visualizations (coming soon)

### 5. Network Agent
- Performs network operations via MCP
- Retrieves and processes web content
- Handles URL fetching and parsing

## Requirements

- MCP Server running for agents that use tools
- Properly configured backend (OpenAI, Ollama, etc.)
- For code execution and data analysis: proper environment setup in MCP server

## Setup Instructions

### 1. Start MCP Servers

From the MCP_Servers directory:
```bash
python launch_mcp_servers.py
```

### 2. Configure Agents

Configuration can be done through the unified_ai_gui.py interface in the Settings dialog.

### 3. Create Custom Agents

You can create custom agents from the UI or directly in the agent_manager.py file:

```python
from app_root.agents.agent_manager import AgentManager, DirectAgent

# Create agent manager
agent_manager = AgentManager(llm_backend=your_backend, mcp_client=your_mcp_client)

# Add a custom agent
agent_id = agent_manager.add_agent(
    name="Custom Assistant",
    description="My custom agent",
    system_prompt="You are a specialized assistant for XYZ tasks.",
    agent_type="DirectAgent"  # Options: DirectAgent, KDEDesktopAgent, CodeExecutionAgent, DataAnalysisAgent, NetworkAgent
)
```

## Agent System Architecture

```
AgentManager
├── Agent (Base Class)
│   ├── DirectAgent
│   ├── KDEDesktopAgent
│   ├── CodeExecutionAgent
│   ├── DataAnalysisAgent
│   └── NetworkAgent
├── Agent Configuration Storage
└── MCP Client Integration
```

## MCP Tool Integration

Agents can use various MCP tools:

- **KDE MCP Server**: Desktop operations, KRunner, notifications
- **Code Execution MCP Server**: Code execution in isolated environment
- **Data Processing MCP Server**: Data analysis and visualization
- **Network Operations MCP Server**: Web requests and content processing

## Extending the Agent System

To add a new agent type:

1. Subclass the `Agent` base class in `agent_manager.py`
2. Implement the `run()` method
3. Add the agent type to the `add_agent()` method in `AgentManager`

Example:

```python
class CustomAgent(Agent):
    """Custom agent with special capabilities"""
    
    async def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Run the agent on a user input"""
        # Your implementation here
        return response
```

## Security Considerations

- Code execution is performed in a sandboxed environment
- Network operations are limited to safe operations
- File access is restricted to permitted directories
- MCP servers enforce permission boundaries

## Coming Soon

- Agent workspace with real-time interaction
- Multi-agent collaboration
- Persistent agent state
- Fine-tuning and training agents on specific tasks