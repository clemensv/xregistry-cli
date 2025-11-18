#!/usr/bin/env python3
"""
Merge script for xRegistry model schema files.

IMPORTANT: This script sources the canonical schema files directly from the
xregistry/spec GitHub repository and merges them with the local model.json.

What this script does:
1. Downloads schema files from https://github.com/xregistry/spec
2. Preserves all registry-level attributes from local model.json
3. Preserves all existing group definitions and their core attributes
4. Updates/adds domain-specific attributes from upstream schema files
5. Resolves $include references
6. Adds plural fields where missing

What this script does NOT do:
- Resolve ximportresources (these must be manually expanded)
- Generate core model attributes (endpointid, self, xid, etc.) - these are preserved from existing model.json
- Handle complex schema transformations

Usage:
    python tools/merge_model_schemas.py [--local]
    
    --local: Use local xregistry/schemas/*.json files instead of fetching from GitHub

The script will create a backup at xregistry/schemas/model.json.backup before making changes.
"""

import json
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

# GitHub raw content URLs for xregistry/spec schema files
SCHEMA_BASE_URL = "https://raw.githubusercontent.com/xregistry/spec/main"
ENDPOINT_SCHEMA_URL = f"{SCHEMA_BASE_URL}/endpoint/model.json"
MESSAGE_SCHEMA_URL = f"{SCHEMA_BASE_URL}/message/model.json"
SCHEMA_SCHEMA_URL = f"{SCHEMA_BASE_URL}/schema/model.json"

def fetch_json_from_url(url: str) -> Dict[str, Any]:
    """
    Fetch and parse JSON from a URL.
    
    Args:
        url: URL to fetch JSON from
        
    Returns:
        Parsed JSON data
    """
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')
            return json.loads(content)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")

def load_json(filepath: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], filepath: Path) -> None:
    """Save data to a JSON file with pretty formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')

def add_plural_field(group_name: str, group_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add the 'plural' field to a group or resource definition if it's missing.
    The plural field is derived from the group/resource key name.
    
    Args:
        group_name: The key name (e.g., 'endpoints', 'messages')
        group_def: The group/resource definition dictionary
        
    Returns:
        Updated definition with plural field
    """
    if isinstance(group_def, dict) and 'singular' in group_def:
        if 'plural' not in group_def:
            group_def = dict(group_def)
            group_def['plural'] = group_name
        
        # Also handle resources
        if 'resources' in group_def and isinstance(group_def['resources'], dict):
            resources_updated = False
            for resource_name, resource_def in group_def['resources'].items():
                if isinstance(resource_def, dict) and 'singular' in resource_def:
                    if 'plural' not in resource_def:
                        if not resources_updated:
                            group_def = dict(group_def)
                            group_def['resources'] = dict(group_def['resources'])
                            resources_updated = True
                        resource_copy = dict(resource_def)
                        resource_copy['plural'] = resource_name
                        group_def['resources'][resource_name] = resource_copy
    
    return group_def

def resolve_include(include_ref: str, source_groups: Dict[str, Any]) -> Any:
    """
    Resolve an $include reference like '../message/model.json#/groups/messagegroups'
    
    Args:
        include_ref: The $include reference string
        source_groups: Dictionary of all available groups
        
    Returns:
        The resolved group definition
    """
    if '#' in include_ref:
        path_part, json_pointer = include_ref.split('#', 1)
        if json_pointer.startswith('/groups/'):
            group_name = json_pointer.split('/')[-1]
            if group_name in source_groups:
                return source_groups[group_name]
            else:
                raise ValueError(f"Cannot resolve $include: {include_ref} - group '{group_name}' not found")
        else:
            raise ValueError(f"Unsupported $include JSON pointer: {json_pointer}")
    else:
        raise ValueError(f"Invalid $include format: {include_ref}")

def merge_schema_groups(endpoint_data: Dict[str, Any], message_data: Dict[str, Any], 
                       schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge group definitions from schema files, resolving $include references.
    
    Args:
        endpoint_data: Content from endpoint.json
        message_data: Content from message.json
        schema_data: Content from schema.json
        
    Returns:
        Merged groups dictionary from schema files only
    """
    # First pass: collect all concrete group definitions
    all_groups = {}
    
    if 'groups' in message_data:
        for group_name, group_def in message_data['groups'].items():
            all_groups[group_name] = add_plural_field(group_name, group_def)
    
    if 'groups' in schema_data:
        for group_name, group_def in schema_data['groups'].items():
            all_groups[group_name] = add_plural_field(group_name, group_def)
    
    if 'groups' in endpoint_data:
        for group_name, group_def in endpoint_data['groups'].items():
            if not (isinstance(group_def, dict) and '$include' in group_def):
                all_groups[group_name] = add_plural_field(group_name, group_def)
    
    # Second pass: resolve $include references
    merged_groups = {}
    if 'groups' in endpoint_data:
        for group_name, group_def in endpoint_data['groups'].items():
            if isinstance(group_def, dict) and '$include' in group_def:
                include_ref = group_def['$include']
                resolved_group = resolve_include(include_ref, all_groups)
                resolved_group = add_plural_field(group_name, resolved_group)
                merged_groups[group_name] = resolved_group
            else:
                merged_groups[group_name] = all_groups[group_name]
    
    # Add groups not in endpoint.json
    for group_name, group_def in all_groups.items():
        if group_name not in merged_groups:
            merged_groups[group_name] = group_def
    
    return merged_groups

def merge_model_files(schemas_dir: Path, use_local: bool = False) -> Dict[str, Any]:
    """
    Merge schema files with existing model.json.
    
    Strategy:
    1. Use existing model.json as the base (contains core attributes)
    2. Load schema files from GitHub or local directory
    3. For each group, merge existing core attributes with schema attributes
    4. Preserve existing structure while updating from schemas
    
    Args:
        schemas_dir: Path to the xregistry/schemas directory
        use_local: If True, use local schema files; if False, fetch from GitHub
        
    Returns:
        Merged model data
    """
    # Load local model file
    model_file = schemas_dir / 'model.json'
    current_model = load_json(model_file)
    
    # Load schema files from GitHub or local directory
    if use_local:
        print("Using local schema files...")
        endpoint_data = load_json(schemas_dir / 'endpoint.json')
        message_data = load_json(schemas_dir / 'message.json')
        schema_data = load_json(schemas_dir / 'schema.json')
    else:
        print("Fetching schema files from xregistry/spec GitHub repository...")
        print(f"  - {ENDPOINT_SCHEMA_URL}")
        endpoint_data = fetch_json_from_url(ENDPOINT_SCHEMA_URL)
        print(f"  - {MESSAGE_SCHEMA_URL}")
        message_data = fetch_json_from_url(MESSAGE_SCHEMA_URL)
        print(f"  - {SCHEMA_SCHEMA_URL}")
        schema_data = fetch_json_from_url(SCHEMA_SCHEMA_URL)
        print()
    
    # Start with current model structure
    merged_model = {
        "$schema": current_model.get("$schema", "https://xregistry.io/xregistryspecs/core-v1/schemas/model.schema.json")
    }
    
    # Preserve registry-level attributes
    if 'attributes' in current_model:
        merged_model['attributes'] = current_model['attributes']
    
    # Get existing groups and schema groups
    existing_groups = current_model.get('groups', {})
    schema_groups = merge_schema_groups(endpoint_data, message_data, schema_data)
    
    # Merge: keep existing group structure but update with schema attributes
    # Preserve the order from existing model.json
    final_groups = {}
    
    # First, process groups in the order they appear in existing model
    for group_name in existing_groups.keys():
        if group_name in schema_groups:
            # Merge both
            existing = existing_groups[group_name]
            schema = schema_groups[group_name]
            
            merged_group = dict(existing)  # Start with existing
            
            # Update metadata from schema
            for key in ['singular', 'modelversion', 'compatiblewith']:
                if key in schema:
                    merged_group[key] = schema[key]
            
            # Ensure plural exists
            if 'plural' not in merged_group and 'singular' in merged_group:
                merged_group['plural'] = group_name
            
            # Merge attributes: keep existing, add/update from schema
            if 'attributes' in merged_group and 'attributes' in schema:
                merged_attrs = dict(merged_group['attributes'])
                merged_attrs.update(schema['attributes'])
                merged_group['attributes'] = merged_attrs
            elif 'attributes' in schema:
                merged_group['attributes'] = schema['attributes']
            
            # Keep existing resources (schema files use ximportresources which is not expanded here)
            # Don't overwrite with ximportresources from schema
            
            final_groups[group_name] = merged_group
        else:
            # Only in existing - keep it
            final_groups[group_name] = existing_groups[group_name]
    
    # Then, add any new groups from schema that weren't in existing
    for group_name in schema_groups.keys():
        if group_name not in final_groups:
            # Only in schema - add it (but it will be incomplete without core attrs)
            print(f"WARNING: Group '{group_name}' from schema files has no existing definition - may be incomplete")
            final_groups[group_name] = schema_groups[group_name]
    
    merged_model['groups'] = final_groups
    
    return merged_model

def main():
    """Main execution function."""
    # Parse command-line arguments
    use_local = '--local' in sys.argv
    
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    schemas_dir = repo_root / 'xregistry' / 'schemas'
    
    # Validate paths
    if not schemas_dir.exists():
        print(f"ERROR: Schemas directory not found: {schemas_dir}", file=sys.stderr)
        return 1
    
    model_file = schemas_dir / 'model.json'
    if not model_file.exists():
        print(f"ERROR: model.json not found: {model_file}", file=sys.stderr)
        return 1
    
    # Only check for local schema files if --local flag is used
    if use_local:
        required_files = ['endpoint.json', 'message.json', 'schema.json']
        for filename in required_files:
            filepath = schemas_dir / filename
            if not filepath.exists():
                print(f"ERROR: Required file not found: {filepath}", file=sys.stderr)
                return 1
    
    print(f"Merging schema files into: {schemas_dir}/model.json\n")
    
    try:
        merged_model = merge_model_files(schemas_dir, use_local=use_local)
        
        # Create backup
        backup_file = schemas_dir / 'model.json.backup'
        backup_file.write_text(model_file.read_text(encoding='utf-8'), encoding='utf-8')
        print(f"Created backup: {backup_file}")
        
        # Save merged model
        save_json(merged_model, model_file)
        print(f"Saved merged model to: {model_file}")
        
        # Print statistics
        group_count = len(merged_model.get('groups', {}))
        attr_count = len(merged_model.get('attributes', {}))
        print(f"\nMerge complete:")
        print(f"  - Registry attributes: {attr_count}")
        print(f"  - Groups: {group_count}")
        
        if 'groups' in merged_model:
            print(f"  - Group names: {', '.join(sorted(merged_model['groups'].keys()))}")
        
        print("\nRecommendation: Run 'python tools/validate_model_schemas.py' to verify consistency")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR during merge: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
