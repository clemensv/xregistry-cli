# pylint: disable=line-too-long

""" Validate the definitions file using the JSON schema in schemas/xregistry_messaging_catalog.json"""

import os
import json
import jsonschema

from xregistry.generator.xregistry_loader import XRegistryLoader


def validate_definition(args) -> int:
    """Validate the definitions file using the JSON schema in schemas/xregistry_messaging_catalog.json"""
    definitions_files = args.definitions_files if isinstance(args.definitions_files, list) else [args.definitions_files]
    
    if args.headers:
        # ok to have = in base64 values
        headers = {
            header.split("=", 1)[0]: header.split("=", 1)[1]
            for header in args.headers
        }
    else:
        headers = {}

    # Call the validate() function with the parsed arguments
    return validate(definitions_files, headers, True)


def validate(definitions_uris, headers, verbose=False):
    """Validate the definitions file(s) using the JSON schema in schemas/xregistry_messaging_catalog.json
    
    Args:
        definitions_uris: A single URI string or a list of URI strings to load and stack
        headers: HTTP headers for authentication
        verbose: Whether to print verbose output
    
    Returns:
        0 on success, 1 on validation error, 2 on load error
    """
    # Normalize to list
    if isinstance(definitions_uris, str):
        definitions_uris = [definitions_uris]
    
    # load the definitions file(s)
    loader = XRegistryLoader()
    
    if len(definitions_uris) == 1:
        definitions_file, docroot = loader.load(definitions_uris[0], headers, False, True)
        display_name = definitions_uris[0]
    else:
        definitions_file, docroot = loader.load_stacked(definitions_uris, headers, False, True)
        display_name = " + ".join(definitions_uris)
    
    if not docroot:
        print(f"Error: could not load definitions file(s) {display_name}")
        return 2
    
    try:
        basepath = os.path.realpath(
            os.path.join(os.path.dirname(__file__), ".."))
        schema_file = os.path.join(basepath, "schemas", "document-schema.json")
        with open(schema_file, "r", encoding='utf-8') as f:
            schema = json.load(f)
    except IOError as e:
        print(f"Error: could not load schema file {schema_file}: {e}")
        return 2
    except json.JSONDecodeError as e:
        print(f"Error: could not parse schema file {schema_file}: {e}")
        return 2

    # validate the definitions file
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(docroot))
    if errors:
        print(f"{definitions_file} Validation errors:")
        for _, error in enumerate(errors):
            print(f"! at {error.json_path}: {error.message}")
            for suberror in sorted(error.context, key=lambda e: e.schema_path):
                print(f"> at {suberror.json_path}: {suberror.message}")
        return 1

    if verbose:
        print(f"OK: definitions file(s) {display_name} is valid")
    return 0
