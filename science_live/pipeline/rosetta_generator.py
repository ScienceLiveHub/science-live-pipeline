"""
RosettaStatementGenerator - Generate Rosetta statements from entities
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
    LinkedEntities, 
    ProcessedQuestion, 
    ProcessingContext,
    GeneratedStatements, 
    RosettaStatement,
)

# ============================================================================
# ROSETTA STATEMENT GENERATOR
# ============================================================================

class RosettaStatementGenerator:
    """Generate Rosetta statements from entities"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.statement_templates = self._initialize_statement_templates()
    
    def _initialize_statement_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize Rosetta statement templates"""
        return {
            'cites': {
                'uri': 'https://w3id.org/rosetta/Cites',
                'label': 'cites',
                'dynamic_template': 'SUBJECT cites OBJECT1',
                'typical_verbs': ['cites', 'references', 'mentions'],
                'question_patterns': [r'cite', r'reference', r'mention'],
                'requires_object1': True
            },
            'authored_by': {
                'uri': 'https://w3id.org/rosetta/AuthoredBy',
                'label': 'authored by',
                'dynamic_template': 'SUBJECT was authored by OBJECT1',
                'typical_verbs': ['authored', 'written', 'created'],
                'question_patterns': [r'author', r'wrote', r'written by'],
                'requires_object1': True
            },
            'has_measurement': {
                'uri': 'https://w3id.org/rosetta/HasMeasurement',
                'label': 'has measurement',
                'dynamic_template': 'SUBJECT has OBJECT1 of OBJECT2 OBJECT3',
                'typical_verbs': ['measures', 'weighs', 'contains'],
                'question_patterns': [r'mass', r'weight', r'temperature', r'measurement'],
                'requires_object1': True
            },
            'located_in': {
                'uri': 'https://w3id.org/rosetta/LocatedIn',
                'label': 'located in',
                'dynamic_template': 'SUBJECT is located in OBJECT1',
                'typical_verbs': ['located', 'situated', 'found'],
                'question_patterns': [r'where', r'location', r'located'],
                'requires_object1': True
            },
            'related_to': {
                'uri': 'https://w3id.org/rosetta/RelatedTo',
                'label': 'related to',
                'dynamic_template': 'SUBJECT is related to OBJECT1',
                'typical_verbs': ['related', 'connected', 'associated'],
                'question_patterns': [r'related', r'about', r'concerning'],
                'requires_object1': True
            }
        }
    
    async def generate(self, linked_entities: LinkedEntities, processed_question: ProcessedQuestion, context: ProcessingContext) -> GeneratedStatements:
        """Generate Rosetta statements from linked entities"""
        self.logger.info(f"Generating Rosetta statements from {len(linked_entities.entities)} entities")
        
        # Determine best statement types for this question
        statement_types = self._match_statement_types(processed_question)
        
        statements = []
        alternatives = []
        
        # Generate statements for each type
        for stmt_type in statement_types[:3]:  # Limit to top 3
            generated = await self._generate_statements_for_type(
                stmt_type, linked_entities, processed_question
            )
            statements.extend(generated['primary'])
            alternatives.extend(generated['alternatives'])
        
        # Calculate generation confidence
        confidence = self._calculate_generation_confidence(statements, linked_entities)
        
        result = GeneratedStatements(
            statements=statements,
            generation_confidence=confidence,
            alternative_interpretations=alternatives
        )
        
        self.logger.info(f"Generated {len(statements)} primary statements with confidence {confidence}")
        return result
    
    def _match_statement_types(self, processed_question: ProcessedQuestion) -> List[str]:
        """Match question to appropriate statement types"""
        question_lower = processed_question.cleaned_text.lower()
        matches = []
        
        for stmt_type, template in self.statement_templates.items():
            score = 0
            
            # Check for question patterns
            for pattern in template['question_patterns']:
                if re.search(pattern, question_lower):
                    score += 3
            
            # Check for typical verbs
            for verb in template['typical_verbs']:
                if verb in question_lower:
                    score += 2
            
            if score > 0:
                matches.append((stmt_type, score))
        
        # Sort by score and return types
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches]
    
    async def _generate_statements_for_type(self, stmt_type: str, linked_entities: LinkedEntities, processed_question: ProcessedQuestion) -> Dict[str, List[RosettaStatement]]:
        """Generate statements for a specific type"""
        template = self.statement_templates[stmt_type]
        statements = {'primary': [], 'alternatives': []}
        
        # Try different subject-object combinations
        for subject in linked_entities.subject_candidates:
            for obj in linked_entities.object_candidates:
                if subject != obj:  # Don't create self-referencing statements
                    stmt = RosettaStatement(
                        subject=subject,
                        statement_type_uri=template['uri'],
                        statement_type_label=template['label'],
                        required_object1=obj if template['requires_object1'] else None,
                        dynamic_label_template=template['dynamic_template']
                    )
                    statements['primary'].append(stmt)
        
        # If no object candidates, try with just subject (for some statement types)
        if not statements['primary'] and linked_entities.subject_candidates:
            for subject in linked_entities.subject_candidates:
                stmt = RosettaStatement(
                    subject=subject,
                    statement_type_uri=template['uri'],
                    statement_type_label=template['label'],
                    dynamic_label_template=template['dynamic_template']
                )
                statements['alternatives'].append(stmt)
        
        return statements
    
    def _calculate_generation_confidence(self, statements: List[RosettaStatement], linked_entities: LinkedEntities) -> float:
        """Calculate confidence in generated statements"""
        if not statements:
            return 0.0
        
        # Base confidence on entity linking confidence
        base_confidence = linked_entities.linking_confidence
        
        # Adjust based on number of complete statements
        complete_statements = sum(1 for stmt in statements if stmt.required_object1 is not None)
        completeness_factor = complete_statements / len(statements) if statements else 0
        
        return base_confidence * (0.5 + 0.5 * completeness_factor)

