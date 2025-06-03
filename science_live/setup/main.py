# =============================================================================
# science_live/setup/main.py
# =============================================================================

"""
Main setup command that provides an interactive menu for all setup options.
"""

import sys
import argparse

def main():
    """Main setup command with interactive menu"""
    
    parser = argparse.ArgumentParser(
        description="Science Live Setup - Choose your setup option",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available setup commands:
  science-live-setup-wordnet    Setup WordNet for enhanced NLP
  science-live-setup-dev        Setup development environment
  science-live-validate         Validate installation
  
Or use the aliases:
  setup-wordnet                 Setup WordNet
  setup-dev                     Setup development environment
  validate-science-live         Validate installation
        """
    )
    
    parser.add_argument(
        'action',
        nargs='?',
        choices=['wordnet', 'dev', 'validate', 'help'],
        default='help',
        help='Setup action to perform'
    )
    
    args = parser.parse_args()
    
    if args.action == 'help':
        parser.print_help()
        print("\n🚀 Science Live Setup")
        print("=" * 30)
        print("Choose what you'd like to set up:")
        print("  wordnet   - Setup WordNet for enhanced question processing")
        print("  dev       - Setup complete development environment")
        print("  validate  - Validate current installation")
        print()
        print("Examples:")
        print("  science-live-setup wordnet")
        print("  science-live-setup dev")
        print("  science-live-setup validate")
        return
    
    elif args.action == 'wordnet':
        from .wordnet import main as wordnet_main
        return wordnet_main()
    
    elif args.action == 'dev':
        from .dev import main as dev_main
        return dev_main()
    
    elif args.action == 'validate':
        from .validate import main as validate_main
        return validate_main()

if __name__ == "__main__":
    main()
