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

