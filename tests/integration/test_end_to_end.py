# ============================================================================
# tests/integration/test_end_to_end.py
# ============================================================================

"""
End-to-End Integration Tests
===========================

Tests that exercise the complete pipeline from natural language
input to final results.
"""

import pytest
from science_live.pipeline import ScienceLivePipeline
from science_live.core import EndpointManager, ConfigLoader
from science_live.core.endpoints import TestNanopubEndpoint
from tests.fixtures.sample_questions import ALL_SAMPLE_QUESTIONS


@pytest.mark.integration
class TestEndToEndPipeline:
    """Complete end-to-end pipeline tests"""
    
    @pytest.fixture
    def pipeline(self):
        """Create a pipeline with test endpoint"""
        endpoint_manager = EndpointManager()
        test_endpoint = TestNanopubEndpoint()
        endpoint_manager.register_endpoint('test', test_endpoint, is_default=True)
        
        return ScienceLivePipeline(endpoint_manager)
    
    @pytest.mark.asyncio
    async def test_citation_question_flow(self, pipeline):
        """Test complete flow for citation questions"""
        question = "What papers cite AlexNet?"
        
        result = await pipeline.process(question)
        
        # Verify result structure
        assert result is not None
        assert result.summary is not None
        assert isinstance(result.detailed_results, list)
        assert isinstance(result.suggestions, list)
        assert result.execution_summary is not None
        
        # Verify content makes sense
        assert len(result.summary) > 0
        assert result.execution_summary['total_execution_time'] > 0
    
    @pytest.mark.asyncio
    async def test_authorship_question_flow(self, pipeline):
        """Test complete flow for authorship questions"""
        question = "Who authored the ImageNet paper?"
        
        result = await pipeline.process(question)
        
        assert result is not None
        assert result.summary is not None
        assert result.execution_summary['pipeline_steps_completed'] == 7
    
    @pytest.mark.asyncio
    async def test_measurement_question_flow(self, pipeline):
        """Test complete flow for measurement questions"""
        question = "What is the mass of the Higgs boson?"
        
        result = await pipeline.process(question)
        
        assert result is not None
        assert result.summary is not None
    
    @pytest.mark.asyncio
    async def test_complex_question_flow(self, pipeline):
        """Test complete flow for complex questions"""
        question = "What papers by researchers at CERN cite quantum mechanics work?"
        
        result = await pipeline.process(question)
        
        assert result is not None
        assert result.summary is not None
        # Complex questions might have lower confidence
        assert isinstance(result.confidence_explanation, str)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_processing(self, pipeline):
        """Test batch processing of multiple questions"""
        questions = [
            "What papers cite AlexNet?",
            "Who authored this paper?",
            "Where is CERN located?"
        ]
        
        results = await pipeline.process_batch(questions)
        
        assert len(results) == 3
        for result in results:
            if not isinstance(result, Exception):
                assert result.summary is not None
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, pipeline):
        """Test error recovery in pipeline"""
        # Test with problematic input
        problematic_questions = [
            "",  # Empty question
            "?",  # Just punctuation
            "asdfghjkl",  # Random text
        ]
        
        for question in problematic_questions:
            result = await pipeline.process(question)
            # Should return error response, not crash
            assert result is not None
            assert isinstance(result.summary, str)
    
    @pytest.mark.asyncio
    async def test_pipeline_with_config(self):
        """Test pipeline with custom configuration"""
        config = ConfigLoader.create_default_config()
        config.app_name = "Test Pipeline"
        
        endpoint_manager = EndpointManager()
        test_endpoint = TestNanopubEndpoint()
        endpoint_manager.register_endpoint('test', test_endpoint, is_default=True)
        
        pipeline = ScienceLivePipeline(endpoint_manager, config={'debug': True})
        
        result = await pipeline.process("What is DNA?")
        assert result is not None


@pytest.mark.integration  
@pytest.mark.slow
class TestRealEndpointIntegration:
    """Integration tests with real endpoints (when available)"""
    
    @pytest.fixture
    def real_pipeline(self):
        """Create pipeline with real endpoint (skip if not available)"""
        try:
            endpoint_manager = EndpointManager()
            # This would be configured with real nanopub endpoint
            # For testing, we'll skip if no real endpoint configured
            pytest.skip("Real nanopub endpoint not configured for testing")
        except Exception:
            pytest.skip("Real endpoint not available")
    
    @pytest.mark.asyncio
    async def test_real_citation_query(self, real_pipeline):
        """Test with real citation query (when endpoint available)"""
        question = "What papers cite https://doi.org/10.1038/nature12373?"
        
        result = await real_pipeline.process(question)
        
        assert result is not None
        assert result.summary is not None
        # Would include more specific assertions based on expected real data
    
    @pytest.mark.asyncio
    async def test_real_orcid_query(self, real_pipeline):
        """Test with real ORCID query (when endpoint available)"""
        question = "What papers by 0000-0002-1784-2920?"
        
        result = await real_pipeline.process(question)
        
        assert result is not None
        assert result.summary is not None


@pytest.mark.performance
class TestPerformance:
    """Performance tests for the pipeline"""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline for performance testing"""
        endpoint_manager = EndpointManager()
        test_endpoint = TestNanopubEndpoint()
        endpoint_manager.register_endpoint('test', test_endpoint, is_default=True)
        
        return ScienceLivePipeline(endpoint_manager)
    
    @pytest.mark.asyncio
    async def test_response_time(self, pipeline):
        """Test pipeline response time"""
        import time
        
        question = "What papers cite AlexNet?"
        
        start_time = time.time()
        result = await pipeline.process(question)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on requirements)
        assert execution_time < 10.0  # 10 seconds max
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, pipeline):
        """Test concurrent question processing"""
        import asyncio
        
        questions = [
            "What papers cite AlexNet?",
            "Who authored ImageNet?",
            "Where is CERN?",
            "What is quantum mechanics?",
            "How does machine learning work?"
        ]
        
        # Process all questions concurrently
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*[
            pipeline.process(q) for q in questions
        ])
        end_time = asyncio.get_event_loop().time()
        
        # Should handle concurrent processing
        assert len(results) == len(questions)
        assert all(r is not None for r in results)
        
        # Concurrent processing should be faster than sequential
        total_time = end_time - start_time
        assert total_time < 30.0  # Reasonable upper bound
