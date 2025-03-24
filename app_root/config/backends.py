import logging
import os
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BackendManager")

class BackendManager:
    """Manages multiple LLM backends (OpenAI, Ollama, etc.)"""
    
    def __init__(self):
        """Initialize the backend manager"""
        self.backends = {}
        self.default_backend = None
        self.config_dir = Path.home() / ".config" / "kde-ai-interface"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "backends.json"
        
        # Load backends
        self._load_backends()
    
    def _load_backends(self):
        """Load backend configurations from file"""
        if not self.config_file.exists():
            # Create default configuration
            self._create_default_backends()
            return
            
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                
            # Parse backend configurations
            self.backends = data.get("backends", {})
            self.default_backend = data.get("default_backend")
            
            logger.info(f"Loaded {len(self.backends)} backends")
        except Exception as e:
            logger.error(f"Failed to load backends: {e}")
            # Create default configuration
            self._create_default_backends()
    
    def _create_default_backends(self):
        """Create default backend configurations"""
        # OpenAI backend
        openai_id = str(uuid.uuid4())
        self.backends[openai_id] = {
            "id": openai_id,
            "name": "OpenAI",
            "type": "openai",
            "enabled": True,
            "config": {
                "api_key": os.environ.get("OPENAI_API_KEY", ""),
                "base_url": "https://api.openai.com/v1",
                "default_model": "gpt-4o-mini",
                "available_models": ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"]
            }
        }
        
        # Ollama backend
        ollama_id = str(uuid.uuid4())
        self.backends[ollama_id] = {
            "id": ollama_id,
            "name": "Ollama (Local)",
            "type": "ollama",
            "enabled": True,
            "config": {
                "api_url": "http://localhost:11434",
                "default_model": "llama3",
                "available_models": ["llama3", "mistral", "phi3"]
            }
        }
        
        # Set default backend to OpenAI
        self.default_backend = openai_id
        
        # Save configuration
        self._save_backends()
        
        logger.info("Created default backend configurations")
    
    def _save_backends(self):
        """Save backend configurations to file"""
        try:
            data = {
                "backends": self.backends,
                "default_backend": self.default_backend
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Saved backend configurations")
        except Exception as e:
            logger.error(f"Failed to save backends: {e}")
    
    def add_backend(self, 
                   name: str, 
                   type: str, 
                   config: Dict[str, Any],
                   enabled: bool = True) -> str:
        """Add a new backend
        
        Args:
            name: Name of the backend
            type: Type of backend (openai, ollama, etc.)
            config: Backend configuration
            enabled: Whether the backend is enabled
            
        Returns:
            str: ID of the new backend
        """
        backend_id = str(uuid.uuid4())
        
        self.backends[backend_id] = {
            "id": backend_id,
            "name": name,
            "type": type,
            "enabled": enabled,
            "config": config
        }
        
        # Set as default if no default is set
        if not self.default_backend:
            self.default_backend = backend_id
            
        # Save configuration
        self._save_backends()
        
        return backend_id
    
    def update_backend(self, 
                      id: str, 
                      name: Optional[str] = None,
                      type: Optional[str] = None,
                      config: Optional[Dict[str, Any]] = None,
                      enabled: Optional[bool] = None) -> bool:
        """Update a backend
        
        Args:
            id: ID of the backend to update
            name: New name (or None to keep current)
            type: New type (or None to keep current)
            config: New configuration (or None to keep current)
            enabled: New enabled status (or None to keep current)
            
        Returns:
            bool: True if successful
        """
        if id not in self.backends:
            logger.error(f"Backend not found: {id}")
            return False
            
        # Update properties
        if name is not None:
            self.backends[id]["name"] = name
            
        if type is not None:
            self.backends[id]["type"] = type
            
        if config is not None:
            self.backends[id]["config"] = config
            
        if enabled is not None:
            self.backends[id]["enabled"] = enabled
            
        # Save configuration
        self._save_backends()
        
        return True
    
    def delete_backend(self, id: str) -> bool:
        """Delete a backend
        
        Args:
            id: ID of the backend to delete
            
        Returns:
            bool: True if successful
        """
        if id not in self.backends:
            logger.error(f"Backend not found: {id}")
            return False
            
        # Remove backend
        del self.backends[id]
        
        # Update default if needed
        if self.default_backend == id:
            self.default_backend = next(iter(self.backends.keys())) if self.backends else None
            
        # Save configuration
        self._save_backends()
        
        return True
    
    def get_backend(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a backend configuration
        
        Args:
            id: ID of the backend
            
        Returns:
            Dict containing backend configuration, or None if not found
        """
        return self.backends.get(id)
    
    def get_backends(self, type: Optional[str] = None, enabled_only: bool = False) -> Dict[str, Dict[str, Any]]:
        """Get all backends
        
        Args:
            type: Optional type filter
            enabled_only: Whether to include only enabled backends
            
        Returns:
            Dict mapping backend IDs to configurations
        """
        if type is None and not enabled_only:
            return self.backends
            
        # Filter backends
        filtered = {}
        for id, backend in self.backends.items():
            if type is not None and backend["type"] != type:
                continue
                
            if enabled_only and not backend["enabled"]:
                continue
                
            filtered[id] = backend
            
        return filtered
    
    def get_default_backend(self) -> Optional[Dict[str, Any]]:
        """Get the default backend configuration
        
        Returns:
            Dict containing default backend configuration, or None if not set
        """
        if not self.default_backend:
            return None
            
        return self.backends.get(self.default_backend)
    
    def set_default_backend(self, id: str) -> bool:
        """Set the default backend
        
        Args:
            id: ID of the backend to set as default
            
        Returns:
            bool: True if successful
        """
        if id not in self.backends:
            logger.error(f"Backend not found: {id}")
            return False
            
        self.default_backend = id
        
        # Save configuration
        self._save_backends()
        
        return True
    
    def instantiate_backend(self, id: str) -> Optional[Any]:
        """Instantiate a backend object
        
        Args:
            id: ID of the backend to instantiate
            
        Returns:
            Backend instance, or None if failed
        """
        if id not in self.backends:
            logger.error(f"Backend not found: {id}")
            return None
            
        backend = self.backends[id]
        
        if not backend["enabled"]:
            logger.error(f"Backend is disabled: {id}")
            return None
            
        type = backend["type"]
        config = backend["config"]
        
        try:
            # Create the backend instance based on type
            if type == "openai":
                from openai_backend import OpenAIBackend
                return OpenAIBackend(
                    api_key=config.get("api_key", ""),
                    model=config.get("default_model", "gpt-4o-mini")
                )
            elif type == "ollama":
                from ollama_backend import OllamaBackend
                return OllamaBackend(
                    server_url=config.get("api_url", "http://localhost:11434"),
                    model=config.get("default_model", "llama3")
                )
            else:
                logger.error(f"Unsupported backend type: {type}")
                return None
        except Exception as e:
            logger.error(f"Failed to instantiate backend: {e}")
            return None
    
    def instantiate_default_backend(self) -> Optional[Any]:
        """Instantiate the default backend object
        
        Returns:
            Default backend instance, or None if failed
        """
        if not self.default_backend:
            logger.error("No default backend set")
            return None
            
        return self.instantiate_backend(self.default_backend)