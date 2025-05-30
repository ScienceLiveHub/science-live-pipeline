# ============================================================================
# tests/test_core/test_endpoints.py
# ============================================================================

"""
Tests for Endpoint Management
============================
"""

import pytest
from unittest.mock import AsyncMock, patch
from science_live.core.endpoints import (
    EndpointManager, StandardNanopubEndpoint, MockNanopubEndpoint
)


class TestEndpointManager:
    """Test EndpointManager functionality"""
    
    @pytest.fixture
    def manager(self):
        """Create endpoint manager for testing"""
        return EndpointManager()
    
    def test_register_endpoint(self, manager):
        """Test endpoint registration"""
        endpoint = MockNanopubEndpoint()
        manager.register_endpoint('test', endpoint, is_default=True)
        
        assert 'test' in manager.endpoints
        assert manager.default_endpoint == 'test'
        assert manager.get_endpoint() == endpoint
    
    def test_get_endpoint_by_name(self, manager):
        """Test getting endpoint by name"""
        endpoint1 = MockNanopubEndpoint()
        endpoint2 = MockNanopubEndpoint()
        
        manager.register_endpoint('test1', endpoint1)
        manager.register_endpoint('test2', endpoint2)
        
        assert manager.get_endpoint('test1') == endpoint1
        assert manager.get_endpoint('test2') == endpoint2
    
    def test_missing_endpoint(self, manager):
        """Test error when endpoint not found"""
        with pytest.raises(ValueError, match="Endpoint 'missing' not found"):
            manager.get_endpoint('missing')
    
    def test_list_endpoints(self, manager):
        """Test listing endpoints"""
        manager.register_endpoint('test1', MockNanopubEndpoint())
        manager.register_endpoint('test2', MockNanopubEndpoint())
        
        endpoints = manager.list_endpoints()
        assert 'test1' in endpoints
        assert 'test2' in endpoints
        assert len(endpoints) == 2


class TestMockNanopubEndpoint:
    """Test MockNanopubEndpoint functionality"""
    
    @pytest.fixture
    def endpoint(self):
        """Create test endpoint"""
        return MockNanopubEndpoint()
    
    @pytest.mark.asyncio
    async def test_execute_sparql(self, endpoint):
        """Test SPARQL execution"""
        query = "SELECT * WHERE { ?s ?p ?o }"
        result = await endpoint.execute_sparql(query)
        
        assert 'results' in result
        assert 'bindings' in result['results']
        assert len(result['results']['bindings']) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_nanopub(self, endpoint):
        """Test nanopub fetching"""
        uri = "http://purl.org/np/test"
        result = await endpoint.fetch_nanopub(uri)
        
        assert result['uri'] == uri
        assert result['format'] == 'trig'
        assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_search_text(self, endpoint):
        """Test text search"""
        results = await endpoint.search_text("machine learning")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert 'np' in results[0]
        assert 'label' in results[0]

