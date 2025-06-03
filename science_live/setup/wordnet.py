# =============================================================================
# science_live/setup/wordnet.py - for wn 0.12.0 API
# =============================================================================

"""
WordNet setup module - accessible via console scripts.
Compatible with wn 0.12.0 API changes.
"""

import sys
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_wn_availability():
    """Check if wn package is available"""
    try:
        import wn
        logger.info("✓ WordNet package (wn) is available")
        return True
    except ImportError:
        logger.error("✗ WordNet package (wn) not found")
        logger.error("Install with: pip install science-live[enhanced]")
        return False

def get_lexicon_info(lexicon):
    """Get lexicon information with API compatibility"""
    try:
        # Try wn 0.12.0+ API first
        if hasattr(lexicon, 'specifier'):
            identifier = lexicon.specifier()
        elif hasattr(lexicon, 'id') and hasattr(lexicon, 'version'):
            identifier = f"{lexicon.id}:{lexicon.version}"
        else:
            identifier = str(lexicon)
        
        # Get label/name
        if hasattr(lexicon, 'label'):
            label = lexicon.label
        elif hasattr(lexicon, 'name'):
            label = lexicon.name
        else:
            label = "Unknown"
        
        return identifier, label
        
    except Exception as e:
        logger.debug(f"Error getting lexicon info: {e}")
        return str(lexicon), "Unknown"

def download_wordnet_data():
    """Download Open English WordNet data"""
    try:
        import wn
        
        logger.info("Checking for existing WordNet data...")
        
        # Check if Open English WordNet is already installed
        try:
            lexicons = wn.lexicons()
            
            # Check for existing installations
            oewn_installed = False
            ewn_installed = False
            
            for lexicon in lexicons:
                identifier, _ = get_lexicon_info(lexicon)
                if 'oewn' in identifier.lower():
                    oewn_installed = True
                elif 'ewn' in identifier.lower():
                    ewn_installed = True
            
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
        logger.info("This may take a few minutes...")
        
        # Download Open English WordNet 2024
        wn.download('oewn:2024')
        
        logger.info("✓ Open English WordNet 2024 downloaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to download WordNet data: {e}")
        logger.error("Check your internet connection and try again")
        return False

def verify_installation():
    """Verify WordNet installation"""
    try:
        import wn
        
        logger.info("Verifying WordNet installation...")
        
        # Test basic functionality with different API approaches
        try:
            # Try with Open English WordNet first
            en = wn.Wordnet('oewn:2024')
            synsets = en.synsets('science')
        except:
            try:
                # Fallback to general function
                synsets = wn.synsets('science')
            except:
                # Try with any available lexicon
                lexicons = wn.lexicons()
                if lexicons:
                    # Use first available lexicon
                    first_lexicon = lexicons[0]
                    identifier, _ = get_lexicon_info(first_lexicon)
                    en = wn.Wordnet(identifier)
                    synsets = en.synsets('science')
                else:
                    synsets = []
        
        if synsets:
            logger.info(f"✓ WordNet working - found {len(synsets)} synsets for 'science'")
            return True
        else:
            logger.warning("⚠ WordNet installed but not functioning properly")
            return False
            
    except Exception as e:
        logger.error(f"✗ WordNet verification failed: {e}")
        return False

def status():
    """Check WordNet status with improved API compatibility"""
    try:
        import wn
        
        print("WordNet Status Report")
        print("=" * 25)
        
        # Get lexicons with error handling
        try:
            lexicons = wn.lexicons()
            print(f"Available lexicons: {len(lexicons)}")
            
            if not lexicons:
                print("  No lexicons found")
                print("  Run: setup-wordnet install")
                return False
            
            # Display lexicon information
            for lexicon in lexicons:
                try:
                    identifier, label = get_lexicon_info(lexicon)
                    print(f"  - {identifier}: {label}")
                except Exception as e:
                    print(f"  - Error reading lexicon: {e}")
                    
        except Exception as e:
            print(f"Error listing lexicons: {e}")
            return False
        
        # Test functionality with multiple approaches
        print(f"\nFunctionality test:")
        test_words = ['science', 'research', 'publication']
        
        for word in test_words:
            try:
                # Try multiple approaches to get synsets
                synsets = None
                
                # Method 1: Try with specific wordnet
                try:
                    if lexicons:
                        first_lexicon = lexicons[0]
                        identifier, _ = get_lexicon_info(first_lexicon)
                        en = wn.Wordnet(identifier)
                        synsets = en.synsets(word)
                except:
                    pass
                
                # Method 2: Try general function
                if not synsets:
                    try:
                        synsets = wn.synsets(word)
                    except:
                        pass
                
                if synsets:
                    print(f"  {word}: {len(synsets)} synsets ✓")
                else:
                    print(f"  {word}: No synsets found ⚠")
                    
            except Exception as e:
                print(f"  {word}: Error - {e}")
        
        print("\n✓ WordNet status check complete")
        return True
        
    except ImportError:
        print("✗ WordNet package not available")
        print("Install with: pip install wn")
        return False
    except Exception as e:
        print(f"✗ WordNet status check failed: {e}")
        return False

def main():
    """Main WordNet setup function"""
    parser = argparse.ArgumentParser(description="Setup WordNet for Science Live")
    parser.add_argument(
        'command',
        nargs='?',
        choices=['install', 'status', 'verify'],
        default='install',
        help='WordNet command (default: install)'
    )
    
    args = parser.parse_args()
    
    print("🧠 Science Live WordNet Setup")
    print("=" * 30)
    
    if args.command == 'status':
        return status()
    elif args.command == 'verify':
        return verify_installation()
    elif args.command == 'install':
        success = True
        
        if not check_wn_availability():
            return False
        
        if not download_wordnet_data():
            success = False
        
        if not verify_installation():
            success = False
        
        if success:
            print("\n✅ WordNet setup completed successfully!")
            print("\nNext steps:")
            print("  - Test: setup-wordnet status")
            print("  - Validate: validate-science-live --wordnet")
            print("  - Use enhanced features in your Science Live pipeline")
        else:
            print("\n❌ WordNet setup encountered issues")
            print("Try running individual commands:")
            print("  setup-wordnet status")
            print("  setup-wordnet verify")
        
        return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
