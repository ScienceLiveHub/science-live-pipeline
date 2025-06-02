"""
EntityExtractorLinker - Extract and link entities to URIs (FIXED FINAL VERSION)
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
# ENTITY EXTRACTOR & LINKER (FIXED FINAL VERSION)
# ============================================================================

class EntityExtractorLinker:
    """Extract and link entities to URIs with proper filtering and punctuation handling"""
    
    def __init__(self, endpoint_manager, config: Dict[str, Any] = None):
        self.endpoint_manager = endpoint_manager
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._entity_cache = {}
        
        # Initialize filtering lists
        self._function_words = self._initialize_function_words()
        self._question_words = self._initialize_question_words()
        self._boundary_words = self._initialize_boundary_words()
    
    def _initialize_function_words(self) -> set:
        """Initialize function words that are definitely not entities"""
        return {
            # Modal verbs - THIS FIXES THE "can" PROBLEM
            'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would',
            # Auxiliary verbs
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing', 'done',
            # Articles
            'a', 'an', 'the',
            # Common pronouns
            'i', 'me', 'my', 'we', 'us', 'our', 'you', 'your', 'he', 'him', 'his', 
            'she', 'her', 'it', 'its', 'they', 'them', 'their',
            'this', 'that', 'these', 'those',
            # Common location/existence words that appear in phrases
            'there', 'here', 'where', 'everywhere', 'anywhere', 'somewhere'
        }
    
    def _initialize_question_words(self) -> set:
        """Initialize question words and interrogatives"""
        return {
            'what', 'who', 'where', 'when', 'why', 'how', 'which', 'whose', 'whom'
        }
    
    def _initialize_boundary_words(self) -> set:
        """Initialize words that should not be at entity boundaries"""
        return {
            # Conjunctions and connectors
            'and', 'or', 'but', 'nor', 'for', 'so', 'yet',
            # Prepositions
            'in', 'on', 'at', 'by', 'for', 'with', 'to', 'from', 'of', 'about',
            'up', 'down', 'into', 'onto', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'under', 'over',
            # Other boundary markers
            'then', 'than', 'as', 'if', 'when', 'while', 'since', 'because'
        }
    
    async def extract_and_link(self, processed_question: ProcessedQuestion, context: ProcessingContext) -> LinkedEntities:
        """Extract and link entities from processed question"""
        self.logger.info(f"Extracting entities from: {processed_question.cleaned_text}")
        
        # Extract entities with punctuation cleaning and filtering
        extracted_entities = await self._extract_entities(processed_question)
        
        # Apply filtering to remove low-quality entities
        filtered_entities = self._clean_and_filter_entities(extracted_entities)
        
        # Link entities to URIs
        linked_entities = await self._link_entities(filtered_entities)
        
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
        """Extract entities with type classification and punctuation cleaning"""
        entities = []
        text = processed_question.original_text
        
        # Extract DOIs with punctuation cleaning - FIXES THE ? ISSUE
        for match in re.finditer(r'10\.\d+/[^\s]+', text):
            doi_text = match.group()
            # Remove trailing punctuation that's not part of the DOI
            while doi_text and doi_text[-1] in '.!?;,':
                doi_text = doi_text[:-1]
            
            if doi_text and len(doi_text) > 5:  # Ensure it's still valid
                entities.append(ExtractedEntity(
                    text=doi_text,
                    entity_type=EntityType.DOI,
                    confidence=0.95,
                    start_pos=match.start(),
                    end_pos=match.start() + len(doi_text)
                ))
        
        # Extract ORCIDs (no punctuation issues typically)
        for match in re.finditer(r'0000-\d{4}-\d{4}-\d{3}[\dX]', text):
            entities.append(ExtractedEntity(
                text=match.group(),
                entity_type=EntityType.ORCID,
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Extract URLs with punctuation cleaning - FIXES THE ? ISSUE
        for match in re.finditer(r'https?://[^\s]+', text):
            url_text = match.group()
            # Remove trailing sentence punctuation
            while url_text and url_text[-1] in '.!?;,':
                url_text = url_text[:-1]
            
            if url_text and '://' in url_text:  # Ensure it's still a valid URL
                entities.append(ExtractedEntity(
                    text=url_text,
                    entity_type=EntityType.URL,
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.start() + len(url_text)
                ))
        
        # Extract quoted strings (potential titles/names)
        for match in re.finditer(r'"([^"]+)"', text):
            quoted_text = match.group(1).strip()
            if len(quoted_text) > 1:
                entities.append(ExtractedEntity(
                    text=quoted_text,
                    entity_type=EntityType.TITLE,
                    confidence=0.8,
                    start_pos=match.start(1),
                    end_pos=match.end(1)
                ))
        
        # Extract acronyms with validation
        for match in re.finditer(r'\b[A-Z]{2,6}\b', text):
            acronym = match.group()
            if self._is_valid_acronym(acronym):
                entities.append(ExtractedEntity(
                    text=acronym,
                    entity_type=EntityType.CONCEPT,
                    confidence=0.75,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        # Extract parenthetical examples
        entities.extend(self._extract_parenthetical_examples(text))
        
        # Extract clean noun phrases
        entities.extend(self._extract_clean_noun_phrases(text))
        
        # Extract meaningful single words
        entities.extend(self._extract_meaningful_words(text))
        
        return entities
    
    def _extract_parenthetical_examples(self, text: str) -> List[ExtractedEntity]:
        """Extract examples from parentheses"""
        entities = []
        
        # Pattern for parenthetical lists: (e.g., item1, item2, item3)
        for match in re.finditer(r'\(e\.g\.,?\s*([^)]+)\)', text, re.IGNORECASE):
            examples_text = match.group(1)
            examples = [ex.strip() for ex in examples_text.split(',')]
            
            for example in examples:
                example = example.strip()
                cleaned_example = self._clean_entity_text(example)
                if cleaned_example and len(cleaned_example) > 2:
                    start_pos = text.find(example, match.start())
                    if start_pos != -1:
                        entities.append(ExtractedEntity(
                            text=cleaned_example,
                            entity_type=EntityType.CONCEPT,
                            confidence=0.8,
                            start_pos=start_pos,
                            end_pos=start_pos + len(example)
                        ))
        
        # Also handle simple parenthetical lists: (climate, socio-economic, ecological)
        for match in re.finditer(r'\(([^)]+)\)', text):
            content = match.group(1)
            if ',' in content and 'e.g.' not in content.lower() and len(content) < 100:
                items = [item.strip() for item in content.split(',')]
                if len(items) >= 2:
                    for item in items:
                        cleaned_item = self._clean_entity_text(item)
                        if cleaned_item and len(cleaned_item) > 2:
                            start_pos = text.find(item, match.start())
                            if start_pos != -1:
                                entities.append(ExtractedEntity(
                                    text=cleaned_item,
                                    entity_type=EntityType.CONCEPT,
                                    confidence=0.75,
                                    start_pos=start_pos,
                                    end_pos=start_pos + len(item)
                                ))
        
        return entities
    
    def _extract_clean_noun_phrases(self, text: str) -> List[ExtractedEntity]:
        """Extract clean noun phrases with proper boundaries"""
        entities = []
        
        # Find potential multi-word phrases (2-3 words)
        for match in re.finditer(r'\b[a-z]+(?:-[a-z]+)?\s+[a-z]+(?:-[a-z]+)?(?:\s+[a-z]+(?:-[a-z]+)?)?\b', text.lower()):
            phrase = text[match.start():match.end()]  # Preserve original case
            cleaned_phrase = self._clean_phrase_boundaries(phrase)
            
            if cleaned_phrase and self._is_meaningful_phrase(cleaned_phrase):
                entities.append(ExtractedEntity(
                    text=cleaned_phrase,
                    entity_type=EntityType.CONCEPT,
                    confidence=0.7,
                    start_pos=match.start(),
                    end_pos=match.start() + len(cleaned_phrase)
                ))
        
        return entities
    
    def _extract_meaningful_words(self, text: str) -> List[ExtractedEntity]:
        """Extract meaningful single words"""
        entities = []
        
        # Look for substantial words (4+ characters)
        for match in re.finditer(r'\b[a-z]{4,}\b', text.lower()):
            word = text[match.start():match.end()]  # Preserve original case
            if self._is_meaningful_single_word(word):
                entities.append(ExtractedEntity(
                    text=word,
                    entity_type=EntityType.CONCEPT,
                    confidence=0.6,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _clean_entity_text(self, text: str) -> str:
        """Clean entity text by removing boundary words"""
        words = text.split()
        
        # Remove boundary words from start and end
        while words and words[0].lower() in self._boundary_words:
            words = words[1:]
        
        while words and words[-1].lower() in self._boundary_words:
            words = words[:-1]
        
        return ' '.join(words)
    
    def _clean_phrase_boundaries(self, phrase: str) -> str:
        """Clean phrase boundaries by removing function words at edges"""
        words = phrase.split()
        
        # Remove function words, boundary words, AND question words from start and end
        words_to_remove = self._boundary_words | self._function_words | self._question_words
        
        # Remove from start
        while words and words[0].lower() in words_to_remove:
            words = words[1:]
        
        # Remove from end  
        while words and words[-1].lower() in words_to_remove:
            words = words[:-1]
        
        # Additional cleanup for common patterns that shouldn't be entities
        if words:
            # Remove common verb starters that slip through
            verb_starters = {'need', 'plan', 'assess', 'want', 'have', 'make', 'take', 'give'}
            while words and words[0].lower() in verb_starters:
                words = words[1:]
            
            # Remove common enders
            common_enders = {'to', 'and', 'or', 'of', 'in', 'on', 'at', 'by', 'for', 'with'}
            while words and words[-1].lower() in common_enders:
                words = words[:-1]
        
        return ' '.join(words)
    
    def _is_valid_acronym(self, text: str) -> bool:
        """Check if text is a valid acronym"""
        if text.lower() in self._question_words or text.lower() in self._function_words:
            return False
        
        common_abbrevs = {'AND', 'OR', 'BUT', 'THE', 'FOR', 'TO', 'OF', 'IN', 'ON', 'AT', 'BY'}
        if text.upper() in common_abbrevs:
            return False
        
        return True
    
    def _is_meaningful_phrase(self, phrase: str) -> bool:
        """Check if phrase is meaningful"""
        if not phrase or len(phrase) < 3:
            return False
        
        words = phrase.lower().split()
        
        if len(words) == 0:
            return False
        
        # NEVER allow phrases that start with question words
        if words[0] in self._question_words:
            return False
        
        # NEVER allow phrases that start with function words
        if words[0] in self._function_words:
            return False
        
        # Skip very generic combinations and problematic patterns
        very_generic = {
            'need to', 'plan to', 'want to', 'have to', 'able to',
            'in order', 'such as', 'as well', 'in the', 'on the',
            'and plan', 'and knowledge', 'to assess', 'to plan',
            'what data', 'what is', 'what are', 'how do', 'how can',
            'which are', 'which is', 'where are', 'when do',
            # Additional problematic patterns from your example
            'there ip', 'there is', 'there are', 'there was', 'there were',
            'already been', 'been licensed', 'already been licensed',
            'has been', 'have been', 'had been', 'will be', 'would be'
        }
        if phrase.lower() in very_generic:
            return False
        
        # Check for verb-heavy phrases that aren't good entities
        verb_indicators = ['been', 'already', 'have', 'has', 'had', 'will', 'would', 'could', 'should']
        verb_count = sum(1 for word in words if word in verb_indicators)
        if verb_count > len(words) * 0.5:  # More than 50% verb indicators
            return False
        
        # Must contain at least one substantial word (4+ chars) that's not a function word
        substantial_words = [w for w in words if len(w) >= 4 and w not in self._function_words]
        if len(substantial_words) == 0:
            return False
        
        # Don't allow phrases where more than half the words are function/boundary words
        function_and_boundary = self._function_words | self._boundary_words | self._question_words
        unwanted_count = sum(1 for w in words if w in function_and_boundary)
        if unwanted_count > len(words) * 0.4:  # Max 40% unwanted words
            return False
        
        # Additional check: if phrase contains auxiliary verbs, it's probably not a good entity
        auxiliary_verbs = {'is', 'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had'}
        if any(word in auxiliary_verbs for word in words):
            return False
        
        return True
    
    def _is_meaningful_single_word(self, word: str) -> bool:
        """Check if single word is meaningful"""
        word_lower = word.lower()
        
        # Must be at least 4 characters
        if len(word) < 4:
            return False
        
        # Not a function word
        if word_lower in self._function_words:
            return False
        
        # Not a question word
        if word_lower in self._question_words:
            return False
        
        # Not a boundary word
        if word_lower in self._boundary_words:
            return False
        
        # Not very common generic words
        very_common = {
            'need', 'want', 'have', 'make', 'take', 'come', 'give', 'know', 'think',
            'said', 'each', 'which', 'other', 'than', 'then', 'them', 'been', 'were',
            'more', 'most', 'some', 'time', 'very', 'when', 'much', 'well', 'just',
            'only', 'also', 'back', 'after', 'here', 'where', 'there', 'such',
            'work', 'find', 'help', 'call', 'move', 'live', 'feel', 'high', 'last',
            'long', 'great', 'little', 'own', 'right', 'old', 'try', 'ask', 'turn',
            'start', 'show', 'play', 'run', 'keep', 'seem', 'leave', 'hand', 'eye',
            'never', 'far', 'away', 'anything', 'may', 'still', 'should', 'another',
            'must', 'go', 'does', 'got', 'has', 'might', 'would', 'could', 'went',
            'came', 'look', 'see', 'get', 'use', 'day', 'man', 'new', 'now', 'way',
            'place', 'part', 'used', 'people', 'water', 'called', 'first', 'made',
            # Common adjectives that are rarely meaningful entities alone
            'effective', 'good', 'best', 'better', 'important', 'large', 'small',
            'different', 'possible', 'available', 'necessary', 'main', 'current',
            'recent', 'general', 'specific', 'particular', 'various', 'certain',
            'similar', 'common', 'special', 'local', 'national', 'international',
            # Additional generic words that shouldn't be entities
            'potential', 'already', 'other', 'same', 'next', 'last', 'first',
            'second', 'third', 'whole', 'full', 'real', 'total', 'final', 'complete',
            'simple', 'easy', 'hard', 'difficult', 'free', 'open', 'clear', 'sure',
            'ready', 'early', 'late', 'quick', 'slow', 'fast', 'strong', 'weak',
            # Common verbs that aren't typically entities
            'assess', 'plan', 'develop', 'create', 'provide', 'include', 'require',
            'ensure', 'support', 'maintain', 'establish', 'implement', 'improve',
            'increase', 'reduce', 'change', 'manage', 'control', 'protect', 'prevent',
            'become', 'allow', 'follow', 'continue', 'remain', 'return', 'remember',
            'consider', 'suggest', 'report', 'decide', 'expect', 'offer', 'appear',
            # Past participles and gerunds that are often not entities
            'based', 'used', 'done', 'made', 'given', 'taken', 'known', 'shown',
            'found', 'seen', 'heard', 'told', 'asked', 'learned', 'studied',
            'licensed', 'related', 'involved', 'required', 'provided', 'included'
        }
        if word_lower in very_common:
            return False
        
        # Prefer words with meaningful suffixes (more likely to be nouns/concepts)
        meaningful_suffixes = [
            'tion', 'sion', 'ment', 'ness', 'ity', 'ism', 'ics', 'ogy', 'phy', 
            'logy', 'graphy', 'ture', 'ence', 'ance', 'ency', 'ancy'
        ]
        
        # If it has a meaningful suffix, it's more likely to be a good entity
        has_meaningful_suffix = any(word_lower.endswith(suffix) for suffix in meaningful_suffixes)
        
        # For words without meaningful suffixes, be more strict about length
        if not has_meaningful_suffix and len(word) < 6:
            return False
        
        # Words that look like domain-specific terms
        if (word_lower.endswith('tion') or word_lower.endswith('sion') or 
            word_lower.endswith('ment') or word_lower.endswith('ness') or
            word_lower.endswith('ity') or word_lower.endswith('ics') or
            word_lower.endswith('ogy') or word_lower.endswith('logy')):
            return True
        
        # For longer words (7+ chars) that don't match common patterns, allow them
        if len(word) >= 7:
            return True
        
        return False
    
    def _clean_and_filter_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicates, overlaps and filter low-quality entities"""
        if not entities:
            return []
        
        # Step 1: Remove exact duplicates (same text, keep highest confidence)
        text_to_entity = {}
        for entity in entities:
            key = entity.text.lower().strip()
            if key not in text_to_entity or entity.confidence > text_to_entity[key].confidence:
                text_to_entity[key] = entity
        
        # Step 2: Remove overlapping positions (keep higher confidence)
        unique_entities = list(text_to_entity.values())
        unique_entities.sort(key=lambda e: e.start_pos)
        
        position_filtered = []
        for entity in unique_entities:
            overlaps = False
            for existing in position_filtered:
                if self._entities_overlap(entity, existing):
                    # If current entity has higher confidence, replace existing
                    if entity.confidence > existing.confidence:
                        position_filtered.remove(existing)
                        break
                    else:
                        overlaps = True
                        break
            
            if not overlaps:
                position_filtered.append(entity)
        
        # Step 3: Remove substring entities (keep longer, more specific ones)
        final_filtered = []
        for entity in position_filtered:
            is_substring = False
            for other in position_filtered:
                if (entity != other and 
                    entity.text.lower().strip() in other.text.lower().strip() and 
                    len(entity.text.strip()) < len(other.text.strip())):
                    # The current entity is a substring of another entity
                    is_substring = True
                    break
            
            if not is_substring:
                final_filtered.append(entity)
        
        # Step 4: Final deduplication by normalized text (just in case)
        final_unique = {}
        for entity in final_filtered:
            # Normalize text: lowercase, strip, collapse whitespace
            normalized_key = ' '.join(entity.text.lower().strip().split())
            if normalized_key not in final_unique or entity.confidence > final_unique[normalized_key].confidence:
                final_unique[normalized_key] = entity
        
        return list(final_unique.values())
    
    def _entities_overlap(self, entity1: ExtractedEntity, entity2: ExtractedEntity) -> bool:
        """Check if two entities overlap in text position"""
        return not (entity1.end_pos <= entity2.start_pos or entity2.end_pos <= entity1.start_pos)
    
    async def _link_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Link entities to URIs"""
        linked_entities = []
        
        for entity in entities:
            # Check cache first
            cache_key = f"{entity.entity_type.value}:{entity.text}"
            if cache_key in self._entity_cache:
                cached = self._entity_cache[cache_key]
                entity.uri = cached['uri']
                entity.label = cached['label']
                entity.aliases = cached['aliases']
                linked_entities.append(entity)
                continue
            
            # Link based on entity type
            if entity.entity_type == EntityType.DOI:
                entity.uri = f"https://doi.org/{entity.text}"
                entity.label = entity.text
            elif entity.entity_type == EntityType.ORCID:
                entity.uri = f"https://orcid.org/{entity.text}"
                entity.label = await self._get_orcid_name(entity.text)
            elif entity.entity_type == EntityType.URL:
                entity.uri = entity.text
                entity.label = entity.text
            elif entity.entity_type in [EntityType.TITLE, EntityType.CONCEPT]:
                # Try to link via external services
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
        """Get name for ORCID"""
        return orcid
    
    async def _link_via_external_services(self, text: str, entity_type: EntityType) -> Optional[Dict[str, Any]]:
        """Link entity via external services"""
        return None
    
    def _classify_entities(self, entities: List[ExtractedEntity], processed_question: ProcessedQuestion) -> Tuple[List[ExtractedEntity], List[ExtractedEntity]]:
        """Classify entities as potential subjects or objects"""
        subject_candidates = []
        object_candidates = []
        
        question_length = len(processed_question.cleaned_text)
        
        for entity in entities:
            position_ratio = entity.start_pos / question_length if question_length > 0 else 0
            
            if entity.entity_type in [EntityType.DOI, EntityType.ORCID, EntityType.URL] and entity.confidence > 0.9:
                subject_candidates.append(entity)
            elif position_ratio < 0.6:
                subject_candidates.append(entity)
            else:
                object_candidates.append(entity)
        
        return subject_candidates, object_candidates
    
    def _calculate_linking_confidence(self, entities: List[ExtractedEntity]) -> float:
        """Calculate overall linking confidence"""
        if not entities:
            return 0.0
        
        total_weighted_confidence = 0
        total_weight = 0
        
        for entity in entities:
            if entity.entity_type in [EntityType.DOI, EntityType.ORCID, EntityType.URL]:
                weight = 3
            elif entity.entity_type == EntityType.TITLE:
                weight = 2
            elif len(entity.text.split()) > 1:
                weight = 2
            else:
                weight = 1
            
            total_weighted_confidence += entity.confidence * weight
            total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0
