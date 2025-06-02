"""
Science Live Pipeline: Main Pipeline Orchestrator
=================================================

Main pipeline class that orchestrates all 7 processing steps to convert
natural language questions into structured scientific knowledge exploration.

This module provides the high-level ScienceLivePipeline class that users
interact with, coordinating all pipeline steps from question processing
to natural language response generation.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any

from .common import (
    ProcessingContext, 
    NaturalLanguageResult, 
    validate_processing_context
)
from .question_processor import QuestionProcessor
from .entity_extractor import EntityExtractorLinker
from .rosetta_generator import RosettaStatementGenerator
from .sparql_generator import SPARQLGenerator
from .query_executor import QueryExecutor
from .result_processor import ResultProcessor
from .nl_generator import NaturalLanguageGenerator


class ScienceLivePipeline:
    """
    Main pipeline that orchestrates all 7 processing steps.
    
    This class provides a high-level interface for processing natural language
    questions through the complete pipeline from question processing to
    natural language response generation.
    
    Pipeline Steps:
    1. QuestionProcessor - Parse and classify questions
    2. EntityExtractorLinker - Extract and link entities
    3. RosettaStatementGenerator - Generate Rosetta statements
    4. SPARQLGenerator - Convert to SPARQL queries
    5. QueryExecutor - Execute queries against nanopub endpoints
    6. ResultProcessor - Structure and group results
    7. NaturalLanguageGenerator - Generate natural language responses
    
    Example:
        from science_live.core import EndpointManager
        from science_live.pipeline import ScienceLivePipeline
        
        endpoint_manager = EndpointManager()
        pipeline = ScienceLivePipeline(endpoint_manager)
        
        result = await pipeline.process("What papers cite AlexNet?")
        print(result.summary)
    """
    
    def __init__(self, endpoint_manager, config: Dict[str, Any] = None):
        """
        Initialize the Science Live pipeline.
        
        Args:
            endpoint_manager: EndpointManager instance for nanopub connections
            config: Optional configuration dictionary for pipeline components
        """
        self.endpoint_manager = endpoint_manager
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize all pipeline steps with their respective configurations
        self.question_processor = QuestionProcessor(
            self.config.get('question_processor', {})
        )
        
        self.entity_extractor = EntityExtractorLinker(
            endpoint_manager, 
            self.config.get('entity_extractor', {})
        )
        
        self.rosetta_generator = RosettaStatementGenerator(
            self.config.get('rosetta_generator', {})
        )
        
        self.sparql_generator = SPARQLGenerator(
            self.config.get('sparql_generator', {})
        )
        
        self.query_executor = QueryExecutor(
            endpoint_manager, 
            self.config.get('query_executor', {})
        )
        
        self.result_processor = ResultProcessor(
            self.config.get('result_processor', {})
        )
        
        self.nl_generator = NaturalLanguageGenerator(
            self.config.get('nl_generator', {})
        )
        
        self.logger.info("Science Live pipeline initialized")
    
    async def process(
        self, 
        question: str, 
        user_id: Optional[str] = None, 
        **kwargs
    ) -> NaturalLanguageResult:
        """
        Process a natural language question through the complete pipeline.
        
        Args:
            question: Natural language question to process
            user_id: Optional user identifier for personalization
            **kwargs: Additional context parameters (session_id, preferences, etc.)
            
        Returns:
            NaturalLanguageResult containing summary, detailed results, 
            confidence explanation, and suggestions
            
        Raises:
            ValueError: If question is invalid or context is malformed
            Exception: For pipeline processing errors (handled gracefully)
        """
        # Create processing context
        context = ProcessingContext(
            original_question=question,
            user_id=user_id,
            debug_mode=self.config.get('debug', False),
            preferences=kwargs.get('preferences', {}),
            **{k: v for k, v in kwargs.items() if k != 'preferences'}
        )
        
        # Validate context
        if not validate_processing_context(context):
            raise ValueError("Invalid processing context")
        
        self.logger.info(f"Starting pipeline processing for: {question}")
        
        try:
            # Step 1: Process and classify the question
            self.logger.debug("Step 1: Processing question")
            processed_question = await self.question_processor.process(question, context)
            self.logger.debug(f"Question classified as: {processed_question.question_type.value}")
            
            # Step 2: Extract and link entities from the question
            self.logger.debug("Step 2: Extracting and linking entities")
            linked_entities = await self.entity_extractor.extract_and_link(
                processed_question, context
            )
            self.logger.debug(f"Found {len(linked_entities.entities)} entities")
            
            # Step 3: Generate Rosetta statements from entities and question
            self.logger.debug("Step 3: Generating Rosetta statements")
            generated_statements = await self.rosetta_generator.generate(
                linked_entities, processed_question, context
            )
            self.logger.debug(f"Generated {len(generated_statements.statements)} statements")
            
            # Step 4: Convert Rosetta statements to SPARQL queries
            self.logger.debug("Step 4: Generating SPARQL queries")
            generated_queries = await self.sparql_generator.generate(
                generated_statements, context
            )
            self.logger.debug(
                f"Generated 1 primary + {len(generated_queries.fallback_queries)} fallback queries"
            )
            
            # Step 5: Execute SPARQL queries against nanopub endpoints
            self.logger.debug("Step 5: Executing queries")
            query_results = await self.query_executor.execute(
                generated_queries, context
            )
            self.logger.debug(f"Query execution: {query_results.total_results} results")
            
            # Step 6: Process and structure raw query results
            self.logger.debug("Step 6: Processing results")
            processed_results = await self.result_processor.process(
                query_results, generated_statements, context
            )
            self.logger.debug(f"Processed {processed_results.total_found} structured results")
            
            # Step 7: Generate natural language response
            self.logger.debug("Step 7: Generating natural language response")
            final_result = await self.nl_generator.generate(
                processed_results, context
            )
            
            # Log successful completion
            execution_time = context.get_elapsed_time()
            self.logger.info(f"Pipeline completed successfully in {execution_time:.2f}s")
            
            return final_result
        except ValueError as e:
            # Handle validation errors specifically
            execution_time = context.get_elapsed_time()
            self.logger.error(f"Validation error after {execution_time:.2f}s: {str(e)}")
        
            return NaturalLanguageResult(
                summary=f"Error processing question: {str(e)}",
                detailed_results=[],
                confidence_explanation="Question validation failed",
                suggestions=[
                    "Please provide a valid question",
                    "Check that your question is not empty",
                    "Try rephrasing your question",
                    "Include specific terms or concepts"
                ],
                execution_summary={
                    'error': str(e),
                    'error_type': 'ValidationError',
                    'total_execution_time': execution_time,
                    'pipeline_steps_completed': 0,
                    'debug_mode': context.debug_mode
                }
            )
        
        except Exception as e:
            # Handle pipeline errors gracefully
            execution_time = context.get_elapsed_time()
            self.logger.error(f"Pipeline failed after {execution_time:.2f}s: {str(e)}")
            
            # Return error response instead of crashing
            return NaturalLanguageResult(
                summary=f"Error processing question: {str(e)}",
                detailed_results=[],
                confidence_explanation="Pipeline processing failed",
                suggestions=[
                    "Please try rephrasing your question",
                    "Check for typos or unusual formatting",
                    "Try a simpler version of your question",
                    "Include specific identifiers like DOI or ORCID if available"
                ],
                execution_summary={
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'total_execution_time': execution_time,
                    'pipeline_steps_completed': 0,
                    'debug_mode': context.debug_mode
                }
            )
    
    async def process_batch(
        self, 
        questions: List[str], 
        user_id: Optional[str] = None,
        **kwargs
    ) -> List[NaturalLanguageResult]:
        """
        Process multiple questions in batch mode.
        
        Args:
            questions: List of natural language questions
            user_id: Optional user identifier
            **kwargs: Additional context parameters
            
        Returns:
            List of NaturalLanguageResult objects, one per question
            
        Note:
            Questions are processed concurrently for better performance.
            Failed questions return error responses rather than exceptions.
        """
        self.logger.info(f"Starting batch processing of {len(questions)} questions")
        
        # Create tasks for concurrent processing
        tasks = [
            self.process(question, user_id=user_id, **kwargs) 
            for question in questions
        ]
        
        # Execute all tasks concurrently, handling exceptions gracefully
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch question {i} failed: {str(result)}")
                processed_results.append(
                    NaturalLanguageResult(
                        summary=f"Error processing question: {str(result)}",
                        detailed_results=[],
                        confidence_explanation="Batch processing failed for this question",
                        suggestions=["Try processing this question individually"],
                        execution_summary={
                            'error': str(result),
                            'batch_index': i,
                            'total_execution_time': 0
                        }
                    )
                )
            else:
                processed_results.append(result)
        
        self.logger.info(f"Batch processing completed: {len(processed_results)} results")
        return processed_results
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the pipeline configuration and status.
        
        Returns:
            Dictionary containing pipeline information
        """
        return {
            'pipeline_version': '1.0.0',
            'steps': [
                'QuestionProcessor',
                'EntityExtractorLinker', 
                'RosettaStatementGenerator',
                'SPARQLGenerator',
                'QueryExecutor',
                'ResultProcessor',
                'NaturalLanguageGenerator'
            ],
            'endpoints': self.endpoint_manager.list_endpoints(),
            'default_endpoint': self.endpoint_manager.default_endpoint,
            'config': {
                'debug_mode': self.config.get('debug', False),
                'component_configs': {
                    component: bool(self.config.get(component))
                    for component in [
                        'question_processor', 'entity_extractor', 'rosetta_generator',
                        'sparql_generator', 'query_executor', 'result_processor',
                        'nl_generator'
                    ]
                }
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on pipeline components.
        
        Returns:
            Dictionary containing health status of each component
        """
        health_status = {
            'overall': 'healthy',
            'components': {},
            'endpoints': {}
        }
        
        try:
            # Check endpoints
            for endpoint_name in self.endpoint_manager.list_endpoints():
                try:
                    endpoint = self.endpoint_manager.get_endpoint(endpoint_name)
                    # Try a simple query to test endpoint
                    test_query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"
                    await endpoint.execute_sparql(test_query)
                    health_status['endpoints'][endpoint_name] = 'healthy'
                except Exception as e:
                    health_status['endpoints'][endpoint_name] = f'unhealthy: {str(e)}'
                    health_status['overall'] = 'degraded'
            
            # Component health (basic checks)
            components = [
                'question_processor', 'entity_extractor', 'rosetta_generator',
                'sparql_generator', 'query_executor', 'result_processor', 'nl_generator'
            ]
            
            for component in components:
                try:
                    component_obj = getattr(self, component)
                    if hasattr(component_obj, 'get_step_metadata'):
                        component_obj.get_step_metadata()
                    health_status['components'][component] = 'healthy'
                except Exception as e:
                    health_status['components'][component] = f'unhealthy: {str(e)}'
                    health_status['overall'] = 'degraded'
            
        except Exception as e:
            health_status['overall'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status


def create_custom_pipeline(steps: List[Any]) -> 'CustomPipeline':
    """
    Create a custom pipeline with specific steps.
    
    This function allows creating specialized pipelines by selecting
    and ordering specific processing steps.
    
    Args:
        steps: List of pipeline step instances in desired order
        
    Returns:
        CustomPipeline instance that processes data through the given steps
        
    Example:
        from science_live.pipeline import (
            QuestionProcessor, EntityExtractorLinker, create_custom_pipeline
        )
        
        custom_steps = [
            QuestionProcessor(),
            EntityExtractorLinker(endpoint_manager)
        ]
        custom_pipeline = create_custom_pipeline(custom_steps)
        
        result = await custom_pipeline.process("What is DNA?")
    """
    
    class CustomPipeline:
        """Custom pipeline with user-defined steps"""
        
        def __init__(self, pipeline_steps: List[Any]):
            self.steps = pipeline_steps
            self.logger = logging.getLogger(self.__class__.__name__)
        
        async def process(self, question: str, **kwargs) -> Any:
            """Process question through custom steps"""
            context = ProcessingContext(original_question=question, **kwargs)
            data = question
            
            self.logger.info(f"Processing through {len(self.steps)} custom steps")
            
            for i, step in enumerate(self.steps):
                try:
                    self.logger.debug(f"Executing step {i+1}: {step.__class__.__name__}")
                    data = await step.process(data, context)
                except Exception as e:
                    self.logger.error(f"Step {i+1} failed: {str(e)}")
                    raise
            
            return data
        
        def get_step_info(self) -> List[str]:
            """Get information about pipeline steps"""
            return [step.__class__.__name__ for step in self.steps]
    
    return CustomPipeline(steps)


# Convenience function for quick pipeline creation
async def quick_process(question: str, endpoint_manager=None) -> NaturalLanguageResult:
    """
    Quick processing function for simple use cases.
    
    Args:
        question: Natural language question to process
        endpoint_manager: Optional endpoint manager (creates test endpoint if None)
        
    Returns:
        NaturalLanguageResult with processed response
        
    Example:
        from science_live.pipeline.pipeline import quick_process
        
        result = await quick_process("What papers cite AlexNet?")
        print(result.summary)
    """
    if endpoint_manager is None:
        from ..core.endpoints import EndpointManager, MockNanopubEndpoint
        endpoint_manager = EndpointManager()
        test_endpoint = MockNanopubEndpoint()
        endpoint_manager.register_endpoint('test', test_endpoint, is_default=True)
    
    pipeline = ScienceLivePipeline(endpoint_manager)
    return await pipeline.process(question)


# Version information
__version__ = "1.0.0"
__author__ = "Science Live Team"
__description__ = "Main pipeline orchestrator for Science Live"
