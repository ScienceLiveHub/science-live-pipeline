# =============================================================================
# science_live/setup/dev.py  
# =============================================================================

"""
Development environment setup module.
"""

import sys
import subprocess
import argparse

def run_command(cmd, description, required=True):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description}")
        return True
    except subprocess.CalledProcessError as e:
        if required:
            print(f"✗ {description} failed: {e}")
            if e.stderr:
                print(f"Error: {e.stderr}")
        else:
            print(f"⚠ {description} failed (optional): {e}")
        return not required

def main():
    """Main development setup function"""
    parser = argparse.ArgumentParser(description="Setup Science Live development environment")
    parser.add_argument('--wordnet', action='store_true', help='Include WordNet setup')
    parser.add_argument('--minimal', action='store_true', help='Minimal setup only')
    
    args = parser.parse_args()
    
    print("🚀 Science Live Development Setup")
    print("=" * 35)
    
    success = True
    
    # Core installation
    if not run_command("pip install -e .", "Installing Science Live in development mode"):
        success = False
    
    if not run_command("pip install -e .[dev]", "Installing development dependencies"):
        success = False
    
    # WordNet setup (unless minimal)
    if not args.minimal and (args.wordnet or True):  # Default to including WordNet
        if not run_command("pip install -e .[enhanced]", "Installing enhanced NLP dependencies"):
            success = False
        
        # Setup WordNet data
        print("🧠 Setting up WordNet...")
        try:
            from .wordnet import main as wordnet_main
            if not wordnet_main():
                success = False
        except Exception as e:
            print(f"✗ WordNet setup failed: {e}")
            success = False
    
    # Optional: pre-commit hooks
    run_command("pre-commit install", "Setting up pre-commit hooks", required=False)
    
    # Test installation
    print("🧪 Testing installation...")
    try:
        from science_live.pipeline import ScienceLivePipeline
        print("✓ Science Live pipeline import successful")
    except Exception as e:
        print(f"✗ Pipeline import failed: {e}")
        success = False
    
    print("\n" + "=" * 35)
    if success:
        print("✅ Development environment ready!")
        print("\nNext steps:")
        print("  - Run tests: python -m pytest")
        print("  - Check WordNet: setup-wordnet status")
        print("  - Validate: validate-science-live")
    else:
        print("❌ Setup completed with issues")
    
    return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1)


