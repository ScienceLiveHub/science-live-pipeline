"""
Science Live Pipeline: Common Data Models
=========================================

Shared data structures used throughout the steps of the Science Live processing pipeline.
All pipeline steps import from this module to ensure consistent data flow.

Author: Science Live Team
Version: 0.0.1
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import asyncio
from datetime import datetime

__all__ = [
    'ProcessingContext',
    'ProcessedQuestion', 
    'ExtractedEntity',
    'LinkedEntities',
    'RosettaStatement',
    'GeneratedStatements',
    'SPARQLQuery',
    'GeneratedQueries',
    'QueryResults',
    'StructuredResult',
    'ProcessedResults',
    'NaturalLanguageResult',
    'EntityType',
    'QuestionType',
    'ConfidenceLevel'
]

# ============================================================================
# ENUMS
# ============================================================================

class EntityType(Enum):
    """Types of entities that can be extracted"""
    DOI = "doi"
    ORCID = "orcid"
    URL = "url"
    PERSON = "person"
    CONCEPT = "concept"
    TITLE = "title"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    NUMBER = "number"
    UNKNOWN = "unknown"

class QuestionType(Enum):
    """Types of questions"""
    WHAT = "what"
    WHO = "who" 
    WHERE = "where"
    WHEN = "when"
    HOW = "how"
    WHY = "why"
    LIST = "list"
    COUNT = "count"
    GENERAL = "general"

class ConfidenceLevel(Enum):
    """Confidence levels for processing results"""
    HIGH = "high"      # >= 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5

# ============================================================================
# PIPELINE CONTEXT
# ============================================================================

@dataclass
class ProcessingContext:
    """Context passed through the entire pipeline"""
    original_question: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    debug_mode: bool = False
    start_time: float = field(default_factory=lambda: time.perf_counter())  # Use perf_counter for consistent timing
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since pipeline started"""
        return time.perf_counter() - self.start_time

# ============================================================================
# STEP 1: QUESTION PROCESSING
# ============================================================================

@dataclass
class ProcessedQuestion:
    """Output of question processing step"""
    original_text: str
    cleaned_text: str
    question_type: QuestionType
    key_phrases: List[str]
    potential_entities: List[str]
    intent_confidence: float
    language: str = 'en'
    processing_metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# STEP 2: ENTITY EXTRACTION
# ============================================================================

@dataclass
class ExtractedEntity:
    """An entity extracted from the question"""
    text: str
    entity_type: EntityType
    confidence: float
    start_pos: int
    end_pos: int
    uri: Optional[str] = None
    label: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_sparql_value(self) -> str:
        """Convert entity to SPARQL representation"""
        if self.uri:
            return f"<{self.uri}>"
        elif self.entity_type == EntityType.NUMBER:
            return str(self.text)
        elif self.entity_type == EntityType.DATE:
            return f'"{self.text}"^^xsd:date'
        else:
            return f'"{self.text}"'

@dataclass
class LinkedEntities:
    """Output of entity extraction and linking"""
    entities: List[ExtractedEntity]
    subject_candidates: List[ExtractedEntity]
    object_candidates: List[ExtractedEntity]
    linking_confidence: float
    linking_metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# STEP 3: ROSETTA STATEMENT GENERATION
# ============================================================================

@dataclass
class RosettaStatement:
    """A structured Rosetta statement"""
    subject: ExtractedEntity
    statement_type_uri: str
    statement_type_label: str
    
    # Object positions (up to 4 as per Rosetta template)
    required_object1: Optional[ExtractedEntity] = None
    optional_object1: Optional[ExtractedEntity] = None
    optional_object2: Optional[ExtractedEntity] = None
    optional_object3: Optional[ExtractedEntity] = None
    
    # Metadata
    dynamic_label_template: Optional[str] = None
    confidence_level: Optional[float] = None
    context: Optional[str] = None
    is_negation: bool = False
    source_references: List[str] = field(default_factory=list)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_natural_language(self) -> str:
        """Convert back to natural language using dynamic label template"""
        if not self.dynamic_label_template:
            return f"{self.subject.label or self.subject.text} {self.statement_type_label}"
        
        result = self.dynamic_label_template
        result = result.replace("SUBJECT", self.subject.label or self.subject.text)
        
        objects = [self.required_object1, self.optional_object1, 
                  self.optional_object2, self.optional_object3]
        
        for i, obj in enumerate(objects, 1):
            if obj:
                placeholder = f"OBJECT{i}"
                result = result.replace(placeholder, obj.label or obj.text)
        
        # Clean up remaining placeholders
        import re
        result = re.sub(r'(OBJECT[0-9]+|SUBJECT)', '', result)
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result

@dataclass
class GeneratedStatements:
    """Output of Rosetta statement generation"""
    statements: List[RosettaStatement]
    generation_confidence: float
    alternative_interpretations: List[RosettaStatement] = field(default_factory=list)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# STEP 4: SPARQL GENERATION
# ============================================================================

@dataclass
class SPARQLQuery:
    """Generated SPARQL query"""
    query_text: str
    query_type: str  # 'SELECT', 'ASK', 'CONSTRUCT'
    estimated_complexity: int  # 1-5 scale
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GeneratedQueries:
    """Output of SPARQL generation"""
    primary_query: SPARQLQuery
    fallback_queries: List[SPARQLQuery] = field(default_factory=list)
    generation_method: str = 'rosetta_template'
    generation_metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# STEP 5: QUERY EXECUTION
# ============================================================================

@dataclass
class QueryResults:
    """Raw results from SPARQL execution"""
    success: bool
    results: List[Dict[str, Any]]
    query_used: str
    execution_time: float
    total_results: int
    error_message: Optional[str] = None
    execution_metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# STEP 6: RESULT PROCESSING
# ============================================================================

@dataclass
class StructuredResult:
    """A single structured result"""
    nanopub_uri: str
    statement_uri: Optional[str] = None
    rosetta_statement: Optional[RosettaStatement] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessedResults:
    """Output of result processing"""
    results: List[StructuredResult]
    total_found: int
    processing_confidence: float
    groupings: Dict[str, List[StructuredResult]] = field(default_factory=dict)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# STEP 7: NATURAL LANGUAGE GENERATION
# ============================================================================

@dataclass
class NaturalLanguageResult:
    """Final natural language output"""
    summary: str
    detailed_results: List[str]
    confidence_explanation: str
    suggestions: List[str]
    execution_summary: Dict[str, Any]
    generation_metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_confidence_level(confidence: float) -> ConfidenceLevel:
    """Convert numeric confidence to confidence level enum"""
    if confidence >= 0.8:
        return ConfidenceLevel.HIGH
    elif confidence >= 0.5:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW

def merge_metadata(*metadata_dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple metadata dictionaries"""
    result = {}
    for metadata in metadata_dicts:
        if metadata:
            result.update(metadata)
    return result

# ============================================================================
# ABSTRACT BASE CLASSES
# ============================================================================

class PipelineStep(ABC):
    """Abstract base class for all pipeline steps"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.step_name = self.__class__.__name__
    
    @abstractmethod
    async def process(self, input_data: Any, context: ProcessingContext) -> Any:
        """Process input data and return output for next step"""
        pass
    
    def get_step_metadata(self) -> Dict[str, Any]:
        """Get metadata about this pipeline step"""
        return {
            'step_name': self.step_name,
            'config': self.config,
            'version': '1.0.0'
        }

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_processing_context(context: ProcessingContext) -> bool:
    """Validate processing context"""
    # Allow empty questions to pass validation - they should be handled gracefully
    # The pipeline should handle empty questions in the question processor step
    if not hasattr(context, 'original_question'):
        return False
    return True

def validate_extracted_entity(entity: ExtractedEntity) -> bool:
    """Validate extracted entity"""
    if not entity.text or entity.confidence < 0 or entity.confidence > 1:
        return False
    if entity.start_pos < 0 or entity.end_pos < entity.start_pos:
        return False
    return True

def validate_rosetta_statement(statement: RosettaStatement) -> bool:
    """Validate Rosetta statement"""
    if not statement.subject or not statement.statement_type_uri:
        return False
    if not validate_extracted_entity(statement.subject):
        return False
    return True

def validate_sparql_query(query: SPARQLQuery) -> bool:
    """Validate SPARQL query"""
    if not query.query_text or not query.query_type:
        return False
    if query.estimated_complexity < 1 or query.estimated_complexity > 5:
        return False
    return True

# ============================================================================
# VERSION INFO
# ============================================================================

__version__ = "1.0.0"
__author__ = "Science Live Team"
__description__ = "Common data models for Science Live pipeline"
