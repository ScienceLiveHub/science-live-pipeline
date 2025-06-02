"""
QueryExecutor - Execute SPARQL against nanopub endpoints  
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import asyncio
import logging
from datetime import datetime

# Import all required classes from common
from .common import (
    GeneratedQueries,
    ProcessingContext,
    QueryResults,
    SPARQLQuery,
)


# ============================================================================
# QUERY EXECUTOR
# ============================================================================

class QueryExecutor:
    """Execute SPARQL against nanopub endpoints"""
    
    def __init__(self, endpoint_manager, config: Dict[str, Any] = None):
        self.endpoint_manager = endpoint_manager
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.query_cache = {}
    
    async def execute(self, generated_queries: GeneratedQueries, context: ProcessingContext) -> QueryResults:
        """Execute SPARQL queries with fallback strategy"""
        self.logger.info("Executing SPARQL queries")

        # Initialize execution errors tracking
        if not hasattr(context, 'execution_errors'):
            context.execution_errors = []

        # Try primary query first
        result = await self._execute_single_query(generated_queries.primary_query, context)
        
        if result.success and result.total_results > 0:
            self.logger.info(f"Primary query succeeded with {result.total_results} results")
            return result
        
        # If primary failed due to error (not just no results), track it
        if not result.success and result.error_message:
            context.execution_errors.append(f"Primary query failed: {result.error_message}")
    
        # Try fallback queries
        for i, fallback_query in enumerate(generated_queries.fallback_queries):
            self.logger.info(f"Trying fallback query {i+1}")
            result = await self._execute_single_query(fallback_query, context)
            
            if result.success and result.total_results > 0:
                self.logger.info(f"Fallback query {i+1} succeeded with {result.total_results} results")
                return result
            elif not result.success and result.error_message:
                context.execution_errors.append(f"Fallback query {i+1} failed: {result.error_message}")
        
        # All queries failed - return last result with error info
        self.logger.warning("All queries failed")
        return result
    
    async def _execute_single_query(self, sparql_query: SPARQLQuery, context: ProcessingContext) -> QueryResults:
        """Execute a single SPARQL query"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check cache first
            cache_key = hash(sparql_query.query_text)
            if cache_key in self.query_cache:
                cached_result = self.query_cache[cache_key]
                self.logger.debug("Using cached query result")
                return QueryResults(
                    success=True,
                    results=cached_result['results'],
                    query_used=sparql_query.query_text,
                    execution_time=cached_result['execution_time'],
                    total_results=len(cached_result['results'])
                )
            
            # Get endpoint
            endpoint = self.endpoint_manager.get_endpoint()
            
            # Execute query
            raw_results = await endpoint.execute_sparql(sparql_query.query_text)
            
            # Process results
            bindings = raw_results.get('results', {}).get('bindings', [])
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Cache results
            self.query_cache[cache_key] = {
                'results': bindings,
                'execution_time': execution_time
            }
            
            return QueryResults(
                success=True,
                results=bindings,
                query_used=sparql_query.query_text,
                execution_time=execution_time,
                total_results=len(bindings)
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"Query execution failed: {str(e)}")
            
            return QueryResults(
                success=False,
                results=[],
                query_used=sparql_query.query_text,
                execution_time=execution_time,
                total_results=0,
                error_message=str(e)
            )

