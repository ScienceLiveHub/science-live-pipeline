"""
Entity Extractor for Science Live Pipeline - Step 2 of 7
========================================================

"""

from typing import Dict, List, Optional, Any, Tuple
import re
import logging

from .common import (
    ExtractedEntity, 
    LinkedEntities, 
    ProcessedQuestion, 
    ProcessingContext, 
    EntityType
)

class EntityExtractorLinker:
    """Step 2: Extract scientific entities from questions"""
    
    def __init__(self, endpoint_manager, config: Dict[str, Any] = None):
        self.endpoint_manager = endpoint_manager
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def extract_and_link(self, processed_question: ProcessedQuestion, context: ProcessingContext) -> LinkedEntities:
        """Extract entities from the processed question"""
        self.logger.info(f"Extracting entities from: {processed_question.cleaned_text}")
        
        entities = self._extract_entities(processed_question.original_text)
        subject_candidates, object_candidates = self._classify_entities(entities, processed_question)
        linking_confidence = self._calculate_extraction_confidence(entities)
        
        result = LinkedEntities(
            entities=entities,
            subject_candidates=subject_candidates,
            object_candidates=object_candidates,
            linking_confidence=linking_confidence
        )
        
        self.logger.info(f"Extracted {len(entities)} entities with confidence {linking_confidence:.2f}")
        return result
    
    def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract all potential entities from text"""
        entities = []
        used_positions = set()
        
        # Extract structured identifiers
        structured_entities = self._extract_structured_identifiers(text)
        entities.extend(structured_entities)
        for entity in structured_entities:
            used_positions.update(range(entity.start_pos, entity.end_pos))
        
        # Extract quoted strings
        quoted_entities = self._extract_quoted_strings(text, used_positions)
        entities.extend(quoted_entities)
        for entity in quoted_entities:
            used_positions.update(range(entity.start_pos, entity.end_pos))
        
        # Extract technical concepts
        concept_entities = self._extract_technical_concepts(text, used_positions)
        entities.extend(concept_entities)
        
        return entities
    
    def _extract_structured_identifiers(self, text: str) -> List[ExtractedEntity]:
        """Extract DOIs, ORCIDs, URLs - FIXED to handle trailing punctuation"""
        entities = []
        
        # DOIs - extract and clean trailing punctuation
        for match in re.finditer(r'10\.\d+/[^\s]+', text):
            original_text = match.group()
            # Remove trailing punctuation (?, !, ., ,, ;)
            cleaned_text = re.sub(r'[?!.,;]+$', '', original_text)
            
            if cleaned_text:  # Make sure we still have text after cleaning
                entities.append(ExtractedEntity(
                    text=cleaned_text,
                    entity_type=EntityType.DOI,
                    confidence=0.95,
                    start_pos=match.start(),
                    end_pos=match.start() + len(cleaned_text),
                    uri=f"https://doi.org/{cleaned_text}"
                ))
        
        # ORCIDs - these usually don't have trailing punctuation issues
        for match in re.finditer(r'0000-\d{4}-\d{4}-\d{3}[\dX]', text):
            entities.append(ExtractedEntity(
                text=match.group(),
                entity_type=EntityType.ORCID,
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end(),
                uri=f"https://orcid.org/{match.group()}"
            ))
        
        # URLs - extract and clean trailing punctuation
        for match in re.finditer(r'https?://[^\s]+', text):
            original_text = match.group()
            # Remove trailing punctuation
            cleaned_text = re.sub(r'[?!.,;]+$', '', original_text)
            
            if cleaned_text:  # Make sure we still have text after cleaning
                entities.append(ExtractedEntity(
                    text=cleaned_text,
                    entity_type=EntityType.URL,
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.start() + len(cleaned_text),
                    uri=cleaned_text
                ))
        
        return entities
    
    def _extract_quoted_strings(self, text: str, used_positions: set) -> List[ExtractedEntity]:
        """Extract quoted strings"""
        entities = []
        
        for match in re.finditer(r'"([^"]+)"', text):
            start_pos = match.start(1)
            end_pos = match.end(1)
            
            if not any(pos in used_positions for pos in range(start_pos, end_pos)):
                entities.append(ExtractedEntity(
                    text=match.group(1),
                    entity_type=EntityType.TITLE,
                    confidence=0.8,
                    start_pos=start_pos,
                    end_pos=end_pos
                ))
        
        return entities
    
    def _extract_technical_concepts(self, text: str, used_positions: set) -> List[ExtractedEntity]:
        """Extract technical concepts"""
        entities = []
        pattern = r'\b[A-Za-z][A-Za-z0-9]*(?:[A-Z][a-z]*|[0-9]+)*(?:[-_][A-Za-z0-9]+)*\b'
        
        for match in re.finditer(pattern, text):
            term = match.group()
            start_pos = match.start()
            end_pos = match.end()
            
            if (any(pos in used_positions for pos in range(start_pos, end_pos)) or
                self._is_common_word(term)):
                continue
            
            confidence = self._calculate_concept_confidence(term)
            
            if confidence >= 0.5:
                entities.append(ExtractedEntity(
                    text=term,
                    entity_type=EntityType.CONCEPT,
                    confidence=confidence,
                    start_pos=start_pos,
                    end_pos=end_pos
                ))
        
        return entities
    
    def _is_common_word(self, term: str) -> bool:
        """Filter common words"""
        common_words = {
            'what', 'who', 'where', 'when', 'how', 'why', 'which',
            'papers', 'research', 'study', 'work', 'data', 'results',
            'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were'
        }
        return len(term) < 3 or term.lower() in common_words
    
    def _calculate_concept_confidence(self, term: str) -> float:
        """Calculate concept confidence"""
        confidence = 0.5
        if any(c.isupper() for c in term[1:]):
            confidence += 0.2
        if any(c.isdigit() for c in term):
            confidence += 0.15
        if len(term) >= 6:
            confidence += 0.1
        return min(confidence, 0.9)
    
    def _classify_entities(self, entities: List[ExtractedEntity], processed_question: ProcessedQuestion) -> Tuple[List[ExtractedEntity], List[ExtractedEntity]]:
        """Classify as subjects/objects"""
        subject_candidates = []
        object_candidates = []
        
        question_length = len(processed_question.cleaned_text)
        
        for entity in entities:
            position_ratio = entity.start_pos / question_length if question_length > 0 else 0
            
            if position_ratio < 0.6:
                subject_candidates.append(entity)
            else:
                object_candidates.append(entity)
            
            if (entity.confidence >= 0.8 and entity not in subject_candidates):
                subject_candidates.append(entity)
        
        return subject_candidates, object_candidates
    
    def _calculate_extraction_confidence(self, entities: List[ExtractedEntity]) -> float:
        """Calculate overall confidence"""
        if not entities:
            return 0.0
        
        total_confidence = sum(entity.confidence for entity in entities)
        return total_confidence / len(entities)


# Quick test function to debug
def test_extraction():
    """Test function to debug entity extraction"""
    extractor = EntityExtractorLinker(None)
    
    test_cases = [
        "What cites 10.1038/nature12373?",
        "What about https://example.org/paper?",
        'Papers by "AlexNet" and FAIR2Adapt'
    ]
    
    for test_text in test_cases:
        print(f"\nTesting: '{test_text}'")
        entities = extractor._extract_structured_identifiers(test_text)
        for entity in entities:
            print(f"  Found: '{entity.text}' ({entity.entity_type.value})")

if __name__ == "__main__":
    test_extraction()
