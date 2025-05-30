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

