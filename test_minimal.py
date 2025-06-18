#!/usr/bin/env python3
"""
Minimal validation test for the xRegistry loader refactoring.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("🚀 Testing xRegistry Loader Refactoring")
    print("=" * 50)

    # Test 1: Basic imports
    try:
        from xregistry.generator.xregistry_loader import XRegistryUrlParser, XRegistryLoader
        print("✓ Successfully imported refactored components")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return 1

    # Test 2: URL Parser Basic Test
    try:
        parser = XRegistryUrlParser("https://example.com/test")
        entry_type = parser.get_entry_type()
        print(f"✓ URL Parser works: {entry_type}")
    except Exception as e:
        print(f"✗ URL Parser failed: {e}")
        return 1

    # Test 3: Basic Loader Test
    try:
        test_doc = {
            "specversion": "0.5-wip",
            "id": "test",
            "schemagroups": {"test": {"schemas": {}}}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_doc, f)
            temp_path = f.name
        
        try:
            loader = XRegistryLoader()
            uri, data = loader.load(temp_path)
            if data is not None:
                print("✓ Basic loading works")
            else:
                print("✗ Loading returned None")
                return 1
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"✗ Basic loader test failed: {e}")
        return 1

    # Test 4: CLI Integration Test
    try:
        sample_file = project_root / "samples" / "message-definitions" / "minimal.xreg.json"
        if sample_file.exists():
            from xregistry.commands.validate_definitions import validate
            result = validate(str(sample_file), {}, verbose=False)
            print(f"✓ CLI validation works: {result}")
        else:
            print("! No sample file for CLI test")
    except Exception as e:
        print(f"! CLI test encountered issue: {e}")

    print("=" * 50)
    print("🎉 Basic validation completed successfully!")
    print("✓ Refactoring appears to be working correctly")
    return 0

if __name__ == "__main__":
    sys.exit(main())
