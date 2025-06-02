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
    
        # Should indicate network connectivity issue, not just "no results"
        assert ("network" in result.summary.lower() or 
                "connectivity" in result.summary.lower() or
                "unable to search" in result.summary.lower())
    
        # Should have network-specific suggestions
        suggestions_text = " ".join(result.suggestions).lower()
        assert ("try again" in suggestions_text or 
                "connection" in suggestions_text or
                "temporarily unavailable" in suggestions_text)
    
        # Pipeline should complete all steps
        assert result.execution_summary['pipeline_steps_completed'] == 7
    
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


