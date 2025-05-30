"""
Science Live: Complete Test Suite
=================================

Comprehensive test suite for all 8 pipeline components with fixtures,
mocks, and integration tests.

Test Structure:
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and configuration
├── test_pipeline/
│   ├── __init__.py
│   ├── test_common.py             # Test data models and utilities
│   ├── test_question_processor.py # Test question processing
│   ├── test_entity_extractor.py   # Test entity extraction & linking
│   ├── test_rosetta_generator.py  # Test Rosetta statement generation
│   ├── test_sparql_generator.py   # Test SPARQL generation
│   ├── test_query_executor.py     # Test query execution
│   ├── test_result_processor.py   # Test result processing
│   ├── test_nl_generator.py       # Test natural language generation
│   └── test_pipeline.py           # Test complete pipeline integration
├── test_core/
│   ├── __init__.py
│   ├── test_endpoints.py          # Test endpoint management
│   └── test_config.py             # Test configuration system
├── fixtures/
│   ├── __init__.py
│   ├── sample_questions.py        # Sample questions for testing
│   ├── sample_entities.py         # Sample entities and URIs
│   ├── sample_sparql_results.py   # Sample SPARQL responses
│   └── sample_nanopubs.py         # Sample nanopublication data
└── integration/
    ├── __init__.py
    ├── test_end_to_end.py         # Full end-to-end tests
    └── test_performance.py        # Performance and load tests
"""

# ============================================================================
# tests/conftest.py - Shared Test Configuration and Fixtures
# ============================================================================

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, List, Any

from science_live.pipeline.common import (
    ProcessingContext, ExtractedEntity, EntityType, QuestionType
)
from science_live.core.endpoints import EndpointManager


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
    manager = Mock(spec=EndpointManager)
    
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
            entity_type=EntityType.CONCEPT,
            confidence=0.9,
            start_pos=0,
            end_pos=7,
            uri="http://example.org/AlexNet",
            label="AlexNet"
        ),
        ExtractedEntity(
            text="10.1038/nature12373",
            entity_type=EntityType.DOI,
            confidence=0.95,
            start_pos=20,
            end_pos=40,
            uri="https://doi.org/10.1038/nature12373",
            label="Nature paper"
        ),
        ExtractedEntity(
            text="0000-0002-1784-2920",
            entity_type=EntityType.ORCID,
            confidence=0.95,
            start_pos=50,
            end_pos=70,
            uri="https://orcid.org/0000-0002-1784-2920",
            label="Anne Fouilloux"
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

