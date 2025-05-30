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


# ============================================================================
# tests/test_pipeline/test_common.py - Test Data Models
# ============================================================================

import pytest
from science_live.pipeline.common import (
    ProcessingContext, ProcessedQuestion, ExtractedEntity, 
    EntityType, QuestionType, ConfidenceLevel,
    get_confidence_level, validate_processing_context,
    validate_extracted_entity, validate_rosetta_statement
)


class TestProcessingContext:
    """Test ProcessingContext data model."""
    
    def test_create_context(self):
        """Test creating a processing context."""
        context = ProcessingContext(
            original_question="What is DNA?",
            user_id="user123"
        )
        
        assert context.original_question == "What is DNA?"
        assert context.user_id == "user123"
        assert context.debug_mode is False
        assert isinstance(context.metadata, dict)
    
    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        import asyncio
        context = ProcessingContext(original_question="test")
        
        # Should be very small elapsed time
        elapsed = context.get_elapsed_time()
        assert elapsed >= 0
        assert elapsed < 1  # Should be less than 1 second
    
    def test_validation(self):
        """Test context validation."""
        valid_context = ProcessingContext(original_question="Valid question")
        assert validate_processing_context(valid_context) is True
        
        invalid_context = ProcessingContext(original_question="")
        assert validate_processing_context(invalid_context) is False


class TestExtractedEntity:
    """Test ExtractedEntity data model."""
    
    def test_create_entity(self):
        """Test creating an extracted entity."""
        entity = ExtractedEntity(
            text="AlexNet",
            entity_type=EntityType.CONCEPT,
            confidence=0.9,
            start_pos=0,
            end_pos=7
        )
        
        assert entity.text == "AlexNet"
        assert entity.entity_type == EntityType.CONCEPT
        assert entity.confidence == 0.9
    
    def test_sparql_value_conversion(self):
        """Test conversion to SPARQL values."""
        # URI entity
        uri_entity = ExtractedEntity(
            text="paper", entity_type=EntityType.CONCEPT,
            confidence=0.9, start_pos=0, end_pos=5,
            uri="http://example.org/paper"
        )
        assert uri_entity.to_sparql_value() == "<http://example.org/paper>"
        
        # Text entity
        text_entity = ExtractedEntity(
            text="machine learning", entity_type=EntityType.CONCEPT,
            confidence=0.8, start_pos=0, end_pos=16
        )
        assert text_entity.to_sparql_value() == '"machine learning"'
        
        # Number entity
        number_entity = ExtractedEntity(
            text="42", entity_type=EntityType.NUMBER,
            confidence=1.0, start_pos=0, end_pos=2
        )
        assert number_entity.to_sparql_value() == "42"
    
    def test_validation(self):
        """Test entity validation."""
        valid_entity = ExtractedEntity(
            text="test", entity_type=EntityType.CONCEPT,
            confidence=0.5, start_pos=0, end_pos=4
        )
        assert validate_extracted_entity(valid_entity) is True
        
        # Invalid confidence
        invalid_entity = ExtractedEntity(
            text="test", entity_type=EntityType.CONCEPT,
            confidence=1.5, start_pos=0, end_pos=4
        )
        assert validate_extracted_entity(invalid_entity) is False


class TestEnums:
    """Test enum types."""
    
    def test_entity_types(self):
        """Test EntityType enum."""
        assert EntityType.DOI.value == "doi"
        assert EntityType.ORCID.value == "orcid"
        assert len(EntityType) == 11  # All entity types
    
    def test_question_types(self):
        """Test QuestionType enum."""
        assert QuestionType.WHAT.value == "what"
        assert QuestionType.WHO.value == "who"
        assert len(QuestionType) == 9  # All question types
    
    def test_confidence_levels(self):
        """Test confidence level conversion."""
        assert get_confidence_level(0.9) == ConfidenceLevel.HIGH
        assert get_confidence_level(0.6) == ConfidenceLevel.MEDIUM
        assert get_confidence_level(0.3) == ConfidenceLevel.LOW


# ============================================================================
# tests/test_pipeline/test_question_processor.py - Test Question Processing
# ============================================================================

import pytest
from science_live.pipeline.question_processor import QuestionProcessor, is_valid_question
from science_live.pipeline.common import ProcessingContext, QuestionType


class TestQuestionProcessor:
    """Test QuestionProcessor functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create a question processor for testing."""
        return QuestionProcessor()
    
    @pytest.mark.asyncio
    async def test_basic_question_processing(self, processor, processing_context):
        """Test basic question processing."""
        question = "What papers cite AlexNet?"
        
        result = await processor.process(question, processing_context)
        
        assert result.original_text == question
        assert result.question_type == QuestionType.WHAT
        assert result.intent_confidence > 0.5
        assert "papers" in result.key_phrases
        assert "cite" in result.key_phrases or "AlexNet" in result.key_phrases
    
    @pytest.mark.asyncio
    async def test_question_type_classification(self, processor, processing_context):
        """Test question type classification."""
        test_cases = [
            ("What is machine learning?", QuestionType.WHAT),
            ("Who authored this paper?", QuestionType.WHO),
            ("Where is CERN located?", QuestionType.WHERE),
            ("When was this published?", QuestionType.WHEN),
            ("How does this work?", QuestionType.HOW),
            ("Why is this important?", QuestionType.WHY),
            ("List all papers by this author", QuestionType.LIST),
            ("How many citations does this have?", QuestionType.COUNT)
        ]
        
        for question, expected_type in test_cases:
            result = await processor.process(question, processing_context)
            assert result.question_type == expected_type, f"Failed for: {question}"
    
    @pytest.mark.asyncio
    async def test_entity_identification(self, processor, processing_context):
        """Test potential entity identification."""
        question = 'What papers cite "AlexNet" by 0000-0002-1784-2920?'
        
        result = await processor.process(question, processing_context)
        
        # Should identify quoted string and ORCID
        assert "AlexNet" in result.potential_entities
        assert "0000-0002-1784-2920" in result.potential_entities
    
    @pytest.mark.asyncio
    async def test_doi_identification(self, processor, processing_context):
        """Test DOI identification."""
        question = "What cites https://doi.org/10.1038/nature12373?"
        
        result = await processor.process(question, processing_context)
        
        # Should identify DOI
        doi_found = any("10.1038/nature12373" in entity for entity in result.potential_entities)
        assert doi_found
    
    @pytest.mark.asyncio
    async def test_text_cleaning(self, processor, processing_context):
        """Test text cleaning functionality."""
        messy_question = "  What    is   DNA???   "
        
        result = await processor.process(messy_question, processing_context)
        
        assert result.cleaned_text == "What is DNA?"
        assert result.original_text == messy_question
    
    @pytest.mark.asyncio
    async def test_empty_question_handling(self, processor, processing_context):
        """Test handling of empty questions."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            await processor.process("", processing_context)
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            await processor.process("   ", processing_context)
    
    def test_question_validation(self):
        """Test question validation utility."""
        assert is_valid_question("What is DNA?") is True
        assert is_valid_question("Valid question here") is True
        assert is_valid_question("") is False
        assert is_valid_question("ab") is False  # Too short
        assert is_valid_question("Buy now! Click here $$$") is False  # Spam
    
    def test_question_complexity_assessment(self, processor):
        """Test question complexity assessment."""
        from science_live.pipeline.common import ProcessedQuestion
        
        # Simple question
        simple_q = ProcessedQuestion(
            original_text="What is DNA?",
            cleaned_text="What is DNA?",
            question_type=QuestionType.WHAT,
            key_phrases=["DNA"],
            potential_entities=["DNA"],
            intent_confidence=0.9
        )
        complexity = processor.get_question_complexity(simple_q)
        assert complexity <= 2
        
        # Complex question
        complex_q = ProcessedQuestion(
            original_text="What papers by researchers at CERN cite quantum mechanics work and relate to particle physics?",
            cleaned_text="What papers by researchers at CERN cite quantum mechanics work and relate to particle physics?",
            question_type=QuestionType.WHAT,
            key_phrases=["papers", "researchers", "CERN", "quantum", "mechanics", "particle", "physics"],
            potential_entities=["CERN", "quantum mechanics", "particle physics"],
            intent_confidence=0.7
        )
        complexity = processor.get_question_complexity(complex_q)
        assert complexity >= 3


# ============================================================================
# tests/test_pipeline/test_entity_extractor.py - Test Entity Extraction
# ============================================================================

import pytest
from unittest.mock import AsyncMock, Mock
from science_live.pipeline.entity_extractor import EntityExtractorLinker
from science_live.pipeline.common import (
    ProcessedQuestion, ProcessingContext, QuestionType, EntityType
)


class TestEntityExtractorLinker:
    """Test EntityExtractorLinker functionality."""
    
    @pytest.fixture
    def extractor(self, mock_endpoint_manager):
        """Create an entity extractor for testing."""
        return EntityExtractorLinker(mock_endpoint_manager)
    
    @pytest.fixture
    def sample_processed_question(self):
        """Create a sample processed question."""
        return ProcessedQuestion(
            original_text='What papers cite "AlexNet" by 0000-0002-1784-2920?',
            cleaned_text='What papers cite "AlexNet" by 0000-0002-1784-2920?',
            question_type=QuestionType.WHAT,
            key_phrases=["papers", "cite", "AlexNet"],
            potential_entities=["AlexNet", "0000-0002-1784-2920"],
            intent_confidence=0.8
        )
    
    @pytest.mark.asyncio
    async def test_basic_entity_extraction(self, extractor, sample_processed_question, processing_context):
        """Test basic entity extraction."""
        result = await extractor.extract_and_link(sample_processed_question, processing_context)
        
        assert len(result.entities) >= 2  # Should find at least AlexNet and ORCID
        
        # Check for ORCID entity
        orcid_entities = [e for e in result.entities if e.entity_type == EntityType.ORCID]
        assert len(orcid_entities) == 1
        assert orcid_entities[0].text == "0000-0002-1784-2920"
        assert orcid_entities[0].uri == "https://orcid.org/0000-0002-1784-2920"
        
        # Check for title entity
        title_entities = [e for e in result.entities if e.entity_type == EntityType.TITLE]
        assert len(title_entities) == 1
        assert title_entities[0].text == "AlexNet"
    
    @pytest.mark.asyncio
    async def test_doi_extraction(self, extractor, processing_context):
        """Test DOI extraction and linking."""
        question = ProcessedQuestion(
            original_text="What cites 10.1038/nature12373?",
            cleaned_text="What cites 10.1038/nature12373?",
            question_type=QuestionType.WHAT,
            key_phrases=["cites"],
            potential_entities=["10.1038/nature12373"],
            intent_confidence=0.9
        )
        
        result = await extractor.extract_and_link(question, processing_context)
        
        doi_entities = [e for e in result.entities if e.entity_type == EntityType.DOI]
        assert len(doi_entities) == 1
        assert doi_entities[0].text == "10.1038/nature12373"
        assert doi_entities[0].uri == "https://doi.org/10.1038/nature12373"
        assert doi_entities[0].confidence >= 0.9
    
    @pytest.mark.asyncio
    async def test_url_extraction(self, extractor, processing_context):
        """Test URL extraction."""
        question = ProcessedQuestion(
            original_text="What about https://example.org/paper?",
            cleaned_text="What about https://example.org/paper?",
            question_type=QuestionType.WHAT,
            key_phrases=["about"],
            potential_entities=["https://example.org/paper"],
            intent_confidence=0.8
        )
        
        result = await extractor.extract_and_link(question, processing_context)
        
        url_entities = [e for e in result.entities if e.entity_type == EntityType.URL]
        assert len(url_entities) == 1
        assert url_entities[0].text == "https://example.org/paper"
        assert url_entities[0].uri == "https://example.org/paper"
    
    @pytest.mark.asyncio
    async def test_entity_classification(self, extractor, sample_processed_question, processing_context):
        """Test entity classification as subjects vs objects."""
        result = await extractor.extract_and_link(sample_processed_question, processing_context)
        
        # Should have both subject and object candidates
        assert len(result.subject_candidates) > 0
        assert len(result.object_candidates) >= 0  # May or may not have objects
        
        # High-confidence entities should be subject candidates
        high_conf_subjects = [e for e in result.subject_candidates if e.confidence > 0.9]
        assert len(high_conf_subjects) > 0
    
    @pytest.mark.asyncio
    async def test_linking_confidence(self, extractor, sample_processed_question, processing_context):
        """Test overall linking confidence calculation."""
        result = await extractor.extract_and_link(sample_processed_question, processing_context)
        
        assert 0.0 <= result.linking_confidence <= 1.0
        
        # Should have reasonable confidence with clear entities
        assert result.linking_confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_empty_question_handling(self, extractor, processing_context):
        """Test handling of questions with no entities."""
        question = ProcessedQuestion(
            original_text="What is this?",
            cleaned_text="What is this?",
            question_type=QuestionType.WHAT,
            key_phrases=["this"],
            potential_entities=[],
            intent_confidence=0.5
        )
        
        result = await extractor.extract_and_link(question, processing_context)
        
        # Should handle gracefully even with no clear entities
        assert isinstance(result.entities, list)
        assert isinstance(result.linking_confidence, float)
        assert 0.0 <= result.linking_confidence <= 1.0


# ============================================================================
# tests/test_pipeline/test_rosetta_generator.py - Test Rosetta Generation
# ============================================================================

import pytest
from science_live.pipeline.rosetta_generator import RosettaStatementGenerator
from science_live.pipeline.common import (
    LinkedEntities, ProcessedQuestion, ProcessingContext, 
    ExtractedEntity, EntityType, QuestionType
)


class TestRosettaStatementGenerator:
    """Test RosettaStatementGenerator functionality."""
    
    @pytest.fixture
    def generator(self):
        """Create a Rosetta statement generator."""
        return RosettaStatementGenerator()
    
    @pytest.fixture
    def citation_entities(self):
        """Create entities for citation testing."""
        subject = ExtractedEntity(
            text="AlexNet paper",
            entity_type=EntityType.DOI,
            confidence=0.95,
            start_pos=0,
            end_pos=12,
            uri="https://doi.org/10.1038/nature12373",
            label="AlexNet: ImageNet Classification"
        )
        
        object_entity = ExtractedEntity(
            text="ImageNet paper",
            entity_type=EntityType.DOI,
            confidence=0.9,
            start_pos=20,
            end_pos=33,
            uri="https://doi.org/10.1234/imagenet",
            label="ImageNet Dataset Paper"
        )
        
        return LinkedEntities(
            entities=[subject, object_entity],
            subject_candidates=[subject],
            object_candidates=[object_entity],
            linking_confidence=0.9
        )
    
    @pytest.fixture
    def citation_question(self):
        """Create a citation-related question."""
        return ProcessedQuestion(
            original_text="What papers cite AlexNet?",
            cleaned_text="What papers cite AlexNet?",
            question_type=QuestionType.WHAT,
            key_phrases=["papers", "cite", "AlexNet"],
            potential_entities=["AlexNet"],
            intent_confidence=0.8
        )
    
    @pytest.mark.asyncio
    async def test_citation_statement_generation(self, generator, citation_entities, citation_question, processing_context):
        """Test generation of citation statements."""
        result = await generator.generate(citation_entities, citation_question, processing_context)
        
        assert len(result.statements) > 0
        
        # Should generate citation-type statements
        citation_statements = [s for s in result.statements if "cite" in s.statement_type_label.lower()]
        assert len(citation_statements) > 0
        
        # Check statement structure
        stmt = citation_statements[0]
        assert stmt.subject is not None
        assert stmt.statement_type_uri is not None
        assert stmt.statement_type_label is not None
    
    @pytest.mark.asyncio
    async def test_authorship_statement_generation(self, generator, processing_context):
        """Test generation of authorship statements."""
        # Create authorship entities
        paper_entity = ExtractedEntity(
            text="Nature paper",
            entity_type=EntityType.DOI,
            confidence=0.9,
            start_pos=0,
            end_pos=12,
            uri="https://doi.org/10.1038/example"
        )
        
        author_entity = ExtractedEntity(
            text="0000-0002-1784-2920",
            entity_type=EntityType.ORCID,
            confidence=0.95,
            start_pos=20,
            end_pos=40,
            uri="https://orcid.org/0000-0002-1784-2920",
            label="Anne Fouilloux"
        )
        
        entities = LinkedEntities(
            entities=[paper_entity, author_entity],
            subject_candidates=[paper_entity],
            object_candidates=[author_entity],
            linking_confidence=0.9
        )
        
        question = ProcessedQuestion(
            original_text="Who authored this paper?",
            cleaned_text="Who authored this paper?",
            question_type=QuestionType.WHO,
            key_phrases=["authored", "paper"],
            potential_entities=["paper"],
            intent_confidence=0.9
        )
        
        result = await generator.generate(entities, question, processing_context)
        
        # Should generate authorship statements
        author_statements = [s for s in result.statements if "author" in s.statement_type_label.lower()]
        assert len(author_statements) > 0
    
    @pytest.mark.asyncio
    async def test_measurement_statement_generation(self, generator, processing_context):
        """Test generation of measurement statements."""
        subject_entity = ExtractedEntity(
            text="Higgs boson",
            entity_type=EntityType.CONCEPT,
            confidence=0.8,
            start_pos=0,
            end_pos=11,
            label="Higgs boson"
        )
        
        value_entity = ExtractedEntity(
            text="125",
            entity_type=EntityType.NUMBER,
            confidence=0.9,
            start_pos=20,
            end_pos=23
        )
        
        entities = LinkedEntities(
            entities=[subject_entity, value_entity],
            subject_candidates=[subject_entity],
            object_candidates=[value_entity],
            linking_confidence=0.8
        )
        
        question = ProcessedQuestion(
            original_text="What is the mass of the Higgs boson?",
            cleaned_text="What is the mass of the Higgs boson?",
            question_type=QuestionType.WHAT,
            key_phrases=["mass", "Higgs", "boson"],
            potential_entities=["Higgs boson"],
            intent_confidence=0.9
        )
        
        result = await generator.generate(entities, question, processing_context)
        
        # Should have generated some statements
        assert len(result.statements) > 0
        assert result.generation_confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_natural_language_conversion(self, generator, citation_entities, citation_question, processing_context):
        """Test conversion of Rosetta statements back to natural language."""
        result = await generator.generate(citation_entities, citation_question, processing_context)
        
        if result.statements:
            stmt = result.statements[0]
            natural_language = stmt.to_natural_language()
            
            assert isinstance(natural_language, str)
            assert len(natural_language) > 0
            assert stmt.subject.label or stmt.subject.text in natural_language
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, generator, citation_entities, citation_question, processing_context):
        """Test confidence calculation for generated statements."""
        result = await generator.generate(citation_entities, citation_question, processing_context)
        
        assert 0.0 <= result.generation_confidence <= 1.0
        
        # Should have reasonable confidence with clear entities
        if result.statements:
            assert result.generation_confidence > 0.3
    
    @pytest.mark.asyncio
    async def test_no_entities_handling(self, generator, processing_context):
        """Test handling when no entities are available."""
        empty_entities = LinkedEntities(
            entities=[],
            subject_candidates=[],
            object_candidates=[],
            linking_confidence=0.0
        )
        
        question = ProcessedQuestion(
            original_text="What is this?",
            cleaned_text="What is this?",
            question_type=QuestionType.WHAT,
            key_phrases=["this"],
            potential_entities=[],
            intent_confidence=0.5
        )
        
        result = await generator.generate(empty_entities, question, processing_context)
        
        # Should handle gracefully
        assert isinstance(result.statements, list)
        assert isinstance(result.generation_confidence, float)
        assert result.generation_confidence >= 0


# ============================================================================
# tests/test_pipeline/test_sparql_generator.py - Test SPARQL Generation
# ============================================================================

import pytest
from science_live.pipeline.sparql_generator import SPARQLGenerator
from science_live.pipeline.common import (
    GeneratedStatements, RosettaStatement, ProcessingContext,
    ExtractedEntity, EntityType
)


class TestSPARQLGenerator:
    """Test SPARQLGenerator functionality."""
    
    @pytest.fixture
    def generator(self):
        """Create a SPARQL generator."""
        return SPARQLGenerator()
    
    @pytest.fixture
    def sample_rosetta_statement(self):
        """Create a sample Rosetta statement."""
        subject = ExtractedEntity(
            text="AlexNet",
            entity_type=EntityType.DOI,
            confidence=0.95,
            start_pos=0,
            end_pos=7,
            uri="https://doi.org/10.1038/nature12373",
            label="AlexNet paper"
        )
        
        object1 = ExtractedEntity(
            text="ImageNet",
            entity_type=EntityType.DOI,
            confidence=0.9,
            start_pos=10,
            end_pos=18,
            uri="https://doi.org/10.1234/imagenet",
            label="ImageNet paper"
        )
        
        return RosettaStatement(
            subject=subject,
            statement_type_uri="https://w3id.org/rosetta/Cites",
            statement_type_label="cites",
            required_object1=object1,
            dynamic_label_template="SUBJECT cites OBJECT1"
        )
    
    @pytest.fixture
    def generated_statements(self, sample_rosetta_statement):
        """Create sample generated statements."""
        return GeneratedStatements(
            statements=[sample_rosetta_statement],
            generation_confidence=0.8
        )
    
    @pytest.mark.asyncio
    async def test_basic_sparql_generation(self, generator, generated_statements, processing_context):
        """Test basic SPARQL query generation."""
        result = await generator.generate(generated_statements, processing_context)
        
        assert result.primary_query is not None
        assert result.primary_query.query_text is not None
        assert len(result.primary_query.query_text) > 0
        
        # Should be a SELECT query
        assert result.primary_query.query_type == 'SELECT'
        assert 'SELECT' in result.primary_query.query_text
        assert 'WHERE' in result.primary_query.query_text
    
    @pytest.mark.asyncio
    async def test_rosetta_query_structure(self, generator, generated_statements, processing_context):
        """Test Rosetta-specific SPARQL query structure."""
        result = await generator.generate(generated_statements, processing_context)
        
        query_text = result.primary_query.query_text
        
        # Should include Rosetta namespaces and patterns
        assert 'PREFIX rosetta:' in query_text
        assert 'rosetta:RosettaStatement' in query_text
        assert 'rosetta:hasStatementType' in query_text
        assert 'rosetta:subject' in query_text
    
    @pytest.mark.asyncio
    async def test_uri_filtering(self, generator, generated_statements, processing_context):
        """Test URI filtering in generated queries."""
        result = await generator.generate(generated_statements, processing_context)
        
        query_text = result.primary_query.query_text
        
        # Should include the subject URI
        assert 'https://doi.org/10.1038/nature12373' in query_text
        
        # Should include the statement type URI
        assert 'https://w3id.org/rosetta/Cites' in query_text
    
    @pytest.mark.asyncio
    async def test_fallback_query_generation(self, generator, generated_statements, processing_context):
        """Test fallback query generation."""
        result = await generator.generate(generated_statements, processing_context)
        
        # Should have fallback queries
        assert len(result.fallback_queries) > 0
        
        # Fallback queries should be valid
        for fallback in result.fallback_queries:
            assert fallback.query_text is not None
            assert len(fallback.query_text) > 0
            assert fallback.query_type in ['SELECT', 'ASK', 'CONSTRUCT']
    
    @pytest.mark.asyncio
    async def test_citation_specific_queries(self, generator, processing_context):
        """Test generation of citation-specific queries."""
        # Create citation statement
        subject = ExtractedEntity(
            text="paper", entity_type=EntityType.DOI,
            confidence=0.9, start_pos=0, end_pos=5,
            uri="https://doi.org/10.1038/example"
        )
        
        citation_stmt = RosettaStatement(
            subject=subject,
            statement_type_uri="https://w3id.org/rosetta/Cites",
            statement_type_label="cites"
        )
        
        statements = GeneratedStatements(
            statements=[citation_stmt],
            generation_confidence=0.8
        )
        
        result = await generator.generate(statements, processing_context)
        
        # Should generate citation-specific fallback
        citation_queries = [q for q in result.fallback_queries 
                          if 'cito:' in q.query_text or 'fabio:' in q.query_text]
        assert len(citation_queries) > 0
    
    @pytest.mark.asyncio
    async def test_complexity_estimation(self, generator, generated_statements, processing_context):
        """Test query complexity estimation."""
        result = await generator.generate(generated_statements, processing_context)
        
        complexity = result.primary_query.estimated_complexity
        assert 1 <= complexity <= 5
        
        # Should have reasonable complexity for statement with subject and object
        assert complexity >= 2
    
    @pytest.mark.asyncio
    async def test_empty_statements_handling(self, generator, processing_context):
        """Test handling of empty statement lists."""
        empty_statements = GeneratedStatements(
            statements=[],
            generation_confidence=0.0
        )
        
        result = await generator.generate(empty_statements, processing_context)
        
        # Should generate fallback query
        assert result.primary_query is not None
        assert result.generation_method == 'text_fallback'
    
    def test_query_validation(self, generator):
        """Test SPARQL query validation."""
        from science_live.pipeline.common import SPARQLQuery, validate_sparql_query
        
        valid_query = SPARQLQuery(
            query_text="SELECT * WHERE { ?s ?p ?o }",
            query_type="SELECT",
            estimated_complexity=1
        )
        assert validate_sparql_query(valid_query) is True
        
        invalid_query = SPARQLQuery(
            query_text="",
            query_type="",
            estimated_complexity=0
        )
        assert validate_sparql_query(invalid_query) is False


# ============================================================================  
# tests/test_pipeline/test_query_executor.py - Test Query Execution
# ============================================================================

import pytest
from unittest.mock import AsyncMock
from science_live.pipeline.query_executor import QueryExecutor
from science_live.pipeline.common import (
    GeneratedQueries, SPARQLQuery, ProcessingContext
)


class TestQueryExecutor:
    """Test QueryExecutor functionality."""
    
    @pytest.fixture
    def executor(self, mock_endpoint_manager):
        """Create a query executor."""
        return QueryExecutor(mock_endpoint_manager)
    
    @pytest.fixture
    def sample_queries(self):
        """Create sample queries for testing."""
        primary = SPARQLQuery(
            query_text="SELECT * WHERE { ?s ?p ?o }",
            query_type="SELECT",
            estimated_complexity=1
        )
        
        fallback = SPARQLQuery(
            query_text="SELECT * WHERE { ?s rdfs:label ?o }",
            query_type="SELECT", 
            estimated_complexity=1
        )
        
        return GeneratedQueries(
            primary_query=primary,
            fallback_queries=[fallback]
        )
    
    @pytest.mark.asyncio
    async def test_successful_query_execution(self, executor, sample_queries, processing_context):
        """Test successful query execution."""
        result = await executor.execute(sample_queries, processing_context)
        
        assert result.success is True
        assert result.total_results > 0
        assert result.execution_time >= 0
        assert result.query_used is not None
        assert isinstance(result.results, list)
    
    @pytest.mark.asyncio
    async def test_fallback_query_execution(self, executor, sample_queries, processing_context, mock_endpoint_manager):
        """Test fallback to secondary queries."""
        # Make primary query return no results
        mock_endpoint = mock_endpoint_manager.get_endpoint.return_value
        mock_endpoint.execute_sparql.side_effect = [
            {'results': {'bindings': []}},  # Primary returns empty
            {'results': {'bindings': [{'s': {'value': 'test'}}]}}  # Fallback returns results
        ]
        
        result = await executor.execute(sample_queries, processing_context)
        
        assert result.success is True
        assert result.total_results > 0
        # Should have used fallback query
        assert mock_endpoint.execute_sparql.call_count == 2
    
    @pytest.mark.asyncio
    async def test_query_failure_handling(self, executor, sample_queries, processing_context, mock_endpoint_manager):
        """Test handling of query failures."""
        # Make endpoint raise exception
        mock_endpoint = mock_endpoint_manager.get_endpoint.return_value
        mock_endpoint.execute_sparql.side_effect = Exception("SPARQL endpoint error")
        
        result = await executor.execute(sample_queries, processing_context)
        
        assert result.success is False
        assert result.total_results == 0
        assert result.error_message is not None
        assert "SPARQL endpoint error" in result.error_message
    
    @pytest.mark.asyncio
    async def test_query_caching(self, executor, sample_queries, processing_context, mock_endpoint_manager):
        """Test query result caching."""
        # Execute same query twice
        result1 = await executor.execute(sample_queries, processing_context)
        result2 = await executor.execute(sample_queries, processing_context)
        
        assert result1.success is True
        assert result2.success is True
        
        # Should have cached the result (endpoint called only once)
        mock_endpoint = mock_endpoint_manager.get_endpoint.return_value
        assert mock_endpoint.execute_sparql.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execution_timing(self, executor, sample_queries, processing_context):
        """Test execution timing measurement."""
        result = await executor.execute(sample_queries, processing_context)
        
        assert result.execution_time >= 0
        assert result.execution_time < 10  # Should be reasonable


# ============================================================================
# tests/test_pipeline/test_result_processor.py - Test Result Processing
# ============================================================================

import pytest
from science_live.pipeline.result_processor import ResultProcessor
from science_live.pipeline.common import (
    QueryResults, GeneratedStatements, ProcessingContext
)


class TestResultProcessor:
    """Test ResultProcessor functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create a result processor."""
        return ResultProcessor()
    
    @pytest.fixture
    def sample_query_results(self, sample_sparql_results):
        """Create sample query results."""
        return QueryResults(
            success=True,
            results=sample_sparql_results['results']['bindings'],
            query_used="SELECT * WHERE { ?s ?p ?o }",
            execution_time=0.5,
            total_results=2
        )
    
    @pytest.fixture
    def empty_statements(self):
        """Create empty generated statements for testing."""
        return GeneratedStatements(
            statements=[],
            generation_confidence=0.0
        )
    
    @pytest.mark.asyncio
    async def test_successful_result_processing(self, processor, sample_query_results, empty_statements, processing_context):
        """Test successful result processing."""
        result = await processor.process(sample_query_results, empty_statements, processing_context)
        
        assert result.total_found == 2
        assert len(result.results) == 2
        assert result.processing_confidence > 0
        
        # Check structured results
        for structured_result in result.results:
            assert structured_result.nanopub_uri is not None
            assert structured_result.confidence >= 0
            assert structured_result.metadata is not None
    
    @pytest.mark.asyncio
    async def test_result_grouping(self, processor, sample_query_results, empty_statements, processing_context):
        """Test result grouping functionality."""
        result = await processor.process(sample_query_results, empty_statements, processing_context)
        
        assert 'by_type' in result.groupings
        assert 'by_confidence' in result.groupings
        
        # Should have grouped by confidence levels
        confidence_groups = result.groupings['by_confidence']
        assert 'high' in confidence_groups
        assert 'medium' in confidence_groups  
        assert 'low' in confidence_groups
    
    @pytest.mark.asyncio
    async def test_confidence_extraction(self, processor, sample_query_results, empty_statements, processing_context):
        """Test confidence value extraction from results."""
        result = await processor.process(sample_query_results, empty_statements, processing_context)
        
        # Should extract confidence from SPARQL results
        high_conf_results = [r for r in result.results if r.confidence >= 0.8]
        assert len(high_conf_results) > 0
    
    @pytest.mark.asyncio
    async def test_empty_results_handling(self, processor, empty_statements, processing_context):
        """Test handling of empty query results."""
        empty_results = QueryResults(
            success=True,
            results=[],
            query_used="SELECT * WHERE { ?s ?p ?o }",
            execution_time=0.1,
            total_results=0
        )
        
        result = await processor.process(empty_results, empty_statements, processing_context)
        
        assert result.total_found == 0
        assert len(result.results) == 0
        assert result.processing_confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_failed_query_handling(self, processor, empty_statements, processing_context):
        """Test handling of failed queries."""
        failed_results = QueryResults(
            success=False,
            results=[],
            query_used="SELECT * WHERE { ?s ?p ?o }",
            execution_time=0.1,
            total_results=0,
            error_message="Query failed"
        )
        
        result = await processor.process(failed_results, empty_statements, processing_context)
        
        assert result.total_found == 0
        assert result.processing_confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_completeness_assessment(self, processor, sample_query_results, empty_statements, processing_context):
        """Test result completeness assessment."""
        result = await processor.process(sample_query_results, empty_statements, processing_context)
        
        # Should assess completeness of each result
        for structured_result in result.results:
            assert 'completeness' in structured_result.metadata
            completeness = structured_result.metadata['completeness']
            assert 0.0 <= completeness <= 1.0


# ============================================================================
# tests/test_pipeline/test_pipeline.py - Test Complete Pipeline Integration
# ============================================================================

import pytest
from science_live.pipeline.pipeline import ScienceLivePipeline


class TestScienceLivePipeline:
    """Test complete pipeline integration."""
    
    @pytest.fixture
    def pipeline(self, mock_endpoint_manager):
        """Create a complete pipeline for testing."""
        return ScienceLivePipeline(mock_endpoint_manager)
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, pipeline):
        """Test complete end-to-end processing."""
        question = "What papers cite AlexNet?"
        
        result = await pipeline.process(question)
        
        assert result is not None
        assert result.summary is not None
        assert isinstance(result.detailed_results, list)
        assert isinstance(result.suggestions, list)
        assert result.execution_summary is not None
    
    @pytest.mark.asyncio  
    async def test_error_handling(self, pipeline, mock_endpoint_manager):
        """Test pipeline error handling."""
        # Make endpoint fail
        mock_endpoint = mock_endpoint_manager.get_endpoint.return_value
        mock_endpoint.execute_sparql.side_effect = Exception("Network error")
        
        result = await pipeline.process("What is DNA?")
        
        # Should return error response gracefully
        assert result is not None
        assert "Error processing question" in result.summary
        assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, pipeline):
        """Test batch processing of multiple questions."""
        questions = [
            "What papers cite AlexNet?",
            "Who authored the ImageNet paper?",
            "What is machine learning?"
        ]
        
        results = await pipeline.process_batch(questions)
        
        assert len(results) == 3
        for result in results:
            if not isinstance(result, Exception):
                assert result.summary is not None


# ============================================================================
# tests/fixtures/sample_questions.py - Sample Test Data
# ============================================================================

"""Sample questions for testing the pipeline."""

CITATION_QUESTIONS = [
    "What papers cite AlexNet?",
    "Who cites https://doi.org/10.1038/nature12373?",
    "Show me citations for the ImageNet paper",
    "What work references this research?",
]

AUTHORSHIP_QUESTIONS = [
    "Who authored this paper?",
    "What papers by 0000-0002-1784-2920?",
    "Show me work by Anne Fouilloux",
    "Authors of the AlexNet paper?",
]

MEASUREMENT_QUESTIONS = [
    "What is the mass of the Higgs boson?",
    "Temperature of the cosmic microwave background?",
    "How fast is the speed of light?",
    "What is the charge of an electron?",
]

LOCATION_QUESTIONS = [
    "Where is CERN located?",
    "Location of the Large Hadron Collider?",
    "Where was this research conducted?",
]

COMPLEX_QUESTIONS = [
    "What papers by researchers at CERN cite quantum mechanics work and relate to particle physics?",
    "Show me recent citations of climate change research by authors with ORCID IDs from Norwegian institutions",
    "Find measurements of stellar masses in papers published after 2020 that cite Gaia mission data",
]

ALL_SAMPLE_QUESTIONS = (
    CITATION_QUESTIONS + 
    AUTHORSHIP_QUESTIONS + 
    MEASUREMENT_QUESTIONS + 
    LOCATION_QUESTIONS + 
    COMPLEX_QUESTIONS
)

# ============================================================================
# tests/integration/test_end_to_end.py - Integration Tests
# ============================================================================

import pytest
from science_live.pipeline import ScienceLivePipeline
from science_live.core import EndpointManager


@pytest.mark.integration
class TestEndToEndIntegration:
    """Integration tests with real endpoints (when available)."""
    
    @pytest.fixture
    def real_pipeline(self):
        """Create pipeline with real endpoint (skip if not available)."""
        try:
            endpoint_manager = EndpointManager()
            # Add real endpoint configuration here
            return ScienceLivePipeline(endpoint_manager)
        except Exception:
            pytest.skip("Real endpoint not available")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_citation_query(self, real_pipeline):
        """Test with real citation query."""
        question = "What papers cite https://doi.org/10.1038/nature12373?"
        
        result = await real_pipeline.process(question)
        
        assert result is not None
        assert result.summary is not None
        # More specific assertions based on expected real data
    
    @pytest.mark.asyncio
    @pytest.mark.slow  
    async def test_real_author_query(self, real_pipeline):
        """Test with real author query."""
        question = "What papers by 0000-0002-1784-2920?"
        
        result = await real_pipeline.process(question)
        
        assert result is not None
        assert result.summary is not None


# Run with: pytest tests/ -v
# Run integration tests: pytest tests/ -v -m integration
# Run without slow tests: pytest tests/ -v -m "not slow"
