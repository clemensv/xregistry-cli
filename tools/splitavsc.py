import json
import os
import argparse

def load_schema(file_path):
    """Load the schema from a given file path."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_schema(schema, file_path):
    """Save the schema to a given file path."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)

def extract_schemas(schema, all_schemas, current_namespace=None):
    """Recursively extract all named schemas and enums."""
    if isinstance(schema, dict):
        if 'namespace' in schema:
            current_namespace = schema['namespace']
        if 'name' in schema:
            full_name = f"{current_namespace}.{schema['name']}".strip('.')
            all_schemas[full_name] = schema
        if 'fields' in schema:
            for field in schema['fields']:
                extract_schemas(field['type'], all_schemas, current_namespace)
        if 'symbols' in schema:
            return  # Enum type, already handled
        if 'items' in schema:
            extract_schemas(schema['items'], all_schemas, current_namespace)
        if 'values' in schema:
            extract_schemas(schema['values'], all_schemas, current_namespace)
        if 'type' in schema and isinstance(schema['type'], dict):
            extract_schemas(schema['type'], all_schemas, current_namespace)
        if 'type' in schema and isinstance(schema['type'], list):
            for item in schema['type']:
                extract_schemas(item, all_schemas, current_namespace)
    elif isinstance(schema, list):
        for item in schema:
            extract_schemas(item, all_schemas, current_namespace)

def inline_dependencies(schema, all_schemas, inlined_schemas=None, current_namespace=None):
    """Inline dependencies for a given schema."""
    if inlined_schemas is None:
        inlined_schemas = set()
    
    if isinstance(schema, list):
        return [inline_dependencies(item, all_schemas, inlined_schemas, current_namespace) for item in schema]

    if isinstance(schema, dict):
        if 'namespace' in schema:
            current_namespace = schema['namespace']
        
        if 'type' in schema:
            if schema['type'] == 'record' or schema['type'] == 'enum':
                name = schema['name']
                full_name = f"{current_namespace}.{name}" if current_namespace else name
                if full_name in inlined_schemas:
                    return full_name
                inlined_schemas.add(full_name)
                if 'fields' in schema:
                    fields = schema.get('fields', [])
                    for field in fields:
                        field['type'] = inline_dependencies(field['type'], all_schemas, inlined_schemas, current_namespace)
            elif isinstance(schema['type'], list):
                schema['type'] = inline_dependencies(schema['type'], all_schemas, inlined_schemas, current_namespace)
            elif isinstance(schema['type'], dict):
                schema['type'] = inline_dependencies(schema['type'], all_schemas, inlined_schemas, current_namespace)
            else:
                full_name = schema['type']
                if full_name in all_schemas:
                    ref_schema = all_schemas[full_name]
                    schema = inline_dependencies(ref_schema, all_schemas, inlined_schemas, current_namespace)
        return schema

    elif isinstance(schema, str):
        full_name = schema
        if full_name in all_schemas:
            if full_name in inlined_schemas:
                return full_name
            ref_schema = all_schemas[full_name]
            return inline_dependencies(ref_schema, all_schemas, inlined_schemas, current_namespace)

    return schema

def break_up_union_schema(union_schema):
    """Break up the union schema into individual AVSC files with inlined dependencies."""
    all_schemas = {}
    extract_schemas(union_schema, all_schemas)
    
    for schema in union_schema:
        if 'name' in schema:
            inlined_schema = inline_dependencies(schema, all_schemas)
            file_name = f"{schema['name']}.avsc"
            save_schema(inlined_schema, os.path.join(output_dir, file_name))

def main():
    parser = argparse.ArgumentParser(description='Break up a union Avro schema into individual self-contained AVSC files.')
    parser.add_argument('--input', required=True, help='Input union schema file path')
    parser.add_argument('--output', required=True, help='Output directory for individual AVSC files')

    args = parser.parse_args()

    global output_dir
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    union_schema = load_schema(args.input)
    break_up_union_schema(union_schema)

if __name__ == '__main__':
    main()
