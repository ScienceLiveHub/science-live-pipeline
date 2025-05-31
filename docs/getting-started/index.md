# Science Live Pipeline - Quick Start Guide

Get started with AI-powered scientific knowledge exploration in under 5 minutes!

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/your-org/science-live-pipeline.git
cd science-live-pipeline

# Install dependencies
pip install -e .

# Or with development tools
pip install -e ".[dev]"
```

## 🔍 Your First Query

In the example below, we use `MockNanopubEndpoint` that is a test implementation of the NanopubEndpoint interface used for testing and development purposes in the Science Live pipeline. It provides fake responses for testing without requiring a real nanopublication server connection.

Create `demo.py` and run Science Live:

```python
import asyncio
from science_live.core import EndpointManager
from science_live.core.endpoints import MockNanopubEndpoint
from science_live.pipeline import ScienceLivePipeline

async def main():
    # Setup demo environment (always works!)
    endpoint_manager = EndpointManager()
    demo_endpoint = MockNanopubEndpoint()
    endpoint_manager.register_endpoint('demo', demo_endpoint, is_default=True)
    
    # Create Science Live pipeline
    pipeline = ScienceLivePipeline(endpoint_manager)
    
    # Ask your first scientific question
    result = await pipeline.process("What papers cite AlexNet?")
    
    print("🔬 Science Live Results:")
    print(f"📊 {result.summary}")
    print("\n📋 Evidence:")
    for detail in result.detailed_results[:3]:
        print(f"  • {detail}")
    
    await endpoint_manager.close_all()

# Run it!
asyncio.run(main())
```

```bash
python demo.py
```

## 🌐 Connect to Real Nanopub Network

Once the demo works, we connect to an actual nanopublication endpoint via the grlc API service hosted at http://grlc.nanopubs.lod.labs.vu.nl.
To make it easier for reuse, we define a new class `GrlcNanopubEndpoint` from `NanopubEndpoint`:

```python
import asyncio
import aiohttp
from science_live.core import EndpointManager
from science_live.core.endpoints import NanopubEndpoint
from science_live.pipeline import ScienceLivePipeline

class GrlcNanopubEndpoint(NanopubEndpoint):
    """Real nanopub network via grlc API"""
    
    def __init__(self, base_url="http://grlc.nanopubs.lod.labs.vu.nl", timeout=30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None
        
    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def execute_sparql(self, query: str):
        """Convert Science Live queries to grlc API calls"""
        session = await self._get_session()
        
        # Map queries to grlc endpoints
        if "cite" in query.lower():
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs_with_text"
            params = {'text': 'cite', 'format': 'json'}
        elif "author" in query.lower():
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs_with_text"
            params = {'text': 'author', 'format': 'json'}
        else:
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs"
            params = {'page': 1, 'format': 'json'}
        
        headers = {'Accept': 'application/json'}
        
        try:
            async with session.get(endpoint, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Return data in SPARQL format (grlc already provides this)
                    return data
                else:
                    return {'results': {'bindings': []}}
        except Exception as e:
            print(f"grlc API error: {e}")
            return {'results': {'bindings': []}}
    
    async def fetch_nanopub(self, uri: str):
        """Fetch individual nanopub"""
        session = await self._get_session()
        try:
            async with session.get(uri) as response:
                return {
                    'uri': uri,
                    'content': await response.text(),
                    'status': response.status
                }
        except Exception as e:
            return {'uri': uri, 'error': str(e)}
    
    async def search_text(self, text: str, limit: int = 10):
        """Search nanopubs by text"""
        # Implementation using grlc text search
        return []

async def connect_real_nanopubs():
    """Connect to real nanopublication network"""
    endpoint_manager = EndpointManager()
    
    # Use real nanopub network
    nanopub_endpoint = GrlcNanopubEndpoint()
    endpoint_manager.register_endpoint('real', nanopub_endpoint, is_default=True)
    
    # Create pipeline
    pipeline = ScienceLivePipeline(endpoint_manager)
    
    # Test with real scientific questions
    questions = [
        "What papers cite AlexNet?",
        "Who authored machine learning papers?",
        "What research relates to neural networks?"
    ]
    
    for question in questions:
        print(f"\n🔬 Question: {question}")
        result = await pipeline.process(question)
        print(f"📊 Answer: {result.summary}")
        
        if result.detailed_results:
            print("📋 Real nanopub evidence:")
            # Show more results - change [:2] to [:5] or [:10]
            for i, detail in enumerate(result.detailed_results[:5], 1):
                print(f"  {i}. {detail}")
            
            # Show total available
            total_results = len(result.detailed_results)
            if total_results > 5:
                print(f"  ... and {total_results - 5} more results available")
    
    await endpoint_manager.close_all()

# Connect to real nanopub network
asyncio.run(connect_real_nanopubs())
```

## 🎯 Example Questions

Try these with your Science Live pipeline:

```python
# Citation analysis
await pipeline.process("What papers cite AlexNet?")
await pipeline.process("What work references https://doi.org/10.1038/nature12373?")

# Author research
await pipeline.process("What papers by 0000-0002-1784-2920?")
await pipeline.process("Who authored deep learning research?")

# Concept exploration
await pipeline.process("What is machine learning?")
await pipeline.process("How do neural networks work?")

# Scientific measurements
await pipeline.process("What is the mass of the Higgs boson?")
await pipeline.process("What are the properties of quantum mechanics?")

# Location-based queries
await pipeline.process("Where is CERN located?")
await pipeline.process("What institutions study particle physics?")

# Complex research questions
await pipeline.process("What recent advances relate to CRISPR gene editing?")
await pipeline.process("How does quantum computing relate to cryptography?")
```

## 🛠️ Configuration

Create `config.yaml` for persistent settings:

```yaml
app_name: "My Science Explorer"
app_type: "research_assistant"

endpoints:
  - name: "nanopub_network"
    type: "grlc"
    url: "http://grlc.nanopubs.lod.labs.vu.nl"
    is_default: true
    timeout: 60

processors:
  text_search_limit: 50
  enable_caching: true
  template_match_threshold: 0.3

ui:
  max_results_per_page: 20
  enable_export: true
  export_formats: ["json", "csv", "rdf"]
```

Load and use configuration:

```python
import asyncio
import aiohttp
from science_live.core import EndpointManager
from science_live.core.endpoints import NanopubEndpoint
from science_live.core.config import ConfigLoader
from science_live.pipeline import ScienceLivePipeline

# First, define the GrlcNanopubEndpoint class (from the working example above)
class GrlcNanopubEndpoint(NanopubEndpoint):
    """Real nanopub network via grlc API"""
    
    def __init__(self, base_url="http://grlc.nanopubs.lod.labs.vu.nl", timeout=30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None
        
    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def execute_sparql(self, query: str):
        """Convert Science Live queries to grlc API calls"""
        session = await self._get_session()
        
        # Map queries to grlc endpoints
        if "cite" in query.lower():
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs_with_text"
            params = {'text': 'cite', 'format': 'json'}
        elif "author" in query.lower():
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs_with_text"
            params = {'text': 'author', 'format': 'json'}
        else:
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs"
            params = {'page': 1, 'format': 'json'}
        
        headers = {'Accept': 'application/json'}
        
        try:
            async with session.get(endpoint, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return {'results': {'bindings': []}}
        except Exception as e:
            print(f"grlc API error: {e}")
            return {'results': {'bindings': []}}
    
    async def fetch_nanopub(self, uri: str):
        """Fetch individual nanopub"""
        session = await self._get_session()
        try:
            async with session.get(uri) as response:
                return {
                    'uri': uri,
                    'content': await response.text(),
                    'status': response.status
                }
        except Exception as e:
            return {'uri': uri, 'error': str(e)}
    
    async def search_text(self, text: str, limit: int = 10):
        """Search nanopubs by text"""
        return []

async def main_with_config():
    # Load configuration from YAML
    config = ConfigLoader.from_yaml('config.yaml')
    
    # Create endpoint manager
    endpoint_manager = EndpointManager()
    
    # Setup endpoints from config
    for ep_config in config.endpoints:
        if ep_config.type == "grlc":
            # Use the GrlcNanopubEndpoint class defined above
            nanopub_endpoint = GrlcNanopubEndpoint(ep_config.url, ep_config.timeout)
            endpoint_manager.register_endpoint(
                ep_config.name, 
                nanopub_endpoint, 
                is_default=ep_config.is_default
            )
    
    # Create pipeline with both endpoint_manager AND config
    pipeline = ScienceLivePipeline(endpoint_manager, config={'debug': True})
    
    # Use the configured pipeline
    result = await pipeline.process("What papers cite AlexNet?")
    print(f"📊 {result.summary}")
    
    await endpoint_manager.close_all()

# Run with configuration
asyncio.run(main_with_config())
```

**Or simpler approach without YAML (recommended for beginners):**

```python
import asyncio
import aiohttp
from science_live.core import EndpointManager
from science_live.core.endpoints import NanopubEndpoint
from science_live.pipeline import ScienceLivePipeline

# Define the working GrlcNanopubEndpoint class
class GrlcNanopubEndpoint(NanopubEndpoint):
    """Real nanopub network via grlc API"""
    
    def __init__(self, base_url="http://grlc.nanopubs.lod.labs.vu.nl", timeout=30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None
        
    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def execute_sparql(self, query: str):
        """Convert Science Live queries to grlc API calls"""
        session = await self._get_session()
        
        # Map queries to grlc endpoints
        if "cite" in query.lower():
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs_with_text"
            params = {'text': 'cite', 'format': 'json'}
        elif "author" in query.lower():
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs_with_text"
            params = {'text': 'author', 'format': 'json'}
        else:
            endpoint = f"{self.base_url}/api/local/local/find_nanopubs"
            params = {'page': 1, 'format': 'json'}
        
        headers = {'Accept': 'application/json'}
        
        try:
            async with session.get(endpoint, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return {'results': {'bindings': []}}
        except Exception as e:
            print(f"grlc API error: {e}")
            return {'results': {'bindings': []}}
    
    async def fetch_nanopub(self, uri: str):
        """Fetch individual nanopub"""
        session = await self._get_session()
        try:
            async with session.get(uri) as response:
                return {
                    'uri': uri,
                    'content': await response.text(),
                    'status': response.status
                }
        except Exception as e:
            return {'uri': uri, 'error': str(e)}
    
    async def search_text(self, text: str, limit: int = 10):
        """Search nanopubs by text"""
        return []

async def simple_configured_pipeline():
    # Manual configuration (no YAML file needed)
    endpoint_manager = EndpointManager()
    
    # Add your working nanopub endpoint
    nanopub_endpoint = GrlcNanopubEndpoint(
        base_url="http://grlc.nanopubs.lod.labs.vu.nl",
        timeout=60
    )
    endpoint_manager.register_endpoint('nanopubs', nanopub_endpoint, is_default=True)
    
    # Pipeline with custom config
    pipeline_config = {
        'debug': True,
        'result_limit': 50,
        'enable_caching': True
    }
    pipeline = ScienceLivePipeline(endpoint_manager, config=pipeline_config)
    
    # Use the pipeline
    result = await pipeline.process("What papers cite AlexNet?")
    print(f"📊 {result.summary}")
    
    await endpoint_manager.close_all()

# Run the simple configured pipeline
asyncio.run(simple_configured_pipeline())
```

## 📚 Understanding the Pipeline

Science Live processes questions through 7 AI steps:

1. **🧠 Question Processing** - Analyzes natural language and extracts intent
2. **🔍 Entity Extraction** - Finds scientific entities (papers, authors, concepts)
3. **📝 Rosetta Generation** - Creates structured scientific statements
4. **⚡ SPARQL Translation** - Converts to database queries
5. **🌐 Query Execution** - Searches nanopublication networks
6. **📊 Result Processing** - Organizes and ranks findings
7. **💬 Natural Language** - Generates human-readable responses

## 📖 Next Steps

1. **🔬 Explore** - Try different scientific questions and domains
2. **🛠️ Customize** - Adapt pipeline steps for your research area
3. **📊 Integrate** - Build Science Live into your research workflows
4. **🌐 Scale** - Deploy for team or institutional use
5. **🤝 Contribute** - Help improve the scientific knowledge network

**Need help?** Check the [API documentation](../api/index) or [open an issue](https://github.com/your-org/science-live-pipeline/issues).
