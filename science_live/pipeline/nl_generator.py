"""
NaturalLanguageGenerator - Convert results back to natural language
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
    ProcessedResults,
    ProcessingContext,
    NaturalLanguageResult,
    RosettaStatement,
)

# ============================================================================
# NATURAL LANGUAGE GENERATOR
# ============================================================================

class NaturalLanguageGenerator:
    """Convert results back to natural language"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate(self, processed_results: ProcessedResults, context: ProcessingContext) -> NaturalLanguageResult:
        """Generate natural language summary of results"""
        self.logger.info(f"Generating natural language for {processed_results.total_found} results")
        
        if processed_results.total_found == 0:
            return self._generate_no_results_response(context)
        
        # Generate summary
        summary = self._generate_summary(processed_results, context)
        
        # Generate detailed results
        detailed_results = await self._generate_detailed_results(processed_results)
        
        # Generate confidence explanation
        confidence_explanation = self._generate_confidence_explanation(processed_results)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(processed_results, context)
        
        # Generate execution summary
        execution_summary = self._generate_execution_summary(context)
        
        result = NaturalLanguageResult(
            summary=summary,
            detailed_results=detailed_results,
            confidence_explanation=confidence_explanation,
            suggestions=suggestions,
            execution_summary=execution_summary
        )
        
        self.logger.info("Generated natural language response")
        return result
    
    def _generate_summary(self, processed_results: ProcessedResults, context: ProcessingContext) -> str:
        """Generate high-level summary"""
        total = processed_results.total_found
        confidence = processed_results.processing_confidence
        
        # Analyze result types
        type_counts = {}
        for result_type, results in processed_results.groupings.get('by_type', {}).items():
            type_counts[result_type] = len(results)
        
        # Generate summary based on most common result type
        if 'citation' in type_counts and type_counts['citation'] > total * 0.5:
            summary = f"Found {total} citation relationships"
        elif 'rosetta_statement' in type_counts:
            summary = f"Found {total} scientific statements"
        else:
            summary = f"Found {total} relevant nanopublications"
        
        # Add confidence qualifier
        if confidence >= 0.8:
            summary += " with high confidence."
        elif confidence >= 0.5:
            summary += " with moderate confidence."
        else:
            summary += " with low confidence."
        
        return summary
    
    async def _generate_detailed_results(self, processed_results: ProcessedResults) -> List[str]:
        """Generate detailed descriptions of individual results"""
        detailed = []
        
        # Limit to top results
        top_results = sorted(processed_results.results, key=lambda x: x.confidence, reverse=True)[:10]
        
        for i, result in enumerate(top_results, 1):
            if result.rosetta_statement and result.rosetta_statement.dynamic_label_template:
                # Use Rosetta statement's natural language representation
                description = self._rosetta_to_natural_language(result.rosetta_statement)
            else:
                # Fallback to generic description
                description = f"Nanopublication {result.nanopub_uri}"
            
            # Add confidence indicator
            if result.confidence >= 0.8:
                confidence_indicator = "✓"
            elif result.confidence >= 0.5:
                confidence_indicator = "~"
            else:
                confidence_indicator = "?"
            
            detailed.append(f"{i}. {confidence_indicator} {description}")
        
        return detailed
    
    def _rosetta_to_natural_language(self, rosetta_statement: RosettaStatement) -> str:
        """Convert Rosetta statement to natural language"""
        template = rosetta_statement.dynamic_label_template
        if not template:
            return f"{rosetta_statement.subject.label or rosetta_statement.subject.text} {rosetta_statement.statement_type_label}"
        
        # Replace placeholders
        result = template.replace("SUBJECT", rosetta_statement.subject.label or rosetta_statement.subject.text)
        
        if rosetta_statement.required_object1:
            result = result.replace("OBJECT1", rosetta_statement.required_object1.label or rosetta_statement.required_object1.text)
        
        if rosetta_statement.optional_object1:
            result = result.replace("OBJECT2", rosetta_statement.optional_object1.label or rosetta_statement.optional_object1.text)
        
        # Clean up any remaining placeholders
        result = re.sub(r'(OBJECT[0-9]+|SUBJECT)', '', result)
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def _generate_confidence_explanation(self, processed_results: ProcessedResults) -> str:
        """Explain the confidence level"""
        confidence = processed_results.processing_confidence
        
        if confidence >= 0.8:
            return "High confidence: Results closely match your query with well-structured data."
        elif confidence >= 0.6:
            return "Good confidence: Results are relevant with mostly complete information."
        elif confidence >= 0.4:
            return "Moderate confidence: Results may be relevant but information is incomplete."
        else:
            return "Low confidence: Results are uncertain and may not fully match your query."
    
    def _generate_suggestions(self, processed_results: ProcessedResults, context: ProcessingContext) -> List[str]:
        """Generate suggestions for related queries"""
        suggestions = []
        
        # Analyze result patterns to suggest related queries
        if 'citation' in processed_results.groupings.get('by_type', {}):
            suggestions.append("Try searching for 'papers authored by [author name]'")
            suggestions.append("Search for 'recent citations of this work'")
        
        if processed_results.total_found > 50:
            suggestions.append("Add more specific terms to narrow your search")
        elif processed_results.total_found < 5:
            suggestions.append("Try broader terms or check spelling")
            suggestions.append("Use alternative phrasings of your question")
        
        # Add generic suggestions
        suggestions.extend([
            "Explore related concepts using 'what is related to [topic]'",
            "Find author information with ORCID: 'work by 0000-0000-0000-0000'"
        ])
        
        return suggestions[:5]
    
    def _generate_execution_summary(self, context: ProcessingContext) -> Dict[str, Any]:
        """Generate summary of execution process"""
        total_time = context.get_elapsed_time()  # Use the context's elapsed time method
        
        return {
            'total_execution_time': round(total_time, 2),
            'query_processed': context.original_question,
            'pipeline_steps_completed': 7,
            'debug_mode': context.debug_mode
        }
           
    def _generate_no_results_response(self, context: ProcessingContext) -> NaturalLanguageResult:
        """Generate response when no results found"""
            
        # Check if we have execution errors that might explain no results
        execution_errors = getattr(context, 'execution_errors', [])
        network_errors = [err for err in execution_errors if 'network' in str(err).lower() or 'connection' in str(err).lower()]
    
        if network_errors:
            # Network error caused no results
            summary = "Unable to search nanopublications due to network connectivity issues."
            confidence_explanation = "Could not connect to the nanopublication network to process your query."
            suggestions = [
                "Please try again in a few moments",
                "Check your internet connection",
                "The nanopublication servers may be temporarily unavailable",
                "Try a simpler query if the problem persists"
            ]
        else:
            # Normal no results case
            summary = "No results found for your query."
            confidence_explanation = "Unable to find matching information in the nanopub network."
            suggestions = [
                "Check spelling and try different terms",
                "Use more general concepts", 
                "Try asking about related topics",
                "Include specific identifiers like DOI or ORCID if available"
            ]
    
        return NaturalLanguageResult(
            summary=summary,
            detailed_results=[],
            confidence_explanation=confidence_explanation,
            suggestions=suggestions,
            execution_summary=self._generate_execution_summary(context)
        )

