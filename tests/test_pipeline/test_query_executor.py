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


