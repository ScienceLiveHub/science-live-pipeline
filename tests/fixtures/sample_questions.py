# ============================================================================
# tests/fixtures/sample_questions.py
# ============================================================================

"""Sample questions for testing the pipeline."""

CITATION_QUESTIONS = [
    "What papers cite AlexNet?",
    "Who cites https://doi.org/10.1038/nature12373?",
    "Show me citations for the ImageNet paper",
    "What work references this research?",
]

AUTHORSHIP_QUESTIONS = [
    "Who authored this paper?",
    "What papers by 0000-0002-1784-2920?",
    "Show me work by Anne Fouilloux",
    "Authors of the AlexNet paper?",
]

MEASUREMENT_QUESTIONS = [
    "What is the mass of the Higgs boson?",
    "Temperature of the cosmic microwave background?",
    "How fast is the speed of light?",
    "What is the charge of an electron?",
]

LOCATION_QUESTIONS = [
    "Where is CERN located?",
    "Location of the Large Hadron Collider?",
    "Where was this research conducted?",
]

COMPLEX_QUESTIONS = [
    "What papers by researchers at CERN cite quantum mechanics work and relate to particle physics?",
    "Show me recent citations of climate change research by authors with ORCID IDs from Norwegian institutions",
    "Find measurements of stellar masses in papers published after 2020 that cite Gaia mission data",
]

ALL_SAMPLE_QUESTIONS = (
    CITATION_QUESTIONS + 
    AUTHORSHIP_QUESTIONS + 
    MEASUREMENT_QUESTIONS + 
    LOCATION_QUESTIONS + 
    COMPLEX_QUESTIONS
)

