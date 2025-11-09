# pylint: disable=wrong-import-position, line-too-long

""" Command line interface for the xregistry tool"""

import argparse
import logging
import sys

from xregistry.commands import catalog
from xregistry.commands.catalog import CatalogSubcommands, ManifestSubcommands
from xregistry.commands.config import add_config_subcommands

logging.basicConfig(level=logging.DEBUG if sys.gettrace() is not None else logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from .commands.validate_definitions import validate_definition
from .commands.generate_code import generate_code
from .commands.list_templates import list_templates
#from .commands.manifest import ManifestSubcommands

def main():
    """ Main function for the xregistry command line interface"""

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()
    
    # Add global model path argument
    parser.add_argument(
        "--model", 
        help="Path to custom model.json file or HTTP(S) URL. Can also use XREGISTRY_MODEL_PATH environment variable.",
        default=None
    )

    # the script accepts a set of commands, each with its own set of arguments
    # the first argument is the command name:
    #  generate: generates code from input definitions
    #  validate: validates an definition
    #  list: lists the available templates

    subparsers_parser = parser.add_subparsers(dest="command", help="The command to execute: generate, validate or list")
    subparsers_parser.default = "generate"
    generate_parser = subparsers_parser.add_parser("generate", help="Generate code.")
    generate_parser.set_defaults(func=generate_code)
    validate_parser = subparsers_parser.add_parser("validate", help="Validate a definition")
    validate_parser.set_defaults(func=validate_definition)
    list_parser = subparsers_parser.add_parser("list", help="List available templates")
    list_parser.set_defaults(func=list_templates)
    config_parser = subparsers_parser.add_parser("config", help="Manage configuration")
    add_config_subcommands(config_parser)
    manifest_parser = subparsers_parser.add_parser("manifest", help="Manage the manifest file")
    ManifestSubcommands.add_parsers(manifest_parser)
    subparsers_parser.required = True
    catalog_parser = subparsers_parser.add_parser("catalog", help="Manage the catalog")
    CatalogSubcommands.add_parsers(catalog_parser)    # Specify the arguments for the generate command
    generate_parser.add_argument("--projectname", dest="project_name", required=False, help="The project name (namespace name) for the output")
    generate_parser.add_argument("--schemaprojectname", dest="schema_project_name", required=False, help="The project name (namespace name) for schema classes (optional, defaults to projectname)")
    generate_parser.add_argument("--noschema", dest="no_schema", action="store_true", required=False, help="Do not generate schema classes (optional, defaults to false)")
    generate_parser.add_argument("--nocode", dest="no_code", action="store_true", required=False, help="Do not generate non-schema code like consumers or producers (optional, defaults to false)")
    generate_parser.add_argument("--language", dest="language", required=False, help="The language to use for the generated code")
    generate_parser.add_argument("--style", dest="style", required=False, help="The style of the generated code")
    generate_parser.add_argument("--output", dest="output_dir", required=False, help="The directory where the generated code should be saved")
    generate_parser.add_argument("--definitions", "--url", "-d", "-f", dest="definitions_files", nargs="+", required=True, help="One or more files or URLs containing the definitions. Files are loaded in order and stacked, with later files shadowing earlier ones.")
    generate_parser.add_argument("--requestheaders", nargs="*", dest="headers", required=False,help="Extra HTTP headers in the format 'key=value'")
    generate_parser.add_argument("--templates", nargs="*", dest="template_dirs", required=False, help="Paths of extra directories containing custom templates")
    generate_parser.add_argument("--template-args", nargs="*", dest="template_args", required=False, help="Extra template arguments to pass to the code generator in the form 'key=value")
    generate_parser.add_argument("--messagegroup", dest="messagegroup", required=False, help="Limit the generation to a specific message group")
    generate_parser.add_argument("--endpoint", dest="endpoint", required=False, help="Limit the generation to a specific endpoint")

    # specify the arguments for the validate command
    validate_parser.add_argument("--definitions", "-d", "-f", dest="definitions_files", nargs="+", required=True, help="One or more files or URLs containing the definitions. Files are loaded in order and stacked, with later files shadowing earlier ones.")
    validate_parser.add_argument("--requestheaders", nargs="*", dest="headers", required=False,help="Extra HTTP headers in the format 'key=value'")

    # specify the arguments for the list command
    list_parser.add_argument("--templates", nargs="*", dest="template_dirs", required=False, help="Paths of extra directories containing custom templates")
    list_parser.add_argument("--format", dest="listformat", required=False, help="Format for the output: text or json", choices=["text", "json"], default="text")

    # Parse the command line arguments
    args = parser.parse_args()
    if not 'func' in args:
        parser.print_help()
        return 1
    try:
        args.func(args)
        return 0
    except ValueError as e:
        print(f"Error: {e.args[0]}")
        return 1
