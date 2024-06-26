# pylint: disable=line-too-long

""" Validate the definitions file using the JSON schema in schemas/xregistry_messaging_catalog.json"""

import os
import json
import jsonschema

from xregistry.generator.xregistry_loader import XRegistryLoader


def validate_definition(args) -> int:
    """Validate the definitions file using the JSON schema in schemas/xregistry_messaging_catalog.json"""
    if args.definitions_file:
        definitions_file = args.definitions_file
    if args.headers:
        # ok to have = in base64 values
        headers = {
            header.split("=", 1)[0]: header.split("=", 1)[1]
            for header in args.headers
        }
    else:
        headers = {}

    # Call the validate() function with the parsed arguments
    return validate(definitions_file, headers, True)


def validate(definitions_uri, headers, verbose=False):
    """Validate the definitions file using the JSON schema in schemas/xregistry_messaging_catalog.json"""
    # load the definitions file
    loader = XRegistryLoader()
    definitions_file, docroot = loader.load(
        definitions_uri, headers, False, True)
    if not docroot:
        print(f"Error: could not load definitions file {definitions_uri}")
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
        print(f"OK: definitions file {definitions_uri} is valid")
    return 0
