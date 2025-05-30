# ============================================================================
# tests/fixtures/sample_sparql_results.py
# ============================================================================

"""Sample SPARQL results for testing."""

SAMPLE_CITATION_RESULTS = {
    'results': {
        'bindings': [
            {
                'np': {'value': 'http://purl.org/np/citation1'},
                'citing_paper': {'value': 'https://doi.org/10.1234/citing'},
                'cited_paper': {'value': 'https://doi.org/10.1038/nature12373'},
                'citation_type': {'value': 'http://purl.org/spar/cito/cites'}
            },
            {
                'np': {'value': 'http://purl.org/np/citation2'},
                'citing_paper': {'value': 'https://doi.org/10.5678/another'},
                'cited_paper': {'value': 'https://doi.org/10.1038/nature12373'},
                'citation_type': {'value': 'http://purl.org/spar/cito/extends'}
            }
        ]
    }
}

SAMPLE_ROSETTA_RESULTS = {
    'results': {
        'bindings': [
            {
                'np': {'value': 'http://purl.org/np/rosetta1'},
                'statement': {'value': 'http://purl.org/np/rosetta1#stmt'},
                'subject': {'value': 'https://doi.org/10.1038/nature12373'},
                'object1': {'value': 'https://doi.org/10.1234/cited'},
                'label': {'value': 'AlexNet cites ImageNet paper'},
                'confidence': {'value': '0.9'}
            }
        ]
    }
}
