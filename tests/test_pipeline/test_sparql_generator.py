import pytest
from science_live.pipeline.sparql_generator import SPARQLGenerator
from science_live.pipeline.common import (
    GeneratedStatements, RosettaStatement, ProcessingContext,
    ExtractedEntity, EntityType
)


class TestSPARQLGenerator:
    """Test SPARQLGenerator functionality."""
    
    @pytest.fixture
    def generator(self):
        """Create a SPARQL generator."""
        return SPARQLGenerator()
    
    @pytest.fixture
    def sample_rosetta_statement(self):
        """Create a sample Rosetta statement."""
        subject = ExtractedEntity(
            text="AlexNet",
            entity_type=EntityType.DOI,
            confidence=0.95,
            start_pos=0,
            end_pos=7,
            uri="https://doi.org/10.1038/nature12373",
            label="AlexNet paper"
        )
        
        object1 = ExtractedEntity(
            text="ImageNet",
            entity_type=EntityType.DOI,
            confidence=0.9,
            start_pos=10,
            end_pos=18,
            uri="https://doi.org/10.1234/imagenet",
            label="ImageNet paper"
        )
        
        return RosettaStatement(
            subject=subject,
            statement_type_uri="https://w3id.org/rosetta/Cites",
            statement_type_label="cites",
            required_object1=object1,
            dynamic_label_template="SUBJECT cites OBJECT1"
        )
    
    @pytest.fixture
    def generated_statements(self, sample_rosetta_statement):
        """Create sample generated statements."""
        return GeneratedStatements(
            statements=[sample_rosetta_statement],
            generation_confidence=0.8
        )
    
    @pytest.mark.asyncio
    async def test_basic_sparql_generation(self, generator, generated_statements, processing_context):
        """Test basic SPARQL query generation."""
        result = await generator.generate(generated_statements, processing_context)
        
        assert result.primary_query is not None
        assert result.primary_query.query_text is not None
        assert len(result.primary_query.query_text) > 0
        
        # Should be a SELECT query
        assert result.primary_query.query_type == 'SELECT'
        assert 'SELECT' in result.primary_query.query_text
        assert 'WHERE' in result.primary_query.query_text
    
    @pytest.mark.asyncio
    async def test_rosetta_query_structure(self, generator, generated_statements, processing_context):
        """Test Rosetta-specific SPARQL query structure."""
        result = await generator.generate(generated_statements, processing_context)
        
        query_text = result.primary_query.query_text
        
        # Should include Rosetta namespaces and patterns
        assert 'PREFIX rosetta:' in query_text
        assert 'rosetta:RosettaStatement' in query_text
        assert 'rosetta:hasStatementType' in query_text
        assert 'rosetta:subject' in query_text
    
    @pytest.mark.asyncio
    async def test_uri_filtering(self, generator, generated_statements, processing_context):
        """Test URI filtering in generated queries."""
        result = await generator.generate(generated_statements, processing_context)
        
        query_text = result.primary_query.query_text
        
        # Should include the subject URI
        assert 'https://doi.org/10.1038/nature12373' in query_text
        
        # Should include the statement type URI
        assert 'https://w3id.org/rosetta/Cites' in query_text
    
    @pytest.mark.asyncio
    async def test_fallback_query_generation(self, generator, generated_statements, processing_context):
        """Test fallback query generation."""
        result = await generator.generate(generated_statements, processing_context)
        
        # Should have fallback queries
        assert len(result.fallback_queries) > 0
        
        # Fallback queries should be valid
        for fallback in result.fallback_queries:
            assert fallback.query_text is not None
            assert len(fallback.query_text) > 0
            assert fallback.query_type in ['SELECT', 'ASK', 'CONSTRUCT']
    
    @pytest.mark.asyncio
    async def test_citation_specific_queries(self, generator, processing_context):
        """Test generation of citation-specific queries."""
        # Create citation statement
        subject = ExtractedEntity(
            text="paper", entity_type=EntityType.DOI,
            confidence=0.9, start_pos=0, end_pos=5,
            uri="https://doi.org/10.1038/example"
        )
        
        citation_stmt = RosettaStatement(
            subject=subject,
            statement_type_uri="https://w3id.org/rosetta/Cites",
            statement_type_label="cites"
        )
        
        statements = GeneratedStatements(
            statements=[citation_stmt],
            generation_confidence=0.8
        )
        
        result = await generator.generate(statements, processing_context)
        
        # Should generate citation-specific fallback
        citation_queries = [q for q in result.fallback_queries 
                          if 'cito:' in q.query_text or 'fabio:' in q.query_text]
        assert len(citation_queries) > 0
    
    @pytest.mark.asyncio
    async def test_complexity_estimation(self, generator, generated_statements, processing_context):
        """Test query complexity estimation."""
        result = await generator.generate(generated_statements, processing_context)
        
        complexity = result.primary_query.estimated_complexity
        assert 1 <= complexity <= 5
        
        # Should have reasonable complexity for statement with subject and object
        assert complexity >= 2
    
    @pytest.mark.asyncio
    async def test_empty_statements_handling(self, generator, processing_context):
        """Test handling of empty statement lists."""
        empty_statements = GeneratedStatements(
            statements=[],
            generation_confidence=0.0
        )
        
        result = await generator.generate(empty_statements, processing_context)
        
        # Should generate fallback query
        assert result.primary_query is not None
        assert result.generation_method == 'text_fallback'
    
    def test_query_validation(self, generator):
        """Test SPARQL query validation."""
        from science_live.pipeline.common import SPARQLQuery, validate_sparql_query
        
        valid_query = SPARQLQuery(
            query_text="SELECT * WHERE { ?s ?p ?o }",
            query_type="SELECT",
            estimated_complexity=1
        )
        assert validate_sparql_query(valid_query) is True
        
        invalid_query = SPARQLQuery(
            query_text="",
            query_type="",
            estimated_complexity=0
        )
        assert validate_sparql_query(invalid_query) is False


