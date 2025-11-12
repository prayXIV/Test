#!/usr/bin/env python3
"""
Run all RSS feed generators
"""

import os
import sys
import importlib.util
from pathlib import Path

def run_all_feeds():
    """Execute all feed generator scripts in feed_generators/ directory"""
    
    # Add project root to Python path for absolute imports
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    feed_generators_dir = project_root / 'feed_generators'
    
    if not feed_generators_dir.exists():
        print(f"Error: {feed_generators_dir} directory not found")
        sys.exit(1)
    
    # Get all Python files in feed_generators directory (excluding __init__.py and utility files)
    feed_files = [f for f in feed_generators_dir.glob('*.py') 
                  if f.name not in ['__init__.py', 'date_utils.py']]
    
    if not feed_files:
        print("No feed generator scripts found")
        sys.exit(1)
    
    print(f"Found {len(feed_files)} feed generator(s)")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    
    for feed_file in sorted(feed_files):
        print(f"\nRunning: {feed_file.name}")
        try:
            # Load and execute the module
            spec = importlib.util.spec_from_file_location(feed_file.stem, feed_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Call the generate_feed function
            if hasattr(module, 'generate_feed'):
                module.generate_feed()
                success_count += 1
                print(f"✓ Successfully generated feed from {feed_file.name}")
            else:
                print(f"✗ {feed_file.name} does not have a generate_feed() function")
                error_count += 1
                
        except Exception as e:
            print(f"✗ Error running {feed_file.name}: {e}")
            error_count += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Summary: {success_count} succeeded, {error_count} failed")
    print("=" * 50)
    
    if error_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_all_feeds()

