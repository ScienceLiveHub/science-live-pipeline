# ============================================================================
# tests/test_core/test_config.py
# ============================================================================

"""
Tests for Configuration Management
=================================
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from science_live.core.config import (
    ScienceLiveConfig, ConfigLoader, EndpointConfig, save_config
)


class TestConfigLoader:
    """Test ConfigLoader functionality"""
    
    def test_create_default_config(self):
        """Test creating default configuration"""
        config = ConfigLoader.create_default_config()
        
        assert config.app_name == "Science Live Default"
        assert config.app_type == "general"
        assert len(config.endpoints) == 1
        assert config.endpoints[0].name == "test"
    
    def test_from_dict(self):
        """Test loading from dictionary"""
        config_dict = {
            'app_name': 'Test App',
            'app_type': 'citation_explorer',
            'endpoints': [
                {
                    'name': 'production',
                    'type': 'standard',
                    'url': 'https://nanopub.org/sparql',
                    'is_default': True
                }
            ]
        }
        
        config = ConfigLoader.from_dict(config_dict)
        
        assert config.app_name == 'Test App'
        assert config.app_type == 'citation_explorer'
        assert len(config.endpoints) == 1
        assert config.endpoints[0].name == 'production'
    
    def test_from_yaml(self):
        """Test loading from YAML file"""
        config_data = {
            'app_name': 'YAML Test',
            'app_type': 'general',
            'endpoints': [
                {
                    'name': 'test',
                    'type': 'test',
                    'url': 'https://test.example.org',
                    'is_default': True
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            yaml_path = f.name
        
        try:
            config = ConfigLoader.from_yaml(yaml_path)
            assert config.app_name == 'YAML Test'
            assert len(config.endpoints) == 1
        finally:
            Path(yaml_path).unlink()
    
    def test_from_json(self):
        """Test loading from JSON file"""
        config_data = {
            'app_name': 'JSON Test',
            'app_type': 'general',
            'endpoints': []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            json_path = f.name
        
        try:
            config = ConfigLoader.from_json(json_path)
            assert config.app_name == 'JSON Test'
        finally:
            Path(json_path).unlink()
    
    def test_missing_file(self):
        """Test error handling for missing files"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.from_yaml('nonexistent.yaml')


class TestConfigSaving:
    """Test configuration saving"""
    
    def test_save_yaml(self):
        """Test saving configuration as YAML"""
        config = ConfigLoader.create_default_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_path = f.name
        
        try:
            save_config(config, yaml_path, 'yaml')
            
            # Load it back and verify
            loaded_config = ConfigLoader.from_yaml(yaml_path)
            assert loaded_config.app_name == config.app_name
        finally:
            Path(yaml_path).unlink()
    
    def test_save_json(self):
        """Test saving configuration as JSON"""
        config = ConfigLoader.create_default_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name
        
        try:
            save_config(config, json_path, 'json')
            
            # Load it back and verify
            loaded_config = ConfigLoader.from_json(json_path)
            assert loaded_config.app_name == config.app_name
        finally:
            Path(json_path).unlink()

