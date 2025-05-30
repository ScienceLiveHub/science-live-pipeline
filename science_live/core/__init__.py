# ============================================================================
# science_live/core/__init__.py
# ============================================================================

"""
Science Live Core: Infrastructure Components
===========================================

Core infrastructure components for Science Live including:
- Endpoint management for nanopub servers
- Configuration system
- Caching and performance utilities
- Authentication and security

Usage:
    from science_live.core import EndpointManager, ScienceLiveConfig
    
    # Setup endpoints
    endpoint_manager = EndpointManager()
    endpoint_manager.register_endpoint('production', StandardNanopubEndpoint(url))
    
    # Load configuration
    config = ScienceLiveConfig.from_yaml('config.yaml')
"""

from .endpoints import EndpointManager, NanopubEndpoint, StandardNanopubEndpoint
from .config import ScienceLiveConfig, ConfigLoader

__all__ = [
    'EndpointManager',
    'NanopubEndpoint', 
    'StandardNanopubEndpoint',
    'ScienceLiveConfig',
    'ConfigLoader'
]

