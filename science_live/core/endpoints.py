# ============================================================================
# science_live/core/endpoints.py
# ============================================================================

"""
Nanopub Endpoint Management
==========================

Manages connections to nanopublication servers and provides
a unified interface for SPARQL queries and nanopub retrieval.
"""

import aiohttp
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import json


class NanopubEndpoint(ABC):
    """Abstract base class for nanopub data sources"""
    
    @abstractmethod
    async def execute_sparql(self, query: str) -> Dict[str, Any]:
        """Execute a SPARQL query against the endpoint"""
        pass
    
    @abstractmethod
    async def fetch_nanopub(self, uri: str) -> Dict[str, Any]:
        """Fetch a specific nanopublication by URI"""
        pass
    
    @abstractmethod
    async def search_text(self, text: str, limit: int = 10) -> List[Dict]:
        """Search nanopubs by text"""
        pass


class StandardNanopubEndpoint(NanopubEndpoint):
    """Standard nanopub network endpoint implementation"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def execute_sparql(self, query: str) -> Dict[str, Any]:
        """Execute SPARQL query against nanopub endpoint"""
        session = await self._get_session()
        
        # Standard nanopub SPARQL endpoint
        sparql_url = urljoin(self.base_url, '/sparql')
        
        headers = {
            'Accept': 'application/sparql-results+json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'query': query}
        
        try:
            async with session.post(sparql_url, headers=headers, data=data) as response:
                response.raise_for_status()
                result = await response.json()
                return result
                
        except aiohttp.ClientError as e:
            self.logger.error(f"SPARQL query failed: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse SPARQL response: {e}")
            raise
    
    async def fetch_nanopub(self, uri: str) -> Dict[str, Any]:
        """Fetch nanopub by URI"""
        session = await self._get_session()
        
        # Try to fetch as Trig format
        headers = {'Accept': 'application/trig'}
        
        try:
            async with session.get(uri, headers=headers) as response:
                response.raise_for_status()
                content = await response.text()
                
                # Return as dict with content
                return {
                    'uri': uri,
                    'format': 'trig',
                    'content': content,
                    'status': response.status
                }
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Failed to fetch nanopub {uri}: {e}")
            raise
    
    async def search_text(self, text: str, limit: int = 10) -> List[Dict]:
        """Search nanopubs by text using SPARQL"""
        # Create a simple text search SPARQL query
        sparql_query = f"""
        PREFIX np: <http://www.nanopub.org/nschema#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?np ?label WHERE {{
            ?np np:hasAssertion ?assertion .
            ?assertion ?p ?o .
            OPTIONAL {{ ?o rdfs:label ?label . }}
            FILTER(CONTAINS(LCASE(STR(?o)), "{text.lower()}"))
        }}
        LIMIT {limit}
        """
        
        try:
            result = await self.execute_sparql(sparql_query)
            bindings = result.get('results', {}).get('bindings', [])
            
            # Convert to simplified format
            search_results = []
            for binding in bindings:
                search_results.append({
                    'np': binding.get('np', {}).get('value'),
                    'label': binding.get('label', {}).get('value', ''),
                    'score': 1.0  # Simple scoring
                })
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Text search failed: {e}")
            return []


class MockNanopubEndpoint(NanopubEndpoint):
    """Test nanopub endpoint with mock data"""
    
    def __init__(self, base_url: str = "https://test.nanopub.org"):
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute_sparql(self, query: str) -> Dict[str, Any]:
        """Return mock SPARQL results"""
        # Simple mock response
        return {
            'results': {
                'bindings': [
                    {
                        'np': {'value': 'http://purl.org/np/test_nanopub_1'},
                        'subject': {'value': 'http://example.org/subject1'},
                        'object1': {'value': 'http://example.org/object1'},
                        'label': {'value': 'Test nanopublication 1'}
                    },
                    {
                        'np': {'value': 'http://purl.org/np/test_nanopub_2'},
                        'subject': {'value': 'http://example.org/subject2'},
                        'object1': {'value': 'http://example.org/object2'},
                        'label': {'value': 'Test nanopublication 2'}
                    }
                ]
            }
        }
    
    async def fetch_nanopub(self, uri: str) -> Dict[str, Any]:
        """Return mock nanopub data"""
        return {
            'uri': uri,
            'format': 'trig',
            'content': f'# Mock nanopub content for {uri}',
            'status': 200
        }
    
    async def search_text(self, text: str, limit: int = 10) -> List[Dict]:
        """Return mock search results"""
        return [
            {'np': 'http://purl.org/np/test1', 'label': f'Test result for: {text}', 'score': 0.9},
            {'np': 'http://purl.org/np/test2', 'label': f'Another result for: {text}', 'score': 0.7}
        ]


class EndpointManager:
    """Manages multiple nanopub endpoints with failover support"""
    
    def __init__(self):
        self.endpoints: Dict[str, NanopubEndpoint] = {}
        self.default_endpoint: Optional[str] = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_endpoint(self, name: str, endpoint: NanopubEndpoint, is_default: bool = False):
        """Register a nanopub endpoint"""
        self.endpoints[name] = endpoint
        
        if is_default or not self.default_endpoint:
            self.default_endpoint = name
        
        self.logger.info(f"Registered endpoint: {name} (default: {is_default})")
    
    def get_endpoint(self, name: Optional[str] = None) -> NanopubEndpoint:
        """Get endpoint by name or return default"""
        endpoint_name = name or self.default_endpoint
        
        if not endpoint_name or endpoint_name not in self.endpoints:
            raise ValueError(f"Endpoint '{endpoint_name}' not found")
        
        return self.endpoints[endpoint_name]
    
    def list_endpoints(self) -> List[str]:
        """List all registered endpoints"""
        return list(self.endpoints.keys())
    
    async def close_all(self):
        """Close all endpoints"""
        for endpoint in self.endpoints.values():
            if hasattr(endpoint, 'close'):
                await endpoint.close()


