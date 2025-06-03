# =============================================================================
# scripts/validate_install.py
# =============================================================================

#!/usr/bin/env python3
"""
Installation Validator for Science Live
=======================================

This script validates that Science Live is properly installed and
all components are working correctly.

Usage:
    python scripts/validate_install.py
    python scripts/validate_install.py --wordnet
    python scripts/validate_install.py --full
"""

import sys
import importlib
import argparse
from pathlib import Path

def test_basic_imports():
    """Test basic Science Live imports"""
    print("📦 Testing basic imports...")
    
    try:
        import science_live
        print(f"✓ science_live imported (version: {getattr(science_live, '__version__', 'unknown')})")
    except ImportError as e:
        print(f"✗ Failed to import science_live: {e}")
        return False
    
    components = [
        ('science_live.core', 'Core components'),
        ('science_live.pipeline', 'Pipeline components'),
        ('science_live.pipeline.common', 'Common data models'),
    ]
    
    success = True
    for module_name, description in components:
        try:
            importlib.import_module(module_name)
            print(f"✓ {description} available")
        except ImportError as e:
            print(f"✗ {description} failed: {e}")
            success = False
    
    return success

def test_wordnet_integration():
    """Test WordNet integration"""
    print("\n🧠 Testing WordNet integration...")
    
    try:
        import wn
        print("✓ WordNet package available")
        
        # Check for WordNet data
        try:
            lexicons = wn.lexicons()
            if lexicons:
                print(f"✓ WordNet data available ({len(lexicons)} lexicons)")
                for lex in lexicons[:3]:  # Show first 3
                    print(f"  - {lex.identifier}: {lex.label}")
                if len(lexicons) > 3:
                    print(f"  ... and {len(lexicons) - 3} more")
            else:
                print("⚠ WordNet package installed but no data found")
                print("  Run: python scripts/setup_wordnet.py")
                return False
        except Exception as e:
            print(f"⚠ Could not check WordNet data: {e}")
            return False
        
        # Test basic WordNet functionality
        try:
            synsets = wn.synsets('science')
            if synsets:
                print(f"✓ WordNet functionality working ({len(synsets)} synsets for 'science')")
            else:
                print("⚠ WordNet installed but not functioning properly")
                return False
        except Exception as e:
            print(f"✗ WordNet functionality test failed: {e}")
            return False
            
        return True
        
    except ImportError:
        print("⚠ WordNet package not available")
        print("  Install with: pip install wn")
        print("  Or: pip install science-live[enhanced]")
        return False

def test_pipeline_functionality():
    """Test basic pipeline functionality"""
    print("\n⚙️ Testing pipeline functionality...")
    
    try:
        from science_live.core.endpoints import EndpointManager, MockNanopubEndpoint
        from science_live.pipeline import ScienceLivePipeline
        
        # Create test pipeline
        endpoint_manager = EndpointManager()
        mock_endpoint = MockNanopubEndpoint()
        endpoint_manager.register_endpoint('test', mock_endpoint, is_default=True)
        
        pipeline = ScienceLivePipeline(endpoint_manager)
        print("✓ Pipeline creation successful")
        
        # Test pipeline info
        info = pipeline.get_pipeline_info()
        if info and 'steps' in info:
            print(f"✓ Pipeline has {len(info['steps'])} steps")
        else:
            print("⚠ Pipeline info incomplete")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Pipeline test failed: {e}")
        return False

async def test_async_functionality():
    """Test async pipeline functionality"""
    print("\n🔄 Testing async functionality...")
    
    try:
        from science_live.core.endpoints import EndpointManager, MockNanopubEndpoint
        from science_live.pipeline import ScienceLivePipeline
        
        # Create test pipeline
        endpoint_manager = EndpointManager()
        mock_endpoint = MockNanopubEndpoint()
        endpoint_manager.register_endpoint('test', mock_endpoint, is_default=True)
        
        pipeline = ScienceLivePipeline(endpoint_manager)
        
        # Test basic question processing
        result = await pipeline.process("What is machine learning?")
        
        if result and hasattr(result, 'summary'):
            print("✓ Async question processing successful")
            print(f"  Sample result: {result.summary[:50]}...")
            return True
        else:
            print("✗ Async processing returned invalid result")
            return False
            
    except Exception as e:
        print(f"✗ Async functionality test failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate Science Live installation")
    parser.add_argument('--wordnet', action='store_true', help='Test WordNet integration')
    parser.add_argument('--full', action='store_true', help='Run full test suite')
    
    args = parser.parse_args()
    
    print("🔍 Science Live Installation Validator")
    print("=" * 40)
    
    success = True
    
    # Basic imports test
    if not test_basic_imports():
        success = False
    
    # WordNet test (if requested or full)
    if args.wordnet or args.full:
        if not test_wordnet_integration():
            success = False
    
    # Pipeline functionality test
    if not test_pipeline_functionality():
        success = False
    
    # Async functionality test (if full)
    if args.full:
        import asyncio
        try:
            if not asyncio.run(test_async_functionality()):
                success = False
        except Exception as e:
            print(f"✗ Async test setup failed: {e}")
            success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed! Science Live is properly installed.")
        if not (args.wordnet or args.full):
            print("\nFor complete validation, run:")
            print("  python scripts/validate_install.py --full")
    else:
        print("⚠ Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("  - Reinstall: pip install -e .")
        print("  - Setup WordNet: python scripts/setup_wordnet.py")
        print("  - Setup dev environment: python scripts/setup_dev.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
