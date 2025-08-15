"""
Configuration management service for Fabric settings.
Handles reading/writing .env files and managing vendor configurations.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

from utils.logging import logger
from utils.io import atomic_write_text
from services.providers import VendorConfig, ProviderService


@dataclass
class FabricConfig:
    """Complete Fabric configuration."""
    default_vendor: Optional[str] = None
    default_model: Optional[str] = None
    vendors: Dict[str, VendorConfig] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 90
    
    def __post_init__(self):
        if self.vendors is None:
            self.vendors = {}


class ConfigurationManager:
    """Manages Fabric configuration reading and writing."""
    
    def __init__(self):
        # Use the actual user's home directory
        actual_home = os.path.expanduser("~")
        self.config_dir = Path(actual_home) / ".config" / "fabric"
        self.env_path = self.config_dir / ".env"
        self.config_json_path = self.config_dir / "ui_config.json"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> FabricConfig:
        """Load configuration from .env and config files."""
        config = FabricConfig()
        
        # Load vendors from ProviderService
        provider_service = ProviderService()
        vendor_configs = provider_service.load_vendor_configs()
        config.vendors = vendor_configs
        
        # Load .env file
        env_vars = self._read_env_file()
        
        # Set defaults from env (normalize vendor name)
        default_vendor = env_vars.get("DEFAULT_VENDOR", "")
        if default_vendor:
            # Normalize vendor name (OpenAI -> openai)
            config.default_vendor = default_vendor.lower()
        config.default_model = env_vars.get("DEFAULT_MODEL", "")
        
        # If default model but no vendor, try to detect vendor
        if config.default_model and not config.default_vendor:
            config.default_vendor = provider_service.detect_vendor_from_model(
                config.default_model
            )
        
        # Load UI-specific settings from JSON if exists
        if self.config_json_path.exists():
            try:
                with open(self.config_json_path, 'r') as f:
                    ui_settings = json.load(f)
                    config.temperature = ui_settings.get("temperature", config.temperature)
                    config.max_tokens = ui_settings.get("max_tokens", config.max_tokens)
                    config.timeout = ui_settings.get("timeout", config.timeout)
            except Exception as e:
                logger.warning(f"Could not load UI settings: {e}")
        
        return config
    
    def save_config(self, config: FabricConfig) -> bool:
        """Save configuration to files."""
        try:
            # Save defaults to .env (append/update)
            self._update_env_file({
                "DEFAULT_VENDOR": config.default_vendor or "",
                "DEFAULT_MODEL": config.default_model or ""
            })
            
            # Save UI settings to JSON
            ui_settings = {
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "timeout": config.timeout
            }
            atomic_write_text(
                self.config_json_path,
                json.dumps(ui_settings, indent=2)
            )
            
            logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def update_vendor_config(self, vendor: str, api_key: str = None, 
                           base_url: str = None) -> bool:
        """Update vendor-specific configuration."""
        try:
            provider_service = ProviderService()
            vendor_info = provider_service.VENDOR_CONFIGS.get(vendor)
            
            if not vendor_info:
                logger.error(f"Unknown vendor: {vendor}")
                return False
            
            updates = {}
            
            # Update API key if provided
            if api_key and vendor_info.get("env_var"):
                updates[vendor_info["env_var"]] = api_key
            
            # Update base URL if provided
            if base_url and vendor_info.get("base_url_var"):
                updates[vendor_info["base_url_var"]] = base_url
            
            if updates:
                self._update_env_file(updates)
                logger.info(f"Updated {vendor} configuration")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update vendor config: {e}")
            return False
    
    def get_active_vendors(self) -> Dict[str, VendorConfig]:
        """Get only vendors that are configured and enabled."""
        config = self.load_config()
        return {
            name: vendor 
            for name, vendor in config.vendors.items() 
            if vendor.enabled
        }
    
    def validate_vendor_access(self, vendor: str, model: str = None) -> bool:
        """Check if vendor/model combination is accessible."""
        provider_service = ProviderService()
        
        if model:
            return provider_service.validate_model_access(vendor, model)
        
        # Just check if vendor is configured
        vendors = self.get_active_vendors()
        return vendor in vendors
    
    def _read_env_file(self) -> Dict[str, str]:
        """Read environment variables from .env file."""
        env_vars = {}
        
        if not self.env_path.exists():
            return env_vars
        
        try:
            with open(self.env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
        except Exception as e:
            logger.warning(f"Error reading .env file: {e}")
        
        return env_vars
    
    def _update_env_file(self, updates: Dict[str, str]) -> None:
        """Update or append to .env file."""
        # Read existing content
        existing = {}
        lines = []
        
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                for line in f:
                    original_line = line
                    line = line.strip()
                    
                    if line and not line.startswith('#') and '=' in line:
                        key = line.split('=', 1)[0]
                        if key in updates:
                            # Replace this line
                            lines.append(f"{key}={updates[key]}\n")
                            existing[key] = True
                        else:
                            lines.append(original_line)
                    else:
                        lines.append(original_line)
        
        # Add new keys that weren't in the file
        for key, value in updates.items():
            if key not in existing:
                lines.append(f"{key}={value}\n")
        
        # Write back atomically
        content = ''.join(lines)
        atomic_write_text(self.env_path, content, mode=0o600)
    
    def export_config(self) -> str:
        """Export configuration as JSON string."""
        config = self.load_config()
        
        # Convert to dict for export
        export_data = {
            "default_vendor": config.default_vendor,
            "default_model": config.default_model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
            "vendors": {
                name: {
                    "enabled": vendor.enabled,
                    "has_api_key": bool(vendor.api_key),
                    "base_url": vendor.base_url,
                    "models": vendor.models
                }
                for name, vendor in config.vendors.items()
            }
        }
        
        return json.dumps(export_data, indent=2)
    
    def import_config(self, json_str: str) -> bool:
        """Import configuration from JSON string."""
        try:
            data = json.loads(json_str)
            
            config = FabricConfig(
                default_vendor=data.get("default_vendor"),
                default_model=data.get("default_model"),
                temperature=data.get("temperature", 0.7),
                max_tokens=data.get("max_tokens", 2000),
                timeout=data.get("timeout", 90)
            )
            
            return self.save_config(config)
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False


# Singleton instance
_config_manager = None

def get_config_manager() -> ConfigurationManager:
    """Get singleton ConfigurationManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager