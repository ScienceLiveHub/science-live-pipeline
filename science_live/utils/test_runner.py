# =============================================================================
# science_live/utils/test_runner.py
# =============================================================================

"""
Test runner utility accessible via console script.
"""

import sys
import subprocess
import argparse

def main():
    """Test runner with different test suites"""
    parser = argparse.ArgumentParser(description="Science Live Test Runner")
    parser.add_argument('--fast', action='store_true', help='Run fast tests only')
    parser.add_argument('--wordnet', action='store_true', help='Run WordNet tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    
    args = parser.parse_args()
    
    if args.fast:
        cmd = "python -m pytest tests/ -v -m 'not slow and not integration'"
    elif args.wordnet:
        cmd = "python -m pytest tests/ -v -m 'requires_wordnet'"
    elif args.integration:
        cmd = "python -m pytest tests/ -v -m 'integration'"
    else:
        cmd = "python -m pytest tests/ -v"
    
    print(f"🧪 Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)


