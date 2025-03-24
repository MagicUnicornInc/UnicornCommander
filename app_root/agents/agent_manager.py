import logging
import os
import json
import uuid
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import asyncio
import time

# Import MCP client
from ..mcp.client import MCPCoordinatorClient

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AgentManager")

class Agent:
    """Base class for all agents"""
    
    def __init__(self, 
                id: str, 
                name: str, 
                description: str, 
                system_prompt: str,
                required_tools: List[str] = None):
        """Initialize an agent
        
        Args:
            id: Unique ID for the agent
            name: Name of the agent
            description: Description of the agent
            system_prompt: System prompt to use
            required_tools: List of required tools
        """
        self.id = id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.required_tools = required_tools or []
        self.llm_backend = None
        self.mcp_client = None
    
    def set_llm(self, llm_backend):
        """Set the LLM backend to use
        
        Args:
            llm_backend: Backend instance
        """
        self.llm_backend = llm_backend
    
    def set_mcp_client(self, mcp_client):
        """Set the MCP client to use
        
        Args:
            mcp_client: MCP client instance
        """
        self.mcp_client = mcp_client
    
    async def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Run the agent on a user input
        
        Args:
            user_input: User's input
            context: Additional context
            
        Returns:
            str: Agent's response
        """
        raise NotImplementedError("Subclasses must implement run()")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary
        
        Returns:
            Dict representation of the agent
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "required_tools": self.required_tools,
            "type": self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create agent from dictionary
        
        Args:
            data: Dictionary representation of agent
            
        Returns:
            Agent instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            system_prompt=data["system_prompt"],
            required_tools=data.get("required_tools", [])
        )


class DirectAgent(Agent):
    """Agent that uses LLM directly without additional tools"""
    
    async def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Run the agent on a user input
        
        Args:
            user_input: User's input
            context: Additional context
            
        Returns:
            str: Agent's response
        """
        context = context or {}
        
        if not self.llm_backend:
            return "Error: No LLM backend set for agent"
        
        # Prepare conversation history
        conversation_history = context.get("conversation_history", [])
        
        # Generate response
        response = self.llm_backend.generate(
            prompt=user_input,
            system_prompt=self.system_prompt,
            conversation_history=conversation_history
        )
        
        return response


class KDEDesktopAgent(Agent):
    """Agent that can interact with KDE desktop via MCP"""
    
    async def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Run the agent on a user input
        
        Args:
            user_input: User's input
            context: Additional context
            
        Returns:
            str: Agent's response
        """
        context = context or {}
        
        if not self.llm_backend:
            return "Error: No LLM backend set for agent"
            
        if not self.mcp_client:
            return "Error: No MCP client set for agent (required for KDE desktop access)"
        
        # Check if we need to run KRunner query
        if any(keyword in user_input.lower() for keyword in ["search", "find", "open", "launch", "run"]):
            # Extract search terms (simplified approach)
            search_terms = user_input.split()[-1]  # Just use the last word as search term
            
            try:
                # Run KRunner query
                krunner_results = await self.mcp_client.query_krunner(search_terms)
                
                # Extract results
                results = []
                if krunner_results and "results" in krunner_results:
                    for result in krunner_results["results"]:
                        results.append(f"- {result.get('display', 'Unknown')}")
                
                # Add results to context
                context_with_krunner = (
                    f"I searched for '{search_terms}' and found these results:\n" +
                    "\n".join(results)
                )
                
                # Append to system prompt temporarily
                enhanced_system_prompt = f"{self.system_prompt}\n\nKRunner search results: {context_with_krunner}"
                
            except Exception as e:
                logger.error(f"Failed to run KRunner query: {e}")
                enhanced_system_prompt = self.system_prompt
        else:
            enhanced_system_prompt = self.system_prompt
        
        # Prepare conversation history
        conversation_history = context.get("conversation_history", [])
        
        # Generate response
        response = self.llm_backend.generate(
            prompt=user_input,
            system_prompt=enhanced_system_prompt,
            conversation_history=conversation_history
        )
        
        return response


class CodeExecutionAgent(Agent):
    """Agent that can execute code via MCP"""
    
    async def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Run the agent on a user input
        
        Args:
            user_input: User's input
            context: Additional context
            
        Returns:
            str: Agent's response
        """
        context = context or {}
        
        if not self.llm_backend:
            return "Error: No LLM backend set for agent"
            
        if not self.mcp_client:
            return "Error: No MCP client set for agent (required for code execution)"
        
        # Generate initial response (which might include code)
        initial_response = self.llm_backend.generate(
            prompt=user_input,
            system_prompt=self.system_prompt,
            conversation_history=context.get("conversation_history", [])
        )
        
        # Check if response contains code blocks
        import re
        code_blocks = re.findall(r"```(\w*)\n(.*?)```", initial_response, re.DOTALL)
        
        if not code_blocks:
            # No code to execute
            return initial_response
        
        # Execute each code block
        execution_results = []
        
        for lang, code in code_blocks:
            # Determine language
            language = lang.strip().lower() or "python"  # Default to Python if not specified
            
            try:
                # Execute code via MCP
                result = await self.mcp_client.execute_code(code, language)
                
                # Format result
                exec_result = f"**Execution result:**\n```\n{result.get('output', '')}\n```"
                execution_results.append(exec_result)
                
            except Exception as e:
                logger.error(f"Failed to execute code: {e}")
                execution_results.append(f"**Execution failed:** {str(e)}")
        
        # Combine original response with execution results
        final_response = initial_response + "\n\n" + "\n\n".join(execution_results)
        
        return final_response


class DataAnalysisAgent(Agent):
    """Agent that can analyze data via MCP"""
    
    async def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Run the agent on a user input
        
        Args:
            user_input: User's input
            context: Additional context
            
        Returns:
            str: Agent's response
        """
        context = context or {}
        
        if not self.llm_backend:
            return "Error: No LLM backend set for agent"
            
        if not self.mcp_client:
            return "Error: No MCP client set for agent (required for data analysis)"
        
        # Generate initial response
        response = self.llm_backend.generate(
            prompt=user_input,
            system_prompt=self.system_prompt,
            conversation_history=context.get("conversation_history", [])
        )
        
        # Check if context contains data to analyze
        data = context.get("data")
        if not data:
            return response
        
        try:
            # Analyze data via MCP
            analysis_result = await self.mcp_client.analyze_data(data, "summary")
            
            # Format result
            analysis_summary = f"**Data Analysis:**\n```\n{json.dumps(analysis_result.get('summary', {}), indent=2)}\n```"
            
            # Combine original response with analysis
            final_response = response + "\n\n" + analysis_summary
            
            return final_response
            
        except Exception as e:
            logger.error(f"Failed to analyze data: {e}")
            return response


class NetworkAgent(Agent):
    """Agent that can perform network operations via MCP"""
    
    async def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Run the agent on a user input
        
        Args:
            user_input: User's input
            context: Additional context
            
        Returns:
            str: Agent's response
        """
        context = context or {}
        
        if not self.llm_backend:
            return "Error: No LLM backend set for agent"
            
        if not self.mcp_client:
            return "Error: No MCP client set for agent (required for network operations)"
        
        # Extract URLs from input (simplified approach)
        import re
        urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', user_input)
        
        if not urls:
            # No URLs to fetch
            return self.llm_backend.generate(
                prompt=user_input,
                system_prompt=self.system_prompt,
                conversation_history=context.get("conversation_history", [])
            )
        
        # Fetch first URL
        try:
            url = urls[0]
            response = await self.mcp_client.http_request(url)
            
            # Add fetched content to context
            content = response.get("body", "")
            if len(content) > 1000:
                content = content[:1000] + "...(truncated)"
                
            enhanced_system_prompt = (
                f"{self.system_prompt}\n\n"
                f"Content from {url}:\n{content}"
            )
            
            # Generate response with enhanced context
            return self.llm_backend.generate(
                prompt=user_input,
                system_prompt=enhanced_system_prompt,
                conversation_history=context.get("conversation_history", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch URL: {e}")
            return self.llm_backend.generate(
                prompt=user_input,
                system_prompt=f"{self.system_prompt}\n\nNote: Failed to fetch URL due to error: {str(e)}",
                conversation_history=context.get("conversation_history", [])
            )


class AgentManager:
    """Manages the creation and execution of agents"""
    
    def __init__(self, llm_backend=None, mcp_client=None, structured_storage=None):
        """Initialize the agent manager
        
        Args:
            llm_backend: Default LLM backend to use
            mcp_client: MCP client for tools
            structured_storage: Structured storage for agent persistence
        """
        self.llm_backend = llm_backend
        self.mcp_client = mcp_client
        self.structured_storage = structured_storage
        self.agents = {}
        
        # Load agents
        self._load_agents()
    
    def _load_agents(self):
        """Load agents from storage"""
        if not self.structured_storage:
            self._create_default_agents()
            return
            
        # Load agents from structured storage
        agents = self.structured_storage.list_agent_models(type="agent")
        
        if not agents:
            self._create_default_agents()
            return
            
        # Convert to Agent objects
        for agent_id, agent_data in agents.items():
            try:
                agent_type = agent_data.get("configuration", {}).get("type", "DirectAgent")
                
                # Create agent based on type
                if agent_type == "DirectAgent":
                    agent = DirectAgent.from_dict(agent_data)
                elif agent_type == "KDEDesktopAgent":
                    agent = KDEDesktopAgent.from_dict(agent_data)
                elif agent_type == "CodeExecutionAgent":
                    agent = CodeExecutionAgent.from_dict(agent_data)
                elif agent_type == "DataAnalysisAgent":
                    agent = DataAnalysisAgent.from_dict(agent_data)
                elif agent_type == "NetworkAgent":
                    agent = NetworkAgent.from_dict(agent_data)
                else:
                    # Default to DirectAgent
                    agent = DirectAgent.from_dict(agent_data)
                
                # Set backend and client
                agent.set_llm(self.llm_backend)
                agent.set_mcp_client(self.mcp_client)
                
                # Add to agents dict
                self.agents[agent_id] = agent
                
            except Exception as e:
                logger.error(f"Failed to load agent {agent_id}: {e}")
    
    def _create_default_agents(self):
        """Create default agents"""
        # Create a basic assistant agent
        assistant_id = str(uuid.uuid4())
        assistant = DirectAgent(
            id=assistant_id,
            name="Assistant",
            description="Basic assistant that responds to general queries",
            system_prompt="You are a helpful assistant for KDE Plasma desktop users. Provide clear and concise answers."
        )
        assistant.set_llm(self.llm_backend)
        assistant.set_mcp_client(self.mcp_client)
        self.agents[assistant_id] = assistant
        
        # Create a KDE desktop agent
        kde_id = str(uuid.uuid4())
        kde_agent = KDEDesktopAgent(
            id=kde_id,
            name="KDE Helper",
            description="Assistant that can interact with KDE desktop",
            system_prompt="You are a KDE desktop assistant. You can help users with KDE-specific tasks and provide information about KDE Plasma desktop environment.",
            required_tools=["kde_mcp"]
        )
        kde_agent.set_llm(self.llm_backend)
        kde_agent.set_mcp_client(self.mcp_client)
        self.agents[kde_id] = kde_agent
        
        # Create a code agent
        code_id = str(uuid.uuid4())
        code_agent = CodeExecutionAgent(
            id=code_id,
            name="Code Assistant",
            description="Assistant that can execute code and provide programming help",
            system_prompt="You are a programming assistant. You can help users with coding tasks and execute code for them. When providing code examples, use markdown code blocks with the appropriate language specifier.",
            required_tools=["code_mcp"]
        )
        code_agent.set_llm(self.llm_backend)
        code_agent.set_mcp_client(self.mcp_client)
        self.agents[code_id] = code_agent
        
        # Save agents if storage is available
        if self.structured_storage:
            for agent_id, agent in self.agents.items():
                try:
                    self.structured_storage.save_agent_model(
                        id=agent.id,
                        name=agent.name,
                        type="agent",
                        system_prompt=agent.system_prompt,
                        configuration=agent.to_dict()
                    )
                except Exception as e:
                    logger.error(f"Failed to save agent {agent_id}: {e}")
    
    def add_agent(self, 
                 name: str, 
                 description: str, 
                 system_prompt: str,
                 agent_type: str = "DirectAgent",
                 required_tools: List[str] = None) -> str:
        """Add a new agent
        
        Args:
            name: Name of the agent
            description: Description of the agent
            system_prompt: System prompt to use
            agent_type: Type of agent to create
            required_tools: List of required tools
            
        Returns:
            str: ID of the new agent
        """
        agent_id = str(uuid.uuid4())
        
        # Create agent based on type
        if agent_type == "KDEDesktopAgent":
            agent = KDEDesktopAgent(
                id=agent_id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                required_tools=required_tools
            )
        elif agent_type == "CodeExecutionAgent":
            agent = CodeExecutionAgent(
                id=agent_id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                required_tools=required_tools
            )
        elif agent_type == "DataAnalysisAgent":
            agent = DataAnalysisAgent(
                id=agent_id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                required_tools=required_tools
            )
        elif agent_type == "NetworkAgent":
            agent = NetworkAgent(
                id=agent_id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                required_tools=required_tools
            )
        else:
            # Default to DirectAgent
            agent = DirectAgent(
                id=agent_id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                required_tools=required_tools
            )
        
        # Set backend and client
        agent.set_llm(self.llm_backend)
        agent.set_mcp_client(self.mcp_client)
        
        # Add to agents dict
        self.agents[agent_id] = agent
        
        # Save agent if storage is available
        if self.structured_storage:
            try:
                self.structured_storage.save_agent_model(
                    id=agent.id,
                    name=agent.name,
                    type="agent",
                    system_prompt=agent.system_prompt,
                    configuration=agent.to_dict()
                )
            except Exception as e:
                logger.error(f"Failed to save agent {agent_id}: {e}")
        
        return agent_id
    
    def update_agent(self, 
                    id: str, 
                    name: Optional[str] = None,
                    description: Optional[str] = None,
                    system_prompt: Optional[str] = None) -> bool:
        """Update an agent
        
        Args:
            id: ID of the agent to update
            name: New name (or None to keep current)
            description: New description (or None to keep current)
            system_prompt: New system prompt (or None to keep current)
            
        Returns:
            bool: True if successful
        """
        if id not in self.agents:
            logger.error(f"Agent not found: {id}")
            return False
            
        agent = self.agents[id]
        
        # Update properties
        if name is not None:
            agent.name = name
            
        if description is not None:
            agent.description = description
            
        if system_prompt is not None:
            agent.system_prompt = system_prompt
            
        # Save agent if storage is available
        if self.structured_storage:
            try:
                self.structured_storage.save_agent_model(
                    id=agent.id,
                    name=agent.name,
                    type="agent",
                    system_prompt=agent.system_prompt,
                    configuration=agent.to_dict()
                )
            except Exception as e:
                logger.error(f"Failed to save agent {id}: {e}")
        
        return True
    
    def delete_agent(self, id: str) -> bool:
        """Delete an agent
        
        Args:
            id: ID of the agent to delete
            
        Returns:
            bool: True if successful
        """
        if id not in self.agents:
            logger.error(f"Agent not found: {id}")
            return False
            
        # Remove agent
        del self.agents[id]
        
        # Delete from storage if available
        if self.structured_storage:
            try:
                self.structured_storage.delete_agent_model(id)
            except Exception as e:
                logger.error(f"Failed to delete agent {id} from storage: {e}")
        
        return True
    
    def get_agent(self, id: str) -> Optional[Agent]:
        """Get an agent by ID
        
        Args:
            id: ID of the agent
            
        Returns:
            Agent instance, or None if not found
        """
        return self.agents.get(id)
    
    def list_agents(self) -> Dict[str, Agent]:
        """List all agents
        
        Returns:
            Dict mapping agent IDs to Agent instances
        """
        return self.agents
    
    def set_llm_backend(self, llm_backend):
        """Set the LLM backend for all agents
        
        Args:
            llm_backend: LLM backend instance
        """
        self.llm_backend = llm_backend
        
        # Update all agents
        for agent in self.agents.values():
            agent.set_llm(llm_backend)
    
    def set_mcp_client(self, mcp_client):
        """Set the MCP client for all agents
        
        Args:
            mcp_client: MCP client instance
        """
        self.mcp_client = mcp_client
        
        # Update all agents
        for agent in self.agents.values():
            agent.set_mcp_client(mcp_client)
    
    async def run_agent(self, 
                       agent_id: str, 
                       user_input: str, 
                       context: Dict[str, Any] = None) -> str:
        """Run an agent on a user input
        
        Args:
            agent_id: ID of the agent to run
            user_input: User's input
            context: Additional context
            
        Returns:
            str: Agent's response
        """
        agent = self.get_agent(agent_id)
        
        if not agent:
            return f"Error: Agent not found: {agent_id}"
            
        if not agent.llm_backend:
            agent.set_llm(self.llm_backend)
            
        if not agent.mcp_client:
            agent.set_mcp_client(self.mcp_client)
            
        # Run the agent
        return await agent.run(user_input, context)