#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class ModelConfig:
    """Configuration for AI model connections"""
    
    DEFAULT_MODELS = [
        {
            "id": "default",
            "name": "Default Model",
            "description": "Default AI model",
            "context_window": 4096,
            "max_tokens": 1024
        }
    ]
    
    def __init__(self, settings_manager):
        """Initialize model configuration"""
        self.settings_manager = settings_manager
        self.models = []
        self.load_models()
    
    def load_models(self):
        """Load model configurations"""
        # Start with default models
        self.models = self.DEFAULT_MODELS.copy()
        
        # Load user-defined models from settings
        user_models_str = self.settings_manager.get("model/user_models", "[]")
        try:
            import json
            user_models = json.loads(user_models_str)
            if isinstance(user_models, list):
                self.models.extend(user_models)
        except Exception:
            # If parsing fails, just use the defaults
            pass
    
    def save_models(self):
        """Save model configurations"""
        # Filter out default models
        default_ids = [m["id"] for m in self.DEFAULT_MODELS]
        user_models = [m for m in self.models if m["id"] not in default_ids]
        
        # Save user models to settings
        import json
        self.settings_manager.set("model/user_models", json.dumps(user_models))
        self.settings_manager.save()
    
    def get_model_by_id(self, model_id):
        """Get a model configuration by ID"""
        for model in self.models:
            if model["id"] == model_id:
                return model
        
        # Return the default model if not found
        return self.models[0]
    
    def add_model(self, model_data):
        """Add a new model configuration"""
        # Check if a model with this ID already exists
        for i, model in enumerate(self.models):
            if model["id"] == model_data["id"]:
                # Update existing model
                self.models[i] = model_data
                self.save_models()
                return
        
        # Add new model
        self.models.append(model_data)
        self.save_models()
    
    def remove_model(self, model_id):
        """Remove a model configuration"""
        # Cannot remove default models
        default_ids = [m["id"] for m in self.DEFAULT_MODELS]
        if model_id in default_ids:
            return False
        
        # Remove from the list
        self.models = [m for m in self.models if m["id"] != model_id]
        self.save_models()
        return True
    
    def get_all_models(self):
        """Get all model configurations"""
        return self.models