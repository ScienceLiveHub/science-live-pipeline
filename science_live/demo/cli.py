# =============================================================================
# science_live/demo/cli.py
# =============================================================================

"""
Demo CLI for Science Live.
"""

import asyncio
import sys

def main():
    """Demo CLI"""
    print("🔬 Science Live Demo")
    print("=" * 20)
    
    try:
        from science_live.core.endpoints import EndpointManager, MockNanopubEndpoint
        from science_live.pipeline import ScienceLivePipeline
        
        async def demo():
            endpoint_manager = EndpointManager()
            mock_endpoint = MockNanopubEndpoint()
            endpoint_manager.register_endpoint('demo', mock_endpoint, is_default=True)
            
            pipeline = ScienceLivePipeline(endpoint_manager)
            
            questions = [
                "What papers cite AlexNet?",
                "Who authored the ImageNet paper?",
                "What is machine learning?"
            ]
            
            for question in questions:
                print(f"\n❓ Question: {question}")
                result = await pipeline.process(question)
                print(f"📄 Answer: {result.summary}")
            
            await endpoint_manager.close_all()
        
        asyncio.run(demo())
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
