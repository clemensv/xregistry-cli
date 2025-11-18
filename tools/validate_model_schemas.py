#!/usr/bin/env python3
"""
Validate that model.json is consistent with the domain schema files.

This script verifies that:
1. All groups defined in endpoint.json, message.json, and schema.json exist in model.json
2. All domain-specific attributes from schema files are present in model.json
3. The structure is consistent

This validation helps ensure model.json stays in sync with the domain schema files.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

def load_json(filepath: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_group(group_name: str, schema_group: Dict[str, Any], model_group: Dict[str, Any]) -> List[str]:
    """
    Validate that a group in model.json matches the schema definition.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check singular/plural
    if 'singular' in schema_group and schema_group['singular'] != model_group.get('singular'):
        errors.append(f"  {group_name}: singular mismatch - schema has '{schema_group['singular']}', model has '{model_group.get('singular')}'")
    
    # Check attributes from schema are in model
    if 'attributes' in schema_group:
        schema_attrs = set(schema_group['attributes'].keys())
        model_attrs = set(model_group.get('attributes', {}).keys())
        
        missing = schema_attrs - model_attrs
        if missing:
            errors.append(f"  {group_name}: missing attributes in model.json: {sorted(missing)}")
    
    # Check resources
    if 'resources' in schema_group:
        model_resources = model_group.get('resources', {})
        for resource_name, schema_resource in schema_group['resources'].items():
            if resource_name not in model_resources:
                errors.append(f"  {group_name}/{resource_name}: resource missing in model.json")
                continue
            
            model_resource = model_resources[resource_name]
            
            # Check resource attributes
            if 'attributes' in schema_resource:
                schema_res_attrs = set(schema_resource['attributes'].keys())
                model_res_attrs = set(model_resource.get('attributes', {}).keys())
                
                missing = schema_res_attrs - model_res_attrs
                if missing:
                    errors.append(f"  {group_name}/{resource_name}: missing attributes: {sorted(missing)}")
    
    return errors

def main():
    """Main validation function."""
    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    schemas_dir = repo_root / 'xregistry' / 'schemas'
    
    # Validate paths
    if not schemas_dir.exists():
        print(f"ERROR: Schemas directory not found: {schemas_dir}", file=sys.stderr)
        return 1
    
    required_files = ['model.json', 'endpoint.json', 'message.json', 'schema.json']
    for filename in required_files:
        filepath = schemas_dir / filename
        if not filepath.exists():
            print(f"ERROR: Required file not found: {filepath}", file=sys.stderr)
            return 1
    
    print(f"Validating model.json against schema files in: {schemas_dir}\n")
    
    try:
        # Load files
        model = load_json(schemas_dir / 'model.json')
        endpoint_schema = load_json(schemas_dir / 'endpoint.json')
        message_schema = load_json(schemas_dir / 'message.json')
        schema_schema = load_json(schemas_dir / 'schema.json')
        
        # Collect all schema definitions
        schema_groups = {}
        for schema_file, schema_data in [
            ('endpoint.json', endpoint_schema),
            ('message.json', message_schema),
            ('schema.json', schema_schema)
        ]:
            if 'groups' in schema_data:
                for group_name, group_def in schema_data['groups'].items():
                    # Skip $include references for now
                    if isinstance(group_def, dict) and '$include' not in group_def:
                        if group_name in schema_groups:
                            print(f"WARNING: {group_name} defined in multiple schema files")
                        schema_groups[group_name] = (schema_file, group_def)
        
        # Validate each schema group against model
        all_errors = []
        model_groups = model.get('groups', {})
        
        for group_name, (schema_file, schema_group) in schema_groups.items():
            if group_name not in model_groups:
                all_errors.append(f"  {group_name}: defined in {schema_file} but missing from model.json")
                continue
            
            errors = validate_group(group_name, schema_group, model_groups[group_name])
            all_errors.extend(errors)
        
        # Report results
        if all_errors:
            print("VALIDATION ERRORS:\n")
            for error in all_errors:
                print(error)
            print(f"\nTotal errors: {len(all_errors)}")
            return 1
        else:
            print("✓ All validations passed")
            print(f"  - Validated {len(schema_groups)} groups")
            print(f"  - Groups: {', '.join(sorted(schema_groups.keys()))}")
            return 0
        
    except Exception as e:
        print(f"\nERROR during validation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
