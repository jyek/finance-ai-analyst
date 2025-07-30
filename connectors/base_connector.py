"""
Base connector class for external software integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime


class BaseConnector(ABC):
    """Base class for all external software connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with configuration.
        
        Args:
            config: Configuration dictionary containing API keys, endpoints, etc.
        """
        self.config = config
        self.authenticated = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the external service.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the external service.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    def save_to_drive(self, data: Any, filename: str, folder: str = "connectors") -> str:
        """
        Save data to the drive folder.
        
        Args:
            data: Data to save (dict, list, or string)
            filename: Name of the file to save
            folder: Subfolder within drive to save to
            
        Returns:
            str: Path to the saved file
        """
        # Ensure drive folder exists
        drive_path = os.path.join("drive", folder)
        os.makedirs(drive_path, exist_ok=True)
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name, ext = os.path.splitext(filename)
        filename_with_timestamp = f"{base_name}_{timestamp}{ext}"
        
        file_path = os.path.join(drive_path, filename_with_timestamp)
        
        # Save data based on type
        if isinstance(data, (dict, list)):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        return file_path
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value safely.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default) 