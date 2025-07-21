"""
Configuration file for Finance Workspace Agent

This file centralizes all API keys and configuration settings for the project.
You can either set values directly in this file or use environment variables.
"""

import os
from typing import Dict, Any, Optional

class Config:
    """Centralized configuration for the Finance Workspace Agent"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Optional path to a JSON config file
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file if specified"""
        if self.config_file and os.path.exists(self.config_file):
            import json
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                # Update environment variables from file
                for key, value in file_config.items():
                    if key not in os.environ:
                        if key == "GOOGLE_OAUTH_CREDENTIALS_JSON":
                            # Keep OAuth credentials as a dictionary in memory
                            self._oauth_creds = value
                        else:
                            os.environ[key] = str(value)
                print(f"✅ Loaded configuration from {self.config_file}")
            except Exception as e:
                print(f"⚠️ Could not load config file: {e}")
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key"""
        return os.environ.get("OPENAI_API_KEY", "")
    
    @property
    def google_oauth_credentials_json(self):
        """Get Google OAuth credentials JSON"""
        # First check if we have stored credentials from config file
        if hasattr(self, '_oauth_creds'):
            return self._oauth_creds
        
        # Fall back to environment variable
        creds = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON", "")
        if creds and isinstance(creds, str):
            # If it's a string representation of a dict, convert it back to dict
            if creds.startswith('{') and creds.endswith('}'):
                try:
                    import json
                    return json.loads(creds)
                except:
                    pass
        return creds
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for agents"""
        return {
            "config_list": [
                {
                    "model": "gpt-4",
                    "api_key": self.openai_api_key
                }
            ],
            "temperature": 0.1,
            "timeout": 120
        }
    
    def validate(self) -> bool:
        """Validate that required configuration is present"""
        missing = []
        
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        
        if not self.google_oauth_credentials_json:
            missing.append("GOOGLE_OAUTH_CREDENTIALS_JSON")
        
        if missing:
            print(f"❌ Missing required configuration: {', '.join(missing)}")
            return False
        
        return True
    
    def print_status(self):
        """Print current configuration status"""
        print("🔧 Configuration Status:")
        print(f"   OpenAI API Key: {'✅ Set' if self.openai_api_key else '❌ Missing'}")
        print(f"   Google OAuth Credentials: {'✅ Set' if self.google_oauth_credentials_json else '❌ Missing'}")
        print(f"   Config File: {'✅ Loaded' if self.config_file and os.path.exists(self.config_file) else '❌ Not used'}")

# Global config instance
config = Config()

def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get configuration instance
    
    Args:
        config_file: Optional path to config file
        
    Returns:
        Config instance
    """
    if config_file:
        return Config(config_file)
    return config 