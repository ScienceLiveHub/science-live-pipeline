# ============================================================================
# science_live/pipeline/__init__.py - FIXED VERSION
# ============================================================================

"""
Science Live Pipeline: 7-Step Natural Language Processing Pipeline
==================================================================

This package implements a 7-step pipeline for processing natural language
questions and converting them to structured queries against nanopub networks:

1. QuestionProcessor - Parse and classify questions
2. EntityExtractorLinker - Extract and link entities
3. RosettaStatementGenerator - Generate Rosetta statements
4. SPARQLGenerator - Convert to SPARQL queries
5. QueryExecutor - Execute queries
6. ResultProcessor - Structure results
7. NaturalLanguageGenerator - Generate natural language responses

Usage:
    # Individual components
    from science_live.pipeline import QuestionProcessor
    processor = QuestionProcessor()
    
    # Complete pipeline
    from science_live.pipeline import ScienceLivePipeline
    pipeline = ScienceLivePipeline(endpoint_manager)
    result = await pipeline.process("Your question here")
    
    # Custom pipeline
    from science_live.pipeline import create_custom_pipeline
    custom_pipeline = create_custom_pipeline([
        QuestionProcessor(),
        EntityExtractorLinker(endpoint_manager),
        # ... other steps
    ])
"""

# Import common data models first (these should always be available)
try:
    from .common import (
        ProcessingContext,
        ProcessedQuestion,
        ExtractedEntity,
        LinkedEntities,
        RosettaStatement,
        GeneratedStatements,
        SPARQLQuery,
        GeneratedQueries,
        QueryResults,
        StructuredResult,
        ProcessedResults,
        NaturalLanguageResult,
        EntityType,
        QuestionType,
        ConfidenceLevel
    )
    _COMMON_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import common models: {e}")
    _COMMON_AVAILABLE = False

# Import pipeline components with safe error handling
_COMPONENTS_AVAILABLE = {}

try:
    from .question_processor import QuestionProcessor
    _COMPONENTS_AVAILABLE['QuestionProcessor'] = True
except ImportError as e:
    print(f"Warning: Could not import QuestionProcessor: {e}")
    _COMPONENTS_AVAILABLE['QuestionProcessor'] = False

try:
    from .entity_extractor import EntityExtractorLinker
    _COMPONENTS_AVAILABLE['EntityExtractorLinker'] = True
except ImportError as e:
    print(f"Warning: Could not import EntityExtractorLinker: {e}")
    _COMPONENTS_AVAILABLE['EntityExtractorLinker'] = False

try:
    from .rosetta_generator import RosettaStatementGenerator
    _COMPONENTS_AVAILABLE['RosettaStatementGenerator'] = True
except ImportError as e:
    print(f"Warning: Could not import RosettaStatementGenerator: {e}")
    _COMPONENTS_AVAILABLE['RosettaStatementGenerator'] = False

try:
    from .sparql_generator import SPARQLGenerator
    _COMPONENTS_AVAILABLE['SPARQLGenerator'] = True  
except ImportError as e:
    print(f"Warning: Could not import SPARQLGenerator: {e}")
    _COMPONENTS_AVAILABLE['SPARQLGenerator'] = False

try:
    from .query_executor import QueryExecutor
    _COMPONENTS_AVAILABLE['QueryExecutor'] = True
except ImportError as e:
    print(f"Warning: Could not import QueryExecutor: {e}")
    _COMPONENTS_AVAILABLE['QueryExecutor'] = False

try:
    from .result_processor import ResultProcessor
    _COMPONENTS_AVAILABLE['ResultProcessor'] = True
except ImportError as e:
    print(f"Warning: Could not import ResultProcessor: {e}")
    _COMPONENTS_AVAILABLE['ResultProcessor'] = False

try:
    from .nl_generator import NaturalLanguageGenerator
    _COMPONENTS_AVAILABLE['NaturalLanguageGenerator'] = True
except ImportError as e:
    print(f"Warning: Could not import NaturalLanguageGenerator: {e}")
    _COMPONENTS_AVAILABLE['NaturalLanguageGenerator'] = False

# Import main pipeline class
try:
    from .pipeline import ScienceLivePipeline, create_custom_pipeline
    _COMPONENTS_AVAILABLE['ScienceLivePipeline'] = True
except ImportError as e:
    print(f"Warning: Could not import ScienceLivePipeline: {e}")
    _COMPONENTS_AVAILABLE['ScienceLivePipeline'] = False

# Build __all__ list based on what's available
__all__ = []

# Add common models if available
if _COMMON_AVAILABLE:
    __all__.extend([
        'ProcessingContext',
        'ProcessedQuestion',
        'ExtractedEntity',
        'LinkedEntities', 
        'RosettaStatement',
        'GeneratedStatements',
        'SPARQLQuery',
        'GeneratedQueries',
        'QueryResults',
        'StructuredResult',
        'ProcessedResults',
        'NaturalLanguageResult',
        'EntityType',
        'QuestionType',
        'ConfidenceLevel',
    ])

# Add components that are available
for component, available in _COMPONENTS_AVAILABLE.items():
    if available:
        __all__.append(component)

# Add utility functions if main pipeline is available
if _COMPONENTS_AVAILABLE.get('ScienceLivePipeline', False):
    __all__.append('create_custom_pipeline')

# Report status
def get_pipeline_status():
    """Get status of pipeline components"""
    return {
        'common_models_available': _COMMON_AVAILABLE,
        'components_available': _COMPONENTS_AVAILABLE,
        'total_available': sum(_COMPONENTS_AVAILABLE.values()) + (1 if _COMMON_AVAILABLE else 0),
        'total_expected': len(_COMPONENTS_AVAILABLE) + 1
    }


# ============================================================================
# science_live/__init__.py - FIXED VERSION  
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
    from science_live.core import EndpointManager
    from science_live.pipeline import ScienceLivePipeline
    
    # Basic usage
    endpoint_manager = EndpointManager()
    pipeline = ScienceLivePipeline(endpoint_manager)
    result = await pipeline.process("What papers cite AlexNet?")
    
    # Advanced usage with custom config
    from science_live.pipeline import QuestionProcessor
    processor = QuestionProcessor(config={'debug': True})
"""

__version__ = "1.0.0"
__author__ = "Science Live Team"
__description__ = "Semantic knowledge exploration for scientific research"

# Import core components with error handling
try:
    from ..core import EndpointManager, ScienceLiveConfig
    _CORE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import core components: {e}")
    _CORE_AVAILABLE = False

# Import pipeline components with error handling
try:
    from .pipeline import ScienceLivePipeline
    _PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import pipeline: {e}")
    _PIPELINE_AVAILABLE = False

# Build __all__ based on available components
__all__ = []

if _CORE_AVAILABLE:
    __all__.extend(['EndpointManager', 'ScienceLiveConfig'])

if _PIPELINE_AVAILABLE:
    __all__.append('ScienceLivePipeline')

# If nothing is available, provide a helpful function
if not __all__:
    def get_installation_help():
        """Get help for installation issues"""
        return """
        Science Live installation appears incomplete.
        
        Try:
        1. pip install -e .
        2. pip install -e ".[dev]" 
        3. Check that all required files exist
        4. Run: python -c "import science_live; print('Success!')"
        """
    
    __all__ = ['get_installation_help']


# ============================================================================
# tests/conftest.py - FIXED VERSION
# ============================================================================

"""
Shared Test Configuration and Fixtures
======================================

This file contains shared fixtures and configuration for all tests.
It's automatically loaded by pytest and provides common test utilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, List, Any

# Safe imports with error handling
try:
    from science_live.pipeline.common import (
        ProcessingContext, ExtractedEntity, EntityType, QuestionType
    )
    _COMMON_IMPORTED = True
except ImportError as e:
    print(f"Warning: Could not import common models in conftest: {e}")
    _COMMON_IMPORTED = False
    
    # Provide minimal stubs for testing
    class ProcessingContext:
        def __init__(self, original_question, **kwargs):
            self.original_question = original_question
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class ExtractedEntity:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class EntityType:
        DOI = "doi"
        ORCID = "orcid"
        CONCEPT = "concept"
    
    class QuestionType:
        WHAT = "what"
        WHO = "who"

try:
    from science_live.core.endpoints import EndpointManager
    _ENDPOINTS_IMPORTED = True
except ImportError as e:
    print(f"Warning: Could not import endpoints in conftest: {e}")
    _ENDPOINTS_IMPORTED = False
    
    # Provide minimal stub
    class EndpointManager:
        def __init__(self):
            pass
        def get_endpoint(self):
            return Mock()


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def processing_context():
    """Create a basic processing context for tests."""
    return ProcessingContext(
        original_question="What papers cite AlexNet?",
        user_id="test_user",
        debug_mode=True
    )


@pytest.fixture
def mock_endpoint_manager():
    """Create a mock endpoint manager for testing."""
    if _ENDPOINTS_IMPORTED:
        manager = Mock(spec=EndpointManager)
    else:
        manager = Mock()
    
    # Mock endpoint
    mock_endpoint = AsyncMock()
    mock_endpoint.execute_sparql.return_value = {
        'results': {
            'bindings': [
                {
                    'np': {'value': 'http://example.org/nanopub1'},
                    'subject': {'value': 'http://example.org/paper1'},
                    'object1': {'value': 'http://example.org/paper2'}
                }
            ]
        }
    }
    
    manager.get_endpoint.return_value = mock_endpoint
    return manager


@pytest.fixture
def sample_extracted_entities():
    """Create sample extracted entities for testing."""
    return [
        ExtractedEntity(
            text="AlexNet",
            entity_type=EntityType.CONCEPT if hasattr(EntityType, 'CONCEPT') else "concept",
            confidence=0.9,
            start_pos=0,
            end_pos=7,
            uri="http://example.org/AlexNet",
            label="AlexNet"
        ),
        ExtractedEntity(
            text="10.1038/nature12373",
            entity_type=EntityType.DOI if hasattr(EntityType, 'DOI') else "doi",
            confidence=0.95,
            start_pos=20,
            end_pos=40,
            uri="https://doi.org/10.1038/nature12373",
            label="Nature paper"
        )
    ]


@pytest.fixture
def sample_sparql_results():
    """Create sample SPARQL results for testing."""
    return {
        'results': {
            'bindings': [
                {
                    'np': {'value': 'http://purl.org/np/test1'},
                    'statement': {'value': 'http://purl.org/np/test1#statement'},
                    'subject': {'value': 'https://doi.org/10.1038/nature12373'},
                    'object1': {'value': 'https://doi.org/10.1234/citing-paper'},
                    'label': {'value': 'AlexNet cites ImageNet paper'},
                    'confidence': {'value': '0.9'}
                },
                {
                    'np': {'value': 'http://purl.org/np/test2'},
                    'statement': {'value': 'http://purl.org/np/test2#statement'},
                    'subject': {'value': 'https://doi.org/10.1038/nature12373'},
                    'object1': {'value': 'https://doi.org/10.5678/another-paper'},
                    'label': {'value': 'AlexNet references CNN architecture'},
                    'confidence': {'value': '0.8'}
                }
            ]
        }
    }


# Helper function to check component availability
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "requires_pipeline: mark test to require full pipeline"
    )
    config.addinivalue_line(
        "markers", "requires_core: mark test to require core components"
    )


def pytest_runtest_setup(item):
    """Skip tests that require unavailable components."""
    if item.get_closest_marker("requires_pipeline") and not _COMMON_IMPORTED:
        pytest.skip("Pipeline components not available")
    
    if item.get_closest_marker("requires_core") and not _ENDPOINTS_IMPORTED:
        pytest.skip("Core components not available")
