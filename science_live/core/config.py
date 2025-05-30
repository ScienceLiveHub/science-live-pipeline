# ============================================================================
# science_live/core/config.py
# ============================================================================

"""
Configuration Management
=======================

Configuration system for Science Live applications with support for
YAML, JSON, and environment variables.
"""

import os
import yaml
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


@dataclass
class EndpointConfig:
    """Configuration for nanopub endpoints"""
    name: str
    type: str  # 'standard', 'test', 'custom'
    url: str
    is_default: bool = False
    timeout: int = 30
    retry_attempts: int = 3
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class TemplateConfig:
    """Configuration for template system"""
    repository_type: str = 'network'  # 'network', 'local', 'hybrid'
    cache_enabled: bool = True
    cache_dir: str = "./template_cache"
    cache_ttl_hours: int = 24
    preload_templates: List[str] = field(default_factory=list)
    custom_templates_dir: Optional[str] = None


@dataclass
class ProcessorConfig:
    """Configuration for query processors"""
    enabled_processors: List[str] = field(default_factory=lambda: ['template_based', 'text_search'])
    text_search_limit: int = 20
    template_match_threshold: float = 0.3
    sparql_timeout: int = 30
    enable_caching: bool = True


@dataclass
class UIConfig:
    """Configuration for user interfaces"""
    interface_type: str = 'web'  # 'web', 'api', 'cli', 'jupyter'
    theme: str = 'default'
    enable_suggestions: bool = True
    max_results_per_page: int = 20
    enable_export: bool = True
    export_formats: List[str] = field(default_factory=lambda: ['json', 'csv', 'rdf'])


@dataclass
class ScienceLiveConfig:
    """Main configuration for Science Live applications"""
    app_name: str
    app_type: str = 'general'  # 'general', 'citation_explorer', 'concept_explorer', etc.
    version: str = "1.0.0"
    
    endpoints: List[EndpointConfig] = field(default_factory=list)
    templates: TemplateConfig = field(default_factory=TemplateConfig)
    processors: ProcessorConfig = field(default_factory=ProcessorConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    
    # Extensions and plugins
    plugins: List[str] = field(default_factory=list)
    custom_modules: Dict[str, str] = field(default_factory=dict)
    
    # Logging and monitoring
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_endpoint: Optional[str] = None


class ConfigLoader:
    """Load configuration from various sources"""
    
    @staticmethod
    def from_yaml(config_path: Union[str, Path]) -> ScienceLiveConfig:
        """Load configuration from YAML file"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return ConfigLoader._dict_to_config(config_data)
    
    @staticmethod
    def from_json(config_path: Union[str, Path]) -> ScienceLiveConfig:
        """Load configuration from JSON file"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return ConfigLoader._dict_to_config(config_data)
    
    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> ScienceLiveConfig:
        """Load configuration from dictionary"""
        return ConfigLoader._dict_to_config(config_dict)
    
    @staticmethod
    def from_env(prefix: str = "SCIENCE_LIVE_") -> ScienceLiveConfig:
        """Load configuration from environment variables"""
        config_data = {}
        
        # Extract environment variables with the given prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config_data[config_key] = value
        
        # Set defaults for required fields
        config_data.setdefault('app_name', 'Science Live')
        config_data.setdefault('app_type', 'general')
        
        return ConfigLoader._dict_to_config(config_data)
    
    @staticmethod
    def _dict_to_config(data: Dict[str, Any]) -> ScienceLiveConfig:
        """Convert dictionary to configuration object"""
        # Parse endpoints
        endpoints = []
        for ep_data in data.get('endpoints', []):
            endpoints.append(EndpointConfig(**ep_data))
        
        # Parse template config
        template_data = data.get('templates', {})
        templates = TemplateConfig(**template_data)
        
        # Parse processor config
        processor_data = data.get('processors', {})
        processors = ProcessorConfig(**processor_data)
        
        # Parse UI config
        ui_data = data.get('ui', {})
        ui = UIConfig(**ui_data)
        
        return ScienceLiveConfig(
            app_name=data['app_name'],
            app_type=data.get('app_type', 'general'),
            version=data.get('version', '1.0.0'),
            endpoints=endpoints,
            templates=templates,
            processors=processors,
            ui=ui,
            plugins=data.get('plugins', []),
            custom_modules=data.get('custom_modules', {}),
            log_level=data.get('log_level', 'INFO'),
            enable_metrics=data.get('enable_metrics', True),
            metrics_endpoint=data.get('metrics_endpoint')
        )
    
    @staticmethod
    def create_default_config() -> ScienceLiveConfig:
        """Create a default configuration"""
        return ScienceLiveConfig(
            app_name="Science Live Default",
            app_type="general",
            endpoints=[
                EndpointConfig(
                    name="test",
                    type="test",
                    url="https://test.nanopub.org",
                    is_default=True
                )
            ]
        )


def save_config(config: ScienceLiveConfig, path: Union[str, Path], format: str = 'yaml'):
    """Save configuration to file"""
    path = Path(path)
    
    # Convert to dict (simplified)
    config_dict = {
        'app_name': config.app_name,
        'app_type': config.app_type,
        'version': config.version,
        'endpoints': [
            {
                'name': ep.name,
                'type': ep.type,
                'url': ep.url,
                'is_default': ep.is_default,
                'timeout': ep.timeout
            }
            for ep in config.endpoints
        ],
        'log_level': config.log_level,
        'enable_metrics': config.enable_metrics
    }
    
    if format.lower() == 'yaml':
        with open(path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    elif format.lower() == 'json':
        with open(path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")

