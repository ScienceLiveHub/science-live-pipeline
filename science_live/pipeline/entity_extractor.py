"""
EntityExtractorLinker - Extract and link entities to URIs
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
    ExtractedEntity, 
    LinkedEntities, 
    ProcessedQuestion, 
    ProcessingContext, 
    EntityType, 
    PipelineStep,
    validate_extracted_entity
)

# ============================================================================
# ENTITY EXTRACTOR & LINKER
# ============================================================================

class EntityExtractorLinker:
    """Extract and link entities to URIs"""
    
    def __init__(self, endpoint_manager, config: Dict[str, Any] = None):
        self.endpoint_manager = endpoint_manager
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._entity_cache = {}
    
    async def extract_and_link(self, processed_question: ProcessedQuestion, context: ProcessingContext) -> LinkedEntities:
        """Extract and link entities from processed question"""
        self.logger.info(f"Extracting entities from: {processed_question.cleaned_text}")
        
        # Extract entities
        extracted_entities = await self._extract_entities(processed_question)
        
        # Link entities to URIs
        linked_entities = await self._link_entities(extracted_entities)
        
        # Classify entities as subjects or objects
        subject_candidates, object_candidates = self._classify_entities(linked_entities, processed_question)
        
        # Calculate overall linking confidence
        linking_confidence = self._calculate_linking_confidence(linked_entities)
        
        result = LinkedEntities(
            entities=linked_entities,
            subject_candidates=subject_candidates,
            object_candidates=object_candidates,
            linking_confidence=linking_confidence
        )
        
        self.logger.info(f"Extracted {len(linked_entities)} entities with confidence {linking_confidence}")
        return result
    
    async def _extract_entities(self, processed_question: ProcessedQuestion) -> List[ExtractedEntity]:
        """Extract entities with type classification"""
        entities = []
        text = processed_question.original_text
        
        # Extract DOIs
        for match in re.finditer(r'10\.\d+/[^\s]+', text):
            entities.append(ExtractedEntity(
                text=match.group(),
                entity_type='DOI',
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Extract ORCIDs
        for match in re.finditer(r'0000-\d{4}-\d{4}-\d{3}[\dX]', text):
            entities.append(ExtractedEntity(
                text=match.group(),
                entity_type='ORCID',
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Extract URLs
        for match in re.finditer(r'https?://[^\s]+', text):
            entities.append(ExtractedEntity(
                text=match.group(),
                entity_type='URL',
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Extract quoted strings (potential titles/names)
        for match in re.finditer(r'"([^"]+)"', text):
            entities.append(ExtractedEntity(
                text=match.group(1),
                entity_type='TITLE',
                confidence=0.7,
                start_pos=match.start(1),
                end_pos=match.end(1)
            ))
        
        # Extract capitalized terms (potential proper nouns)
        for match in re.finditer(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text):
            # Skip if it's a question word
            if match.group().lower() not in ['What', 'Who', 'Where', 'When', 'How', 'Why']:
                entities.append(ExtractedEntity(
                    text=match.group(),
                    entity_type='CONCEPT',
                    confidence=0.6,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    async def _link_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Link entities to URIs"""
        linked_entities = []
        
        for entity in entities:
            # Check cache first
            cache_key = f"{entity.entity_type}:{entity.text}"
            if cache_key in self._entity_cache:
                cached = self._entity_cache[cache_key]
                entity.uri = cached['uri']
                entity.label = cached['label']
                entity.aliases = cached['aliases']
                linked_entities.append(entity)
                continue
            
            # Link based on entity type
            if entity.entity_type == 'DOI':
                entity.uri = f"https://doi.org/{entity.text}"
                entity.label = entity.text
            
            elif entity.entity_type == 'ORCID':
                entity.uri = f"https://orcid.org/{entity.text}"
                entity.label = await self._get_orcid_name(entity.text)
            
            elif entity.entity_type == 'URL':
                entity.uri = entity.text
                entity.label = entity.text
            
            elif entity.entity_type in ['TITLE', 'CONCEPT']:
                # Try to link via Wikidata or other services
                linked_info = await self._link_via_external_services(entity.text, entity.entity_type)
                if linked_info:
                    entity.uri = linked_info['uri']
                    entity.label = linked_info['label']
                    entity.aliases = linked_info.get('aliases', [])
                    entity.confidence = min(entity.confidence, linked_info.get('confidence', 0.5))
            
            # Cache the result
            self._entity_cache[cache_key] = {
                'uri': entity.uri,
                'label': entity.label,
                'aliases': entity.aliases
            }
            
            linked_entities.append(entity)
        
        return linked_entities
    
    async def _get_orcid_name(self, orcid: str) -> str:
        """Get name for ORCID (simplified - would query ORCID API in production)"""
        # For demo purposes, return ORCID itself
        # In production, would query ORCID API
        return orcid
    
    async def _link_via_external_services(self, text: str, entity_type: str) -> Optional[Dict[str, Any]]:
        """Link entity via external services like Wikidata"""
        # Simplified implementation
        # In production, would query Wikidata API, OpenAlex, etc.
        return None
    
    def _classify_entities(self, entities: List[ExtractedEntity], processed_question: ProcessedQuestion) -> Tuple[List[ExtractedEntity], List[ExtractedEntity]]:
        """Classify entities as potential subjects or objects"""
        subject_candidates = []
        object_candidates = []
        
        # Simple heuristic: entities appearing early in the question are likely subjects
        question_length = len(processed_question.cleaned_text)
        
        for entity in entities:
            position_ratio = entity.start_pos / question_length
            
            if position_ratio < 0.5:
                subject_candidates.append(entity)
            else:
                object_candidates.append(entity)
            
            # High-confidence entities (DOIs, ORCIDs) are good subjects
            if entity.entity_type in ['DOI', 'ORCID'] and entity.confidence > 0.9:
                if entity not in subject_candidates:
                    subject_candidates.append(entity)
        
        return subject_candidates, object_candidates
    
    def _calculate_linking_confidence(self, entities: List[ExtractedEntity]) -> float:
        """Calculate overall linking confidence"""
        if not entities:
            return 0.0
        
        total_confidence = sum(entity.confidence for entity in entities)
        return total_confidence / len(entities)

