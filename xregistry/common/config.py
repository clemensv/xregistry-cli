"""
Configuration management for xregistry-cli.

Provides hierarchical configuration with the following priority order:
1. Command-line arguments (highest priority)
2. Environment variables
3. User configuration file
4. Built-in defaults (lowest priority)

Configuration file location:
- Linux/macOS: ~/.config/xregistry/config.json
- Windows: %APPDATA%/xregistry/config.json
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import platformdirs


logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for model handling."""
    url: Optional[str] = None
    cache_timeout: int = 3600


@dataclass
class DefaultsConfig:
    """Default values for common CLI options."""
    project_name: Optional[str] = None
    language: Optional[str] = None
    style: Optional[str] = None
    output_dir: Optional[str] = None


@dataclass
class RegistryConfig:
    """Configuration for registry connections."""
    base_url: Optional[str] = None
    auth_token: Optional[str] = None
    timeout: int = 30


@dataclass
class XRegistryConfig:
    """Main configuration container."""
    model: ModelConfig = field(default_factory=ModelConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    registry: RegistryConfig = field(default_factory=RegistryConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "model": {
                "url": self.model.url,
                "cache_timeout": self.model.cache_timeout
            },
            "defaults": {
                "project_name": self.defaults.project_name,
                "language": self.defaults.language,
                "style": self.defaults.style,
                "output_dir": self.defaults.output_dir
            },
            "registry": {
                "base_url": self.registry.base_url,
                "auth_token": self.registry.auth_token,
                "timeout": self.registry.timeout
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> XRegistryConfig:
        """Create configuration from dictionary."""
        config = cls()
        
        if "model" in data:
            model_data = data["model"]
            config.model.url = model_data.get("url")
            config.model.cache_timeout = model_data.get("cache_timeout", 3600)
        
        if "defaults" in data:
            defaults_data = data["defaults"]
            config.defaults.project_name = defaults_data.get("project_name")
            config.defaults.language = defaults_data.get("language")
            config.defaults.style = defaults_data.get("style")
            config.defaults.output_dir = defaults_data.get("output_dir")
        
        if "registry" in data:
            registry_data = data["registry"]
            config.registry.base_url = registry_data.get("base_url")
            config.registry.auth_token = registry_data.get("auth_token")
            config.registry.timeout = registry_data.get("timeout", 30)
        
        return config


class ConfigManager:
    """Manages configuration loading, saving, and hierarchical resolution."""
    
    def __init__(self) -> None:
        self._config_dir = Path(platformdirs.user_config_dir("xregistry", "xregistry"))
        self._config_file = self._config_dir / "config.json"
        self._config: Optional[XRegistryConfig] = None
    
    @property
    def config_file_path(self) -> Path:
        """Get the configuration file path."""
        return self._config_file
    
    def ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Configuration directory ensured: {self._config_dir}")
        except OSError as e:
            logger.warning(f"Failed to create config directory {self._config_dir}: {e}")
            raise
    
    def load_config(self) -> XRegistryConfig:
        """Load configuration from file or return default configuration."""
        if self._config is not None:
            return self._config
        
        try:
            if self._config_file.exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = XRegistryConfig.from_dict(data)
                logger.debug(f"Configuration loaded from {self._config_file}")
            else:
                self._config = XRegistryConfig()
                logger.debug("Using default configuration (no config file found)")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load config from {self._config_file}: {e}. Using defaults.")
            self._config = XRegistryConfig()
        
        return self._config
    
    def save_config(self, config: Optional[XRegistryConfig] = None) -> None:
        """Save configuration to file."""
        if config is None:
            config = self.load_config()
        
        try:
            self.ensure_config_dir()
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)
            logger.info(f"Configuration saved to {self._config_file}")
            self._config = config  # Update cached config
        except OSError as e:
            logger.error(f"Failed to save config to {self._config_file}: {e}")
            raise
    
    def get_model_url(self, cli_arg: Optional[str] = None, env_var: Optional[str] = None) -> Optional[str]:
        """
        Get model URL with hierarchical priority resolution.
        
        Priority order:
        1. CLI argument
        2. Environment variable
        3. Config file
        4. None (use embedded model)
        """
        # 1. CLI argument (highest priority)
        if cli_arg:
            logger.debug(f"Using model URL from CLI argument: {cli_arg}")
            return cli_arg
        
        # 2. Environment variable
        if env_var:
            logger.debug(f"Using model URL from environment variable: {env_var}")
            return env_var
        
        # 3. Config file
        config = self.load_config()
        if config.model.url:
            logger.debug(f"Using model URL from config file: {config.model.url}")
            return config.model.url
        
        # 4. No override (use embedded model)
        logger.debug("No model URL override found, using embedded model")
        return None
    
    def set_config_value(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value using dot-notation key path.
        
        Examples:
        - "model.url" -> config.model.url = value
        - "defaults.language" -> config.defaults.language = value
        """
        config = self.load_config()
        keys = key_path.split(".")
        
        if len(keys) != 2:
            raise ValueError(f"Invalid key path: {key_path}. Expected format: 'section.key'")
        
        section, key = keys
        
        if section == "model":
            if key == "url":
                config.model.url = value
            elif key == "cache_timeout":
                config.model.cache_timeout = int(value) if value is not None else 3600
            else:
                raise ValueError(f"Unknown model config key: {key}")
        elif section == "defaults":
            if key == "project_name":
                config.defaults.project_name = value
            elif key == "language":
                config.defaults.language = value
            elif key == "style":
                config.defaults.style = value
            elif key == "output_dir":
                config.defaults.output_dir = value
            else:
                raise ValueError(f"Unknown defaults config key: {key}")
        elif section == "registry":
            if key == "base_url":
                config.registry.base_url = value
            elif key == "auth_token":
                config.registry.auth_token = value
            elif key == "timeout":
                config.registry.timeout = int(value) if value is not None else 30
            else:
                raise ValueError(f"Unknown registry config key: {key}")
        else:
            raise ValueError(f"Unknown config section: {section}")
        
        self.save_config(config)
        logger.info(f"Configuration updated: {key_path} = {value}")
    
    def get_config_value(self, key_path: str) -> Any:
        """Get a configuration value using dot-notation key path."""
        config = self.load_config()
        keys = key_path.split(".")
        
        if len(keys) != 2:
            raise ValueError(f"Invalid key path: {key_path}. Expected format: 'section.key'")
        
        section, key = keys
        
        if section == "model":
            if key == "url":
                return config.model.url
            elif key == "cache_timeout":
                return config.model.cache_timeout
        elif section == "defaults":
            if key == "project_name":
                return config.defaults.project_name
            elif key == "language":
                return config.defaults.language
            elif key == "style":
                return config.defaults.style
            elif key == "output_dir":
                return config.defaults.output_dir
        elif section == "registry":
            if key == "base_url":
                return config.registry.base_url
            elif key == "auth_token":
                return config.registry.auth_token
            elif key == "timeout":
                return config.registry.timeout
        
        raise ValueError(f"Unknown config path: {key_path}")
    
    def reset_config(self) -> None:
        """Reset configuration to defaults and remove config file."""
        try:
            if self._config_file.exists():
                self._config_file.unlink()
                logger.info(f"Configuration file removed: {self._config_file}")
        except OSError as e:
            logger.warning(f"Failed to remove config file {self._config_file}: {e}")
        
        self._config = XRegistryConfig()
        logger.info("Configuration reset to defaults")


# Global configuration manager instance
config_manager = ConfigManager()
