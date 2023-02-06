import os
import json
import jsonschema   

from .core import load_definitions


def validate_definition(args) -> int:
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
    return validate(definitions_file, headers)

def validate(definitions_uri, headers):
    # load the definitions file
    definitions_file, docroot = load_definitions(definitions_uri, headers, False)
    if not docroot:
        print("Error: could not load definitions file {}".format(definitions_uri))
        return 2

    # validate the definitions file using the JSON schema in schemas/ce_registry_doc.json

    # load the schema
    schema_file = os.path.join(os.path.dirname(__file__), "schemas", "ce_registry_doc.json")
    with open(schema_file, "r") as f:
        schema = json.load(f)

    # validate the definitions file
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(docroot))
    if errors:
        print("{} Validation errors:".format(definitions_file))
        for i, error in enumerate(errors):
            print("at {}, {}".format(error.json_path, error.message))
        return 1
        
    print("OK: definitions file {} is valid".format(definitions_uri))
    return 0