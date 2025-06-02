"""
Science Live Pipeline: Question Processing
==========================================

First step of the pipeline that parses and preprocesses natural language questions.

Responsibilities:
- Clean and normalize input text
- Classify question type (what, who, where, etc.)
- Extract key phrases and potential entities
- Assess intent confidence

Author: Science Live Team
Version: 1.0.0
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from .common import (
    ProcessedQuestion, ProcessingContext, QuestionType, 
    PipelineStep, validate_processing_context
)

__all__ = ['QuestionProcessor']

class QuestionProcessor(PipelineStep):
    """
    Parse and preprocess natural language questions.
    
    This is the first step in the pipeline that takes raw natural language
    questions and prepares them for entity extraction and further processing.
    
    Features:
    - Question type classification
    - Text cleaning and normalization
    - Key phrase extraction
    - Potential entity identification
    - Intent confidence assessment
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._question_patterns = self._initialize_patterns()
        self._stop_words = self._initialize_stop_words()
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialize question type classification patterns"""
        return {
            QuestionType.WHAT.value: [
                r'\bwhat\b', r'\bwhich\b', r'\bdefine\b', r'\bexplain\b'
            ],
            QuestionType.WHO.value: [
                r'\bwho\b', r'\bwhom\b', r'\bwhose\b',  # Simple - include all "who" questions
                r'\bauthor(?:ed)?\s+by\b',  # "authored by" or "author by"  
                r'\bwritten\s+by\b',  # "written by"
                r'\bcreated\s+by\b'   # "created by"
            ],
            QuestionType.WHERE.value: [
                r'\bwhere\b', r'\blocation\b', r'\blocated\b'
            ],
            QuestionType.WHEN.value: [
                r'\bwhen\b', r'\bdate\b', r'\btime\b', r'\byear\b'
            ],
            QuestionType.HOW.value: [
                r'\bhow\b(?!\s+many)', r'\bmethod\b', r'\bprocess\b'
            ],
            QuestionType.WHY.value: [
                r'\bwhy\b', r'\breason\b', r'\bcause\b'
            ],
            QuestionType.LIST.value: [
                r'\blist\b', r'\bshow\s+(?:me\s+)?all\b', r'\bfind\s+all\b', 
                r'\bdisplay\s+all\b', r'\benumerate\b', r'\bidentify\s+all\b',
                r'\ball\s+\w+\s+by\b', r'papers\s+by\b'  # "papers by" indicates listing
            ],
            QuestionType.COUNT.value: [
                r'\bhow many\b', r'\bcount\b', r'\bnumber of\b',
                r'\bquantity\b', r'\bamount\b'
            ]
        }
    
    def _initialize_stop_words(self) -> set:
        """Initialize stop words for key phrase extraction"""
        return {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'must', 'shall',
            'of', 'in', 'on', 'at', 'by', 'for', 'with', 'to', 'from',
            'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'under', 'over'
        }
    
    async def process(self, question: str, context: ProcessingContext) -> ProcessedQuestion:
        """
        Process natural language question.
        
        Args:
            question: Raw natural language question
            context: Processing context with user info and preferences
            
        Returns:
            ProcessedQuestion with classified and preprocessed information
            
        Raises:
            ValueError: If question is empty or invalid
        """
        if not validate_processing_context(context):
            raise ValueError("Invalid processing context")
        
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        self.logger.info(f"Processing question: {question}")
        
        # Clean the question
        cleaned = self._clean_question(question)
        
        # Check if cleaned question is empty or only punctuation
        if not cleaned or not cleaned.strip() or re.match(r'^[?!.\s]*$', cleaned):
            raise ValueError("Question cannot be empty")


        # Classify question type and assess confidence
        q_type, confidence = self._classify_question_type(cleaned)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(cleaned)
        
        # Identify potential entities
        potential_entities = self._identify_potential_entities(cleaned)
        
        # Create result
        result = ProcessedQuestion(
            original_text=question,
            cleaned_text=cleaned,
            question_type=q_type,
            key_phrases=key_phrases,
            potential_entities=potential_entities,
            intent_confidence=confidence,
            processing_metadata=self.get_step_metadata()
        )
        
        self.logger.info(
            f"Question classified as: {q_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        
        return result
    
    def _clean_question(self, question: str) -> str:
        """Clean and normalize the question text"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', question.strip())
        
        # Normalize punctuation
        cleaned = re.sub(r'[?!.]+$', '?', cleaned)

        # Check if question is only punctuation (treat as empty)
        if re.match(r'^[?!.\s]*$', cleaned):
            return ""  # Treat punctuation-only as empty

        
        # Ensure question ends with question mark if it's interrogative
        if not cleaned.endswith('?') and self._is_interrogative(cleaned):
            cleaned += '?'
        
        return cleaned
    
    def _is_interrogative(self, text: str) -> bool:
        """Check if text is an interrogative sentence"""
        interrogative_words = [
            'what', 'who', 'where', 'when', 'why', 'how', 'which',
            'whose', 'whom', 'do', 'does', 'did', 'can', 'could',
            'will', 'would', 'should', 'is', 'are', 'was', 'were'
        ]
        
        first_word = text.lower().split()[0] if text.split() else ''
        return first_word in interrogative_words
    
    def _classify_question_type(self, question: str) -> Tuple[QuestionType, float]:
        """Classify the type of question and assess confidence"""
        question_lower = question.lower()
        
        # Score each question type
        scores = {}
        for q_type, patterns in self._question_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, question_lower))
                score += matches * 2  # Weight multiple matches
            
            if score > 0:
                scores[q_type] = score
        
            # Special handling for common conflicts
        if 'list' in scores and 'who' in scores:
            # If we have both LIST and WHO patterns, prefer LIST for "papers by" type questions
            if re.search(r'(?:list|show|find|all)\s+.*(?:papers|work|publications)\s+by\b', question_lower):
                scores['list'] = scores.get('list', 0) + 3  # Boost LIST score

        if not scores:
            return QuestionType.GENERAL, 0.5
        
        # Get best match
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        
        # Calculate confidence based on score and competing alternatives
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.5
        
        # Adjust confidence based on pattern clarity
        if max_score >= 4:  # Very clear indicators
            confidence = min(confidence * 1.2, 1.0)
        elif max_score == 1:  # Weak indicators
            confidence = max(confidence * 0.8, 0.3)
        
        return QuestionType(best_type), confidence
    
    def _extract_key_phrases(self, question: str) -> List[str]:
        """Extract key phrases from the question"""
        # Tokenize and clean
        words = re.findall(r'\b\w+\b', question.lower())
        
        # Remove stop words and short words
        key_words = [
            word for word in words 
            if word not in self._stop_words and len(word) > 2
        ]
        
        # Extract noun phrases (simplified approach)
        # In production, would use NLP libraries like spaCy
        phrases = []
        
        # Single significant words
        phrases.extend(key_words)
        
        # Bigrams of significant words
        for i in range(len(key_words) - 1):
            phrases.append(f"{key_words[i]} {key_words[i+1]}")
        
        # Trigrams for very specific concepts
        for i in range(len(key_words) - 2):
            phrases.append(f"{key_words[i]} {key_words[i+1]} {key_words[i+2]}")
        
        # Remove duplicates and sort by length (longer phrases first)
        unique_phrases = list(set(phrases))
        unique_phrases.sort(key=len, reverse=True)
        
        # Return top phrases
        return unique_phrases[:10]
    
    def _identify_potential_entities(self, question: str) -> List[str]:
        """Identify potential entities in the question"""
        entities = []
        
        # DOI pattern
        doi_matches = re.findall(r'10\.\d+/[^\s]+', question)
        entities.extend(doi_matches)
        
        # ORCID pattern
        orcid_matches = re.findall(r'0000-\d{4}-\d{4}-\d{3}[\dX]', question)
        entities.extend(orcid_matches)
        
        # URL pattern
        url_matches = re.findall(r'https?://[^\s]+', question)
        entities.extend(url_matches)
        
        # Quoted strings (potential titles, names)
        quoted_matches = re.findall(r'"([^"]+)"', question)
        entities.extend(quoted_matches)
        
        # Single quoted strings
        single_quoted_matches = re.findall(r"'([^']+)'", question)
        entities.extend(single_quoted_matches)
        
        # Capitalized phrases (potential proper nouns)
        # Look for sequences of capitalized words
        cap_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        cap_matches = re.findall(cap_pattern, question)
        
        # Filter out question words and common false positives
        question_words = {
            'What', 'Who', 'Where', 'When', 'How', 'Why', 'Which',
            'The', 'This', 'That', 'These', 'Those'
        }
        
        filtered_caps = [
            match for match in cap_matches 
            if match not in question_words and len(match.split()) <= 4
        ]
        entities.extend(filtered_caps)
        
        # Numbers (potential measurements, years, etc.)
        number_matches = re.findall(r'\b\d+(?:\.\d+)?\b', question)
        entities.extend(number_matches)
        
        # Scientific terms (simplified - would use domain-specific dictionaries)
        scientific_pattern = r'\b[a-z]+(?:-[a-z]+)*(?:\s+[a-z]+(?:-[a-z]+)*)*\b'
        potential_terms = re.findall(scientific_pattern, question.lower())
        
        # Filter for likely scientific terms (contains common scientific suffixes)
        scientific_suffixes = ['tion', 'sion', 'ment', 'ness', 'ity', 'ism', 'ics']
        scientific_entities = [
            term for term in potential_terms
            if any(term.endswith(suffix) for suffix in scientific_suffixes)
            and len(term) > 5
        ]
        entities.extend(scientific_entities[:5])  # Limit scientific terms
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)
        
        return unique_entities
    
    def get_question_complexity(self, processed_question: ProcessedQuestion) -> int:
        """
        Assess question complexity on a 1-5 scale.
        
        Args:
            processed_question: The processed question to analyze
            
        Returns:
            Complexity score from 1 (simple) to 5 (very complex)
        """
        complexity = 1
        
        # Increase complexity based on question length
        word_count = len(processed_question.cleaned_text.split())
        if word_count > 20:
            complexity += 2
        elif word_count > 10:
            complexity += 1
        
        # Increase complexity based on number of entities
        entity_count = len(processed_question.potential_entities)
        if entity_count > 5:
            complexity += 2
        elif entity_count > 2:
            complexity += 1
        
        # Increase complexity for compound questions
        if ' and ' in processed_question.cleaned_text.lower():
            complexity += 1
        if ' or ' in processed_question.cleaned_text.lower():
            complexity += 1
        
        # Decrease complexity for very confident question type classification
        if processed_question.intent_confidence > 0.9:
            complexity = max(1, complexity - 1)
        
        return min(complexity, 5)
    
    def suggest_improvements(self, processed_question: ProcessedQuestion) -> List[str]:
        """
        Suggest improvements to make the question more processable.
        
        Args:
            processed_question: The processed question to analyze
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Low confidence suggestions
        if processed_question.intent_confidence < 0.6:
            suggestions.append(
                "Consider rephrasing your question to be more specific"
            )
        
        # No entities found
        if not processed_question.potential_entities:
            suggestions.append(
                "Include specific identifiers like DOI, ORCID, or paper titles"
            )
        
        # Very long question
        if len(processed_question.cleaned_text.split()) > 25:
            suggestions.append(
                "Try breaking your question into smaller, more focused parts"
            )
        
        # Very short question
        if len(processed_question.cleaned_text.split()) < 3:
            suggestions.append(
                "Provide more context or specific details in your question"
            )
        
        # Question type specific suggestions
        if processed_question.question_type == QuestionType.GENERAL:
            suggestions.append(
                "Use question words like 'what', 'who', 'where' for better results"
            )
        
        return suggestions


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_valid_question(question: str) -> bool:
    """Check if a question is valid for processing"""
    if not question or not question.strip():
        return False
    
    # Check minimum length
    if len(question.strip()) < 3:
        return False
    
    # Check for obvious non-questions
    spam_indicators = ['buy now', 'click here', 'free offer', '$$$']
    question_lower = question.lower()
    if any(indicator in question_lower for indicator in spam_indicators):
        return False
    
    return True

def preprocess_question_batch(questions: List[str]) -> List[str]:
    """Preprocess a batch of questions"""
    return [q.strip() for q in questions if is_valid_question(q)]


# ============================================================================
# VERSION INFO
# ============================================================================

__version__ = "1.0.0"
__author__ = "Science Live Team"
__description__ = "Question processing step for Science Live pipeline"
