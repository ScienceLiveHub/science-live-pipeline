"""
SPARQLGenerator - Convert Rosetta statements to SPARQL queries
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
    GeneratedStatements, 
    ProcessingContext,
    GeneratedQueries,
    RosettaStatement,
    SPARQLQuery,
)

# ============================================================================
# SPARQL GENERATOR
# ============================================================================

class SPARQLGenerator:
    """Convert Rosetta statements to SPARQL queries"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.query_templates = self._initialize_query_templates()
    
    def _initialize_query_templates(self) -> Dict[str, str]:
        """Initialize SPARQL query templates"""
        return {
            'basic_rosetta': '''
PREFIX np: <http://www.nanopub.org/nschema#>
PREFIX rosetta: <https://w3id.org/rosetta/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?np ?statement ?subject ?object1 ?object2 ?object3 ?label ?confidence WHERE {{
  ?np np:hasAssertion ?assertion .
  ?statement a rosetta:RosettaStatement .
  ?statement rosetta:hasStatementType <{statement_type}> .
  {subject_pattern}
  {object_patterns}
  OPTIONAL {{ ?statement rosetta:hasDynamicLabel ?label . }}
  OPTIONAL {{ ?statement rosetta:hasConfidenceLevel ?confidence . }}
  {filters}
}}
LIMIT {limit}
            ''',
            
            'citation_search': '''
PREFIX np: <http://www.nanopub.org/nschema#>
PREFIX cito: <http://purl.org/spar/cito/>
PREFIX fabio: <http://purl.org/spar/fabio/>

SELECT DISTINCT ?np ?citing_paper ?cited_paper ?citation_type WHERE {{
  ?np np:hasAssertion ?assertion .
  ?citing_paper ?citation_type ?cited_paper .
  ?citing_paper a fabio:ScholarlyWork .
  {subject_filter}
  FILTER(STRSTARTS(STR(?citation_type), "http://purl.org/spar/cito/"))
}}
LIMIT {limit}
            ''',
            
            'fallback_text': '''
PREFIX np: <http://www.nanopub.org/nschema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?np ?subject ?predicate ?object ?label WHERE {{
  ?np np:hasAssertion ?assertion .
  ?subject ?predicate ?object .
  OPTIONAL {{ ?subject rdfs:label ?label . }}
  {text_filters}
}}
LIMIT {limit}
            '''
        }
    
    async def generate(self, generated_statements: GeneratedStatements, context: ProcessingContext) -> GeneratedQueries:
        """Generate SPARQL queries from Rosetta statements"""
        self.logger.info(f"Generating SPARQL from {len(generated_statements.statements)} statements")
        
        if not generated_statements.statements:
            # Create fallback query
            return self._create_fallback_queries(context)
        
        # Generate primary query from best statement
        primary_statement = generated_statements.statements[0]
        primary_query = self._generate_rosetta_query(primary_statement)
        
        # Generate fallback queries
        fallback_queries = []
        
        # Alternative Rosetta statements
        for stmt in generated_statements.statements[1:3]:
            fallback_queries.append(self._generate_rosetta_query(stmt))
        
        # Alternative interpretations
        for stmt in generated_statements.alternative_interpretations[:2]:
            fallback_queries.append(self._generate_rosetta_query(stmt))
        
        # Citation-specific fallback if applicable
        if self._is_citation_query(primary_statement):
            citation_query = self._generate_citation_query(primary_statement)
            fallback_queries.insert(0, citation_query)
        
        result = GeneratedQueries(
            primary_query=primary_query,
            fallback_queries=fallback_queries,
            generation_method='rosetta_template'
        )
        
        self.logger.info(f"Generated primary query with {len(fallback_queries)} fallbacks")
        return result
    
    def _generate_rosetta_query(self, statement: RosettaStatement) -> SPARQLQuery:
        """Generate SPARQL query for a Rosetta statement"""
        template = self.query_templates['basic_rosetta']
        
        # Build subject pattern
        if statement.subject.uri:
            subject_pattern = f"?statement rosetta:subject <{statement.subject.uri}> ."
        else:
            subject_pattern = f'?statement rosetta:subject ?subject .\n  FILTER(CONTAINS(LCASE(STR(?subject)), "{statement.subject.text.lower()}"))'
        
        # Build object patterns
        object_patterns = []
        if statement.required_object1:
            if statement.required_object1.uri:
                object_patterns.append(f"?statement rosetta:requiredObjectPosition1 <{statement.required_object1.uri}> .")
            else:
                object_patterns.append(f'?statement rosetta:requiredObjectPosition1 ?object1 .\n  FILTER(CONTAINS(LCASE(STR(?object1)), "{statement.required_object1.text.lower()}"))')
        else:
            object_patterns.append("OPTIONAL { ?statement rosetta:requiredObjectPosition1 ?object1 . }")
        
        # Add optional objects
        for i, obj in enumerate([statement.optional_object1, statement.optional_object2, statement.optional_object3], 1):
            if obj and obj.uri:
                object_patterns.append(f"OPTIONAL {{ ?statement rosetta:optionalObjectPosition{i} <{obj.uri}> . }}")
            elif obj:
                object_patterns.append(f"OPTIONAL {{ ?statement rosetta:optionalObjectPosition{i} ?object{i+1} . FILTER(CONTAINS(LCASE(STR(?object{i+1})), \"{obj.text.lower()}\")) }}")
            else:
                object_patterns.append(f"OPTIONAL {{ ?statement rosetta:optionalObjectPosition{i} ?object{i+1} . }}")
        
        # Build filters
        filters = []
        if statement.confidence_level:
            filters.append(f"FILTER(?confidence >= {statement.confidence_level})")
        
        if statement.is_negation:
            filters.append('?statement rosetta:isNegation "true"^^xsd:boolean .')
        else:
            filters.append('OPTIONAL { ?statement rosetta:isNegation ?negation . } FILTER(!BOUND(?negation) || ?negation = "false"^^xsd:boolean)')
        
        # Fill template
        query_text = template.format(
            statement_type=statement.statement_type_uri,
            subject_pattern=subject_pattern,
            object_patterns='\n  '.join(object_patterns),
            filters='\n  '.join(filters),
            limit=self.config.get('result_limit', 50)
        )
        
        return SPARQLQuery(
            query_text=query_text,
            query_type='SELECT',
            estimated_complexity=self._estimate_complexity(statement),
        )
    
    def _generate_citation_query(self, statement: RosettaStatement) -> SPARQLQuery:
        """Generate citation-specific SPARQL query"""
        template = self.query_templates['citation_search']
        
        # Build subject filter for citation queries
        if statement.subject.uri:
            subject_filter = f"FILTER(?cited_paper = <{statement.subject.uri}>)"
        else:
            subject_filter = f'FILTER(CONTAINS(LCASE(STR(?cited_paper)), "{statement.subject.text.lower()}"))'
        
        query_text = template.format(
            subject_filter=subject_filter,
            limit=self.config.get('result_limit', 50)
        )
        
        return SPARQLQuery(
            query_text=query_text,
            query_type='SELECT',
            estimated_complexity=2
        )
    
    def _create_fallback_queries(self, context: ProcessingContext) -> GeneratedQueries:
        """Create fallback queries when no Rosetta statements generated"""
        template = self.query_templates['fallback_text']
        
        # Extract key terms from original question
        question_words = context.original_question.lower().split()
        important_words = [word for word in question_words if len(word) > 3][:3]
        
        text_filters = []
        for word in important_words:
            text_filters.append(f'FILTER(CONTAINS(LCASE(STR(?label)), "{word}"))')
        
        query_text = template.format(
            text_filters=' || '.join(text_filters) if text_filters else '',
            limit=self.config.get('result_limit', 20)
        )
        
        fallback_query = SPARQLQuery(
            query_text=query_text,
            query_type='SELECT',
            estimated_complexity=1
        )
        
        return GeneratedQueries(
            primary_query=fallback_query,
            fallback_queries=[],
            generation_method='text_fallback'
        )
    
    def _is_citation_query(self, statement: RosettaStatement) -> bool:
        """Check if statement is citation-related"""
        return any(term in statement.statement_type_label.lower() 
                  for term in ['cite', 'reference', 'mention'])
    
    def _estimate_complexity(self, statement: RosettaStatement) -> int:
        """Estimate query complexity (1-5 scale)"""
        complexity = 1
        
        if statement.required_object1:
            complexity += 1
        if statement.optional_object1:
            complexity += 1
        if statement.confidence_level:
            complexity += 1
        if statement.context:
            complexity += 1
        
        return min(complexity, 5)

