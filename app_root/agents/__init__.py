# Agents module for KDE AI Interface
from .agent_manager import (
    Agent, 
    DirectAgent, 
    KDEDesktopAgent, 
    CodeExecutionAgent, 
    DataAnalysisAgent, 
    NetworkAgent, 
    AgentManager
)

__all__ = [
    'Agent',
    'DirectAgent',
    'KDEDesktopAgent',
    'CodeExecutionAgent',
    'DataAnalysisAgent',
    'NetworkAgent',
    'AgentManager'
]