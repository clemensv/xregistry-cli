# pylint: disable=line-too-long

"""Generate code from the given arguments. """

from typing import Any, Dict, List, Union
from xregistry.cli import logger
from xregistry.generator.generator_context import GeneratorContext
from xregistry.generator.schema_utils import SchemaUtils
from xregistry.generator.template_renderer import TemplateRenderer
from .validate_definitions import validate

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, None]

def generate_code(args: Any) -> int:
    """Generate code from the given arguments."""
    suppress_schema_output = args.no_schema
    suppress_code_output = args.no_code
    messagegroup_filter = args.messagegroup

    headers = {header.split("=", 1)[0]: header.split("=", 1)[1] for header in args.headers} if args.headers else {}

    template_args = {}
    if args.template_args:
        for arg in args.template_args:
            key, value = arg.split("=", 1)
            template_args[key] = value

    generator_context = GeneratorContext(args.output_dir, messagegroup_filter)

    SchemaUtils.schema_files_collected = set()
    generator_context.loader.reset_schemas_handled()
    SchemaUtils.schema_references_collected = set()
    generator_context.loader.set_current_url(None)

    try:
        if validate(args.definitions_file, headers, False) != 0:
            return 1
        
        renderer = TemplateRenderer(generator_context,
            args.project_name, args.language, args.style, args.output_dir,
            args.definitions_file, headers, args.template_dirs, template_args,
            suppress_code_output, suppress_schema_output
        )
        renderer.generate()

        for schema in SchemaUtils.schema_files_collected:
            renderer = TemplateRenderer(generator_context,
                args.project_name, args.language, args.style, args.output_dir,
                schema, headers, args.template_dirs, template_args,
                suppress_code_output, suppress_schema_output
            )
            renderer.generate()

        if generator_context.stacks.stack("files"):
            for file, content in generator_context.stacks.stack("files"):
                with open(file, "w", encoding='utf-8') as f:
                    f.write(content)
    except SystemExit:
        return 1
    except Exception as err:
        logger.error("%s", err)
        raise err
    return 0
