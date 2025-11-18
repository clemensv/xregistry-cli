# xRegistry Model Schema Management

This directory contains tools for managing and validating the xRegistry model schema files.

## Files

### Schema Files

- **`_model.json`**: JSON Schema definition (meta-schema) that defines the structure of xRegistry models
- **`endpoint.json`**: Domain-specific schema for endpoint groups
- **`message.json`**: Domain-specific schema for messagegroup and message resources
- **`schema.json`**: Domain-specific schema for schemagroup and schema resources
- **`model.json`**: **Canonical model file** containing the complete merged model with all attributes and groups

###{
 Scripts

### `merge_model_schemas.py`

Merges domain-specific schema files into `model.json`. **By default, this script fetches the latest schema definitions directly from the xregistry/spec GitHub repository** to ensure consistency with the upstream canonical definitions.

This script:

- **Fetches schema files from https://github.com/xregistry/spec** (endpoint, message, schema model.json files)
- Preserves all registry-level attributes from `model.json`
- Preserves existing group definitions and their core attributes
- Updates/adds domain-specific attributes from upstream schema files
- Resolves `$include` references between schema files
- Adds `plural` fields where missing
- Creates a backup at `model.json.backup` before making changes

**Usage:**
```bash
# Default: Fetch from GitHub
python tools/merge_model_schemas.py

# Use local schema files instead
python tools/merge_model_schemas.py --local
```

**Important Notes:**
- `model.json` is the canonical source of truth for this repository
- Schema files are fetched from https://github.com/xregistry/spec/main/{domain}/model.json
- Use `--local` flag only if you have local modifications to test
- The script does NOT resolve `ximportresources` directives - these must be manually expanded
- Core model attributes (endpointid, self, xid, etc.) are preserved from existing model.json

### `validate_model_schemas.py`

Validates that `model.json` is consistent with the domain schema files. This script checks:

- All groups defined in schema files exist in `model.json`
- All domain-specific attributes from schema files are present in `model.json`
- Structure and naming consistency

**Usage:**
```bash
python tools/validate_model_schemas.py
```

## Workflow

### When Schema Files Are Updated

1. Edit the domain-specific schema files (endpoint.json, message.json, or schema.json)
2. Run `merge_model_schemas.py` to update `model.json` with the changes
3. Run `validate_model_schemas.py` to verify consistency
4. Review the changes in `model.json` and ensure tests pass
5. Commit both the schema files and updated `model.json`

### When model.json Is Updated Directly

1. Edit `model.json` as needed
2. Run `validate_model_schemas.py` to ensure consistency with schema files
3. If validation fails, either:
   - Update the schema files to match `model.json`, or
   - Run `merge_model_schemas.py` to bring in changes from schema files

## Schema File Structure

### endpoint.json
- Defines the `endpoints` group
- References `messagegroups` via `$include` from message.json
- Contains endpoint-specific attributes like `usage`, `channel`, `protocol`
- Uses `ximportresources` to include message resources

### message.json
- Defines the `messagegroups` group
- Contains the nested `messages` resource definition
- Includes message-specific attributes like `envelope`, `protocol`
- Defines extensive CloudEvents metadata structures

### schema.json
- Defines the `schemagroups` group
- Contains the nested `schemas` resource definition
- Includes schema format and validation attributes

## Core vs. Domain Attributes

### Core Attributes
These are common to all resources and defined in `model.json`:
- `{resource}id` (e.g., endpointid, messagegroupid, schemagroupid)
- `self`, `xid`, `epoch`
- `name`, `description`, `documentation`
- `labels`
- `createdat`, `modifiedat`
- `deprecated`

### Domain Attributes
These are specific to each domain and defined in the schema files:
- **Endpoints**: `usage`, `channel`, `protocol`, `protocoloptions`
- **Messagegroups**: `envelope`, `protocol`, `envelopeoptions`
- **Messages**: `basemessageurl`, `format`, `schemaurl`, `schemaformat`
- **Schemagroups**: Generic container for schemas
- **Schemas**: `format`, validation metadata

## Troubleshooting

### Merge Script Updates Attributes Unexpectedly

The schema files may have been updated with newer definitions. Review the changes and:
- If schema files are correct: Accept the merge and update tests if needed
- If model.json is correct: Update the schema files to match

### Validation Fails After Manual Edit

Check that:
- All `singular` and `plural` fields are correctly set
- Domain-specific attributes from schema files are present
- Group names match between model.json and schema files

### Tests Fail After Merge

This usually indicates:
- Schema files have evolved (e.g., type changed from string to array)
- Tests need to be updated to match new schema
- Or schema files need to be reverted to match tests

The merge script is revealing a synchronization issue - this is expected and helpful for maintaining consistency.
