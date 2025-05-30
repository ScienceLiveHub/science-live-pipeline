# ============================================================================
# science_live/__init__.py
# ============================================================================

"""
Science Live: Semantic Knowledge Exploration for Scientific Research
====================================================================

A modular system for exploring scientific knowledge using nanopublications
and Rosetta statements.

Main Components:
- Pipeline: 7-step processing pipeline for natural language queries
- Core: Endpoint management and configuration
- Applications: Specialized scientific knowledge exploration apps

Example Usage:
    from science_live import ScienceLivePipeline
    from science_live.core import EndpointManager
    
    # Basic usage
    endpoint_manager = EndpointManager()
    pipeline = ScienceLivePipeline(endpoint_manager)
    result = await pipeline.process("What papers cite AlexNet?")
    
    # Advanced usage with custom config
    from science_live.pipeline import QuestionProcessor
    processor = QuestionProcessor(config={'debug': True})
"""

try:
    from .pipeline import ScienceLivePipeline
    from .core import EndpointManager, ScienceLiveConfig
    
    __all__ = [
        'ScienceLivePipeline',
        'EndpointManager', 
        'ScienceLiveConfig'
    ]
except ImportError:
    # Handle case where dependencies aren't installed yet
    __all__ = []

__version__ = "1.0.0"
__author__ = "Science Live Team"
__description__ = "Semantic knowledge exploration for scientific research"
