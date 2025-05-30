from setuptools import setup, find_packages

setup(
    name="science-live",
    version="0.0.1",
    author="Science Live Team",
    description="Semantic knowledge exploration for scientific research",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "pydantic>=1.10.0",
        "pyyaml>=6.0",
        "rdflib>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
        ],
        "nlp": [
            "spacy>=3.4.0",
            "transformers>=4.20.0",
        ],
        "viz": [
            "networkx>=2.8.0",
            "plotly>=5.10.0",
        ]
    },
)
