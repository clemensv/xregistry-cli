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
    return validate(definitions_file, headers, True)

def validate(definitions_uri, headers, verbose=False):
    # load the definitions file
    definitions_file, docroot = load_definitions(definitions_uri, headers, False, True)
    if not docroot:
        print("Error: could not load definitions file {}".format(definitions_uri))
        return 2

    # validate the definitions file using the JSON schema in schemas/xregistry_messaging_catalog.json

    # load the schema
    try:
        basepath = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
        schema_file = os.path.join(basepath, "schemas", "document-schema.json")
        with open(schema_file, "r") as f:
            schema = json.load(f)
    except IOError as e:
        print("Error: could not load schema file {}: {}".format(schema_file, e))
        return 2
    except json.JSONDecodeError as e:
        print("Error: could not parse schema file {}: {}".format(schema_file, e))
        return 2
    

    # validate the definitions file
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(docroot))
    if errors:
        print("{} Validation errors:".format(definitions_file))
        for i, error in enumerate(errors):
            print("! at {}: {}".format(error.json_path, error.message))
            for suberror in sorted(error.context, key=lambda e: e.schema_path):
                print("> at {}: {}".format(suberror.json_path, suberror.message))
        return 1
        
    if verbose:
        print("OK: definitions file {} is valid".format(definitions_uri))
    return 0