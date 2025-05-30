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

