# ============================================================================
# tests/fixtures/sample_entities.py
# ============================================================================

"""Sample entities for testing."""

from science_live.pipeline.common import ExtractedEntity, EntityType

SAMPLE_DOI_ENTITIES = [
    ExtractedEntity(
        text="10.1038/nature12373",
        entity_type=EntityType.DOI,
        confidence=0.95,
        start_pos=0,
        end_pos=20,
        uri="https://doi.org/10.1038/nature12373",
        label="AlexNet Paper"
    ),
    ExtractedEntity(
        text="10.1234/example",
        entity_type=EntityType.DOI,
        confidence=0.9,
        start_pos=0,
        end_pos=15,
        uri="https://doi.org/10.1234/example",
        label="Example Paper"
    )
]

SAMPLE_ORCID_ENTITIES = [
    ExtractedEntity(
        text="0000-0002-1784-2920",
        entity_type=EntityType.ORCID,
        confidence=0.95,
        start_pos=0,
        end_pos=19,
        uri="https://orcid.org/0000-0002-1784-2920",
        label="Anne Fouilloux"
    )
]

SAMPLE_CONCEPT_ENTITIES = [
    ExtractedEntity(
        text="machine learning",
        entity_type=EntityType.CONCEPT,
        confidence=0.8,
        start_pos=0,
        end_pos=16,
        label="Machine Learning"
    ),
    ExtractedEntity(
        text="quantum mechanics",
        entity_type=EntityType.CONCEPT,
        confidence=0.85,
        start_pos=0,
        end_pos=17,
        label="Quantum Mechanics"
    )
]

