"""
ResultProcessor - Process raw SPARQL results into structured format
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
    QueryResults,
    GeneratedStatements,
    ProcessingContext,
    ProcessedResults,
    StructuredResult,
    RosettaStatement,
)


# ============================================================================
# RESULT PROCESSOR
# ============================================================================

class ResultProcessor:
    """Process raw SPARQL results into structured format"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def process(self, query_results: QueryResults, generated_statements: GeneratedStatements, context: ProcessingContext) -> ProcessedResults:
        """Process raw SPARQL results"""
        self.logger.info(f"Processing {query_results.total_results} raw results")
        
        if not query_results.success or not query_results.results:
            return ProcessedResults(
                results=[],
                total_found=0,
                processing_confidence=0.0
            )
        
        # Convert raw results to structured results
        structured_results = []
        for raw_result in query_results.results:
            structured = await self._process_single_result(raw_result, generated_statements)
            if structured:
                structured_results.append(structured)
        
        # Group results by type
        groupings = self._group_results(structured_results)
        
        # Calculate processing confidence
        confidence = self._calculate_processing_confidence(structured_results, query_results)
        
        result = ProcessedResults(
            results=structured_results,
            total_found=len(structured_results),
            processing_confidence=confidence,
            groupings=groupings
        )
        
        self.logger.info(f"Processed to {len(structured_results)} structured results")
        return result
    
    async def _process_single_result(self, raw_result: Dict[str, Any], generated_statements: GeneratedStatements) -> Optional[StructuredResult]:
        """Process a single raw SPARQL result"""
        try:
            # Extract basic information
            nanopub_uri = raw_result.get('np', {}).get('value')
            if not nanopub_uri:
                return None
            
            structured = StructuredResult(
                nanopub_uri=nanopub_uri,
                statement_uri=raw_result.get('statement', {}).get('value'),
                raw_data=raw_result
            )
            
            # Try to match with original Rosetta statement
            structured.rosetta_statement = self._match_to_rosetta_statement(raw_result, generated_statements)
            
            # Extract confidence if available
            if 'confidence' in raw_result:
                try:
                    structured.confidence = float(raw_result['confidence']['value'])
                except (ValueError, KeyError):
                    structured.confidence = 1.0
            
            # Add metadata
            structured.metadata = {
                'has_dynamic_label': 'label' in raw_result,
                'result_type': self._classify_result_type(raw_result),
                'completeness': self._assess_completeness(raw_result)
            }
            
            return structured
            
        except Exception as e:
            self.logger.warning(f"Failed to process result: {str(e)}")
            return None
    
    def _match_to_rosetta_statement(self, raw_result: Dict[str, Any], generated_statements: GeneratedStatements) -> Optional[RosettaStatement]:
        """Try to match raw result back to original Rosetta statement"""
        statement_uri = raw_result.get('statement', {}).get('value')
        if not statement_uri:
            return None
        
        # Simple matching based on statement type
        for stmt in generated_statements.statements:
            if stmt.statement_type_uri in str(statement_uri):
                return stmt
        
        return None
    
    def _classify_result_type(self, raw_result: Dict[str, Any]) -> str:
        """Classify the type of result"""
        if 'citation_type' in raw_result:
            return 'citation'
        elif 'statement' in raw_result:
            return 'rosetta_statement'
        else:
            return 'general'
    
    def _assess_completeness(self, raw_result: Dict[str, Any]) -> float:
        """Assess how complete the result is"""
        expected_fields = ['np', 'subject', 'object1']
        present_fields = sum(1 for field in expected_fields if field in raw_result)
        return present_fields / len(expected_fields)
    
    def _group_results(self, results: List[StructuredResult]) -> Dict[str, List[StructuredResult]]:
        """Group results by various criteria"""
        groupings = {}
        
        # Group by result type
        by_type = {}
        for result in results:
            result_type = result.metadata.get('result_type', 'unknown')
            if result_type not in by_type:
                by_type[result_type] = []
            by_type[result_type].append(result)
        groupings['by_type'] = by_type
        
        # Group by confidence level
        by_confidence = {'high': [], 'medium': [], 'low': []}
        for result in results:
            if result.confidence >= 0.8:
                by_confidence['high'].append(result)
            elif result.confidence >= 0.5:
                by_confidence['medium'].append(result)
            else:
                by_confidence['low'].append(result)
        groupings['by_confidence'] = by_confidence
        
        return groupings
    
    def _calculate_processing_confidence(self, structured_results: List[StructuredResult], query_results: QueryResults) -> float:
        """Calculate confidence in result processing"""
        if not structured_results:
            return 0.0
        
        # Base confidence on successful processing rate
        processing_rate = len(structured_results) / query_results.total_results
        
        # Adjust for result completeness
        avg_completeness = sum(r.metadata.get('completeness', 0) for r in structured_results) / len(structured_results)
        
        # Adjust for confidence levels
        avg_confidence = sum(r.confidence for r in structured_results) / len(structured_results)
        
        return (processing_rate * 0.4 + avg_completeness * 0.3 + avg_confidence * 0.3)

