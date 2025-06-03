# =============================================================================
# science_live/setup/validate.py
# =============================================================================

"""
Installation validation module.
"""

import sys
import argparse
import importlib

def test_basic_imports():
    """Test basic Science Live imports"""
    print("📦 Testing basic imports...")
    
    try:
        import science_live
        print(f"✓ science_live (version: {getattr(science_live, '__version__', 'unknown')})")
    except ImportError as e:
        print(f"✗ science_live import failed: {e}")
        return False
    
    components = [
        ('science_live.core', 'Core components'),
        ('science_live.pipeline', 'Pipeline components'),
    ]
    
    success = True
    for module_name, description in components:
        try:
            importlib.import_module(module_name)
            print(f"✓ {description}")
        except ImportError as e:
            print(f"✗ {description} failed: {e}")
            success = False
    
    return success

def test_wordnet():
    """Test WordNet integration"""
    print("\n🧠 Testing WordNet...")
    
    try:
        import wn
        print("✓ WordNet package available")
        
        lexicons = wn.lexicons()
        if lexicons:
            print(f"✓ WordNet data available ({len(lexicons)} lexicons)")
        else:
            print("⚠ No WordNet data found")
            return False
        
        # Test functionality
        synsets = wn.synsets('science')
        if synsets:
            print(f"✓ WordNet functional ({len(synsets)} synsets for 'science')")
        else:
            print("⚠ WordNet not functioning properly")
            return False
            
        return True
        
    except ImportError:
        print("⚠ WordNet package not available")
        return False

def test_pipeline():
    """Test pipeline functionality"""
    print("\n⚙️ Testing pipeline...")
    
    try:
        from science_live.core.endpoints import EndpointManager, MockNanopubEndpoint
        from science_live.pipeline import ScienceLivePipeline
        
        endpoint_manager = EndpointManager()
        mock_endpoint = MockNanopubEndpoint()
        endpoint_manager.register_endpoint('test', mock_endpoint, is_default=True)
        
        pipeline = ScienceLivePipeline(endpoint_manager)
        print("✓ Pipeline creation successful")
        
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

def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate Science Live installation")
    parser.add_argument('--wordnet', action='store_true', help='Test WordNet integration')
    parser.add_argument('--full', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    print("🔍 Science Live Installation Validator")
    print("=" * 40)
    
    success = True
    
    # Basic tests
    if not test_basic_imports():
        success = False
    
    if not test_pipeline():
        success = False
    
    # WordNet tests
    if args.wordnet or args.full:
        if not test_wordnet():
            success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed!")
        if not (args.wordnet or args.full):
            print("Run with --full for complete validation")
    else:
        print("❌ Some tests failed")
        print("Try: science-live-setup-dev")
    
    return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
