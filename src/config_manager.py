"""
Configuration Manager
Handles loading and managing configuration from YAML files and environment variables.
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration from YAML and environment variables."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Load YAML configuration
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Replace environment variable placeholders
        self._replace_env_vars(self.config)
        
        logger.info(f"Configuration loaded from {self.config_path}")
    
    def _replace_env_vars(self, config: Any) -> Any:
        """
        Recursively replace environment variable placeholders in configuration.
        
        Args:
            config: Configuration dictionary or value
            
        Returns:
            Configuration with environment variables replaced
        """
        if isinstance(config, dict):
            for key, value in config.items():
                config[key] = self._replace_env_vars(value)
        elif isinstance(config, list):
            config = [self._replace_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            # Extract environment variable name
            env_var = config[2:-1]
            env_value = os.getenv(env_var)
            if env_value is None:
                logger.warning(f"Environment variable {env_var} not set, using placeholder")
                return config
            return env_value
        
        return config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration value (e.g., 'azure.subscription_id')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration value
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_azure_config(self) -> Dict[str, str]:
        """Get Azure-specific configuration."""
        return {
            'subscription_id': self.get('azure.subscription_id'),
            'tenant_id': self.get('azure.tenant_id'),
            'client_id': self.get('azure.client_id'),
            'client_secret': self.get('azure.client_secret'),
            'resource_group': self.get('azure.resource_group'),
            'function_name': self.get('azure.function_name')
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.get('monitoring', {})
    
    def get_ica_config(self) -> Dict[str, Any]:
        """Get ICA configuration."""
        return self.get('ica', {})
    
    def get_bob_config(self) -> Dict[str, Any]:
        """Get BOB configuration."""
        return self.get('bob', {})
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration."""
        return self.get('notifications', {})
    
    def validate_config(self) -> bool:
        """
        Validate that all required configuration values are present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_keys = [
            'azure.subscription_id',
            'azure.tenant_id',
            'azure.client_id',
            'azure.client_secret',
            'azure.resource_group',
            'azure.function_name'
        ]
        
        missing_keys = []
        for key in required_keys:
            value = self.get(key)
            if value is None or (isinstance(value, str) and value.startswith("${")):
                missing_keys.append(key)
        
        if missing_keys:
            logger.error(f"Missing required configuration: {', '.join(missing_keys)}")
            return False
        
        logger.info("Configuration validation successful")
        return True
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()
        logger.info("Configuration reloaded")


# Global configuration instance
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: str = "config.yaml") -> ConfigManager:
    """
    Get or create the global configuration instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        ConfigManager instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance

# Made with Bob
