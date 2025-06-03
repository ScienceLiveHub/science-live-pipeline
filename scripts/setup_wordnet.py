# =============================================================================
# scripts/setup_wordnet.py
# =============================================================================

#!/usr/bin/env python3
"""
WordNet Setup Script for Science Live
=====================================

This script downloads and sets up the English WordNet data required
for enhanced question processing in Science Live.

Usage:
    python scripts/setup_wordnet.py
    python scripts/setup_wordnet.py --help
    python scripts/setup_wordnet.py status
    python scripts/setup_wordnet.py install
    python scripts/setup_wordnet.py uninstall
"""

import sys
import os
import argparse
from pathlib import Path
import logging

# Add the project root to Python path so we can import science_live
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_wn_availability():
    """Check if wn package is available"""
    try:
        import wn
        logger.info("✓ WordNet package (wn) is available")
        return True
    except ImportError:
        logger.error("✗ WordNet package (wn) not found")
        logger.error("Please install with: pip install wn")
        logger.error("Or install science-live with: pip install -e .[enhanced]")
        return False

def download_wordnet_data():
    """Download Open English WordNet data"""
    try:
        import wn
        
        logger.info("Checking for existing WordNet data...")
        
        # Check if Open English WordNet is already installed
        try:
            lexicons = wn.lexicons()
            oewn_installed = any('oewn' in lex.identifier for lex in lexicons)
            ewn_installed = any('ewn' in lex.identifier for lex in lexicons)
            
            if oewn_installed:
                logger.info("✓ Open English WordNet data already installed")
                return True
            elif ewn_installed:
                logger.info("✓ English WordNet data found (older version)")
                logger.info("Consider upgrading to Open English WordNet 2024")
                return True
                
        except Exception as e:
            logger.warning(f"Could not check existing lexicons: {e}")
        
        logger.info("Downloading Open English WordNet 2024...")
        logger.info("This may take a few minutes on first run...")
        
        # Download Open English WordNet 2024 (latest recommended)
        wn.download('oewn:2024')
        
        logger.info("✓ Open English WordNet 2024 downloaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to download WordNet data: {e}")
        logger.error("You may need to check your internet connection or try again later")
        return False

def verify_installation():
    """Verify WordNet installation works correctly"""
    try:
        import wn
        
        logger.info("Verifying WordNet installation...")
        
        # Test basic functionality with the default wordnet
        try:
            # Try with Open English WordNet first
            en = wn.Wordnet('oewn:2024')
            synsets = en.synsets('science')
        except:
            # Fallback to general function
            synsets = wn.synsets('science')
        
        if synsets:
            logger.info(f"✓ WordNet verification successful - found {len(synsets)} synsets for 'science'")
            
            # Test a few basic operations
            first_synset = synsets[0]
            logger.info(f"  Example synset: {first_synset}")
            
            # Test hypernyms if available
            try:
                hypernyms = first_synset.hypernyms()
                if hypernyms:
                    logger.info(f"  Found {len(hypernyms)} hypernyms")
            except:
                logger.info("  Hypernym functionality may vary with WordNet version")
            
            return True
        else:
            logger.warning("⚠ WordNet installed but no synsets found for 'science'")
            return False
            
    except Exception as e:
        logger.error(f"✗ WordNet verification failed: {e}")
        return False

def check_wordnet_status():
    """Check current WordNet status"""
    try:
        import wn
        
        print("WordNet Status Report")
        print("=" * 30)
        
        # Check available lexicons
        try:
            lexicons = wn.lexicons()
            print(f"Available lexicons: {len(lexicons)}")
            
            for lexicon in lexicons:
                print(f"  - {lexicon.identifier}: {lexicon.label}")
        except Exception as e:
            print(f"Could not list lexicons: {e}")
        
        # Test basic functionality
        test_words = ['science', 'research', 'publication', 'citation']
        
        print(f"\nSynset counts for test words:")
        for word in test_words:
            try:
                synsets = wn.synsets(word)
                print(f"  {word}: {len(synsets)} synsets")
            except Exception as e:
                print(f"  {word}: Error - {e}")
        
        print("\n✓ WordNet status check complete")
        return True
        
    except ImportError:
        print("✗ WordNet package not available")
        print("Install with: pip install wn")
        return False
    except Exception as e:
        print(f"✗ WordNet error: {e}")
        return False

def uninstall_wordnet_data():
    """Remove WordNet data (useful for testing/cleanup)"""
    try:
        import wn
        
        print("Removing WordNet data...")
        lexicons = wn.lexicons()
        removed_count = 0
        
        for lexicon in lexicons:
            if 'oewn' in lexicon.identifier or 'ewn' in lexicon.identifier:
                print(f"Removing {lexicon.identifier}...")
                try:
                    wn.remove(lexicon.identifier)
                    removed_count += 1
                except Exception as e:
                    print(f"Failed to remove {lexicon.identifier}: {e}")
        
        if removed_count > 0:
            print(f"✓ Removed {removed_count} WordNet lexicon(s)")
        else:
            print("No WordNet lexicons found to remove")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to remove WordNet data: {e}")
        return False

def setup_wordnet_cache_dir():
    """Setup cache directory for WordNet operations"""
    try:
        # Create cache directory in user's home
        cache_dir = Path.home() / '.science_live' / 'wordnet_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✓ WordNet cache directory created: {cache_dir}")
        return str(cache_dir)
        
    except Exception as e:
        logger.warning(f"Could not create cache directory: {e}")
        return None

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(
        description="Setup WordNet for Science Live enhanced question processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_wordnet.py                # Full setup
  python scripts/setup_wordnet.py status         # Check status
  python scripts/setup_wordnet.py install        # Install WordNet data
  python scripts/setup_wordnet.py uninstall      # Remove WordNet data
        """
    )
    
    parser.add_argument(
        'command', 
        nargs='?',
        choices=['install', 'status', 'uninstall'],
        default='install',
        help='Command to run (default: install)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 50)
    logger.info("Science Live WordNet Setup")
    logger.info("=" * 50)
    
    if args.command == 'status':
        return check_wordnet_status()
    
    elif args.command == 'uninstall':
        return uninstall_wordnet_data()
    
    elif args.command == 'install':
        success = True
        
        # Step 1: Check if wn package is available
        if not check_wn_availability():
            logger.error("Please install the WordNet package first:")
            logger.error("  pip install wn")
            logger.error("  or pip install science-live[enhanced]")
            return False
        
        # Step 2: Download WordNet data
        if not download_wordnet_data():
            success = False
        
        # Step 3: Verify installation
        if not verify_installation():
            success = False
        
        # Step 4: Setup cache directory
        cache_dir = setup_wordnet_cache_dir()
        
        # Summary
        logger.info("=" * 50)
        if success:
            logger.info("✓ WordNet setup completed successfully!")
            logger.info("")
            logger.info("You can now use enhanced question processing with:")
            logger.info("  from science_live.pipeline.question_processor import EnhancedQuestionProcessor")
            logger.info("")
            logger.info("Test your installation:")
            logger.info("  python scripts/setup_wordnet.py status")
            logger.info("")
            if cache_dir:
                logger.info(f"Cache directory: {cache_dir}")
        else:
            logger.error("✗ WordNet setup encountered errors")
            logger.error("Some features may not work correctly")
        
        logger.info("=" * 50)
        return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
