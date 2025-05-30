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


