---
title: Science Live Pipeline
subtitle: Breaking Down Silos to Accelerate Knowledge Transfer
description: Semantic knowledge exploration for scientific research
keywords: [FAIR, nanopublications, semantic web, research collaboration]
---

# Science Live Pipeline

## Breaking Down Silos to Accelerate Knowledge Transfer

Science Live Pipeline is a **semantic knowledge exploration platform** designed to address one of the most pressing challenges in modern research: **knowledge silos** that prevent effective collaboration and discovery across disciplines, institutions, and research domains.

```{note}
**The Silo Problem**: Valuable scientific insights often remain trapped within individual research groups, institutions, or disciplines, limiting the potential for breakthrough discoveries and collaborative innovation.
```

## What You Can Do With Science Live

Ask questions in natural language and get structured scientific insights:

- **"What papers cite the original transformer paper?"** → Get citation networks
- **"Who are the key researchers in CRISPR gene editing?"** → Discover expert networks  
- **"What measurements exist for graphene conductivity?"** → Find experimental data
- **"How do climate models connect to biodiversity research?"** → Explore cross-domain links

## Quick Start

Get Science Live running in 2 steps:

1. **Installation**

```bash
git clone https://github.com/ScienceLiveHub/science-live-pipeline

pip install -e ".[dev]"

```

2. **Basic Usage**

```python
# Quick setup for experimentation
import asyncio
from science_live.pipeline.pipeline import quick_process

async def quick_explore():
    # This creates a test environment automatically
    result = await quick_process(
        "What papers cite AlexNet?",
        endpoint_manager=None  # Uses petapico endpoint automatically
    )
    print(result.summary)
    return result

# Run in script
result = asyncio.run(quick_explore())

# Or in Jupyter notebook, use:
# result = await quick_explore()
```

## The Science Live Approach

Breaking down research silos requires a systematic approach to knowledge transformation:

```{mermaid}
graph TD
    A[Research Silos] --> B[Semantic Integration]
    B --> C[Knowledge Graphs]
    C --> D[Collaborative Discovery]

    E[FAIR Principles] --> B
    F[Nanopublications] --> B
    E --> C
    F --> C

    style A fill:#ffcccc
    style D fill:#ccffcc
```

Science Live addresses the silo problem by:

1. Leveraging proven standards (FAIR Principles, Nanopublications) to structure scientific knowledge
2. Enabling semantic integration that makes research outputs machine-readable and interconnectable
3. Building knowledge graphs that reveal hidden connections across research domains
4. Facilitating collaborative discovery through natural language exploration of the scientific record

## Built on Proven Standards

- **Nanopublications**: Structured scientific claims with provenance
- **SPARQL**: Industry-standard semantic web queries
- **FAIR Principles**: Ensuring data findability and reusability
- **Rosetta Statements**: Standardized scientific claim representation

## Community & Support

Science Live Pipeline is developed as an open-source project with contributions from researchers and developers worldwide.

- **Documentation**: This site
- **Issues & Support**: [GitHub Issues](https://github.com/ScienceLiveHub/science-live-pipeline/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ScienceLiveHub/science-live-pipeline/discussions)
- **Contributing**: [Contributing Guide](contributing/index.md)

## Citation

If you use Science Live Pipeline in your research, please cite:

```bibtex
@software{science_live_pipeline,
  title = {Science Live Pipeline: Breaking Down Silos to Accelerate Knowledge Transfer},
  author = {Science Live Team},
  year = {2025},
  url = {https://github.com/ScienceLiveHub/science-live-pipeline},
  version = {0.0.1}
}
```

```{toctree}
:hidden:

getting-started/index
api/index
contributing/index
