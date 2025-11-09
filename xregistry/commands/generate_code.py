# pylint: disable=line-too-long

"""Generate code from the given arguments. """

from typing import Any, Dict, List, Union
from xregistry.cli import logger
from xregistry.generator.generator_context import GeneratorContext
from xregistry.generator.schema_utils import SchemaUtils
from xregistry.generator.template_renderer import TemplateRenderer
from xregistry.common.config import config_manager
from .validate_definitions import validate

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, None]

def generate_code(args: Any) -> int:
    """Generate code from the given arguments."""
    # Load configuration for potential defaults
    config = config_manager.load_config()
    
    # Apply configuration defaults where CLI arguments are not provided
    project_name = args.project_name
    if not project_name and config.defaults.project_name:
        project_name = config.defaults.project_name
        logger.info(f"Using project name from config: {project_name}")
    
    language = args.language
    if not language and config.defaults.language:
        language = config.defaults.language
        logger.info(f"Using language from config: {language}")
    
    style = args.style  
    if not style and config.defaults.style:
        style = config.defaults.style
        logger.info(f"Using style from config: {style}")
    
    output_dir = args.output_dir
    if not output_dir and config.defaults.output_dir:
        output_dir = config.defaults.output_dir
        logger.info(f"Using output directory from config: {output_dir}")
    
    # Validate that all required arguments are provided (either via CLI or config)
    if not project_name:
        raise ValueError("Project name is required. Provide via --projectname or set defaults.project_name in config.")
    if not language:
        raise ValueError("Language is required. Provide via --language or set defaults.language in config.")
    if not style:
        raise ValueError("Style is required. Provide via --style or set defaults.style in config.")
    if not output_dir:
        raise ValueError("Output directory is required. Provide via --output or set defaults.output_dir in config.")
    
    suppress_schema_output = args.no_schema
    suppress_code_output = args.no_code
    messagegroup_filter = args.messagegroup
    endpoint_filter = args.endpoint

    headers = {header.split("=", 1)[0]: header.split("=", 1)[1] for header in args.headers} if args.headers else {}

    template_args = {}
    if args.template_args:
        for arg in args.template_args:
            key, value = arg.split("=", 1)
            template_args[key] = value

    generator_context = GeneratorContext(output_dir, messagegroup_filter, endpoint_filter, getattr(args, 'model', None))

    SchemaUtils.schema_files_collected = set()
    generator_context.loader.reset_schemas_handled()
    SchemaUtils.schema_references_collected = set()
    generator_context.loader.set_current_url(None)

    try:
        # Validate definitions files if they are not URLs
        definitions_files = args.definitions_files if isinstance(args.definitions_files, list) else [args.definitions_files]
        non_url_files = [f for f in definitions_files if not f.startswith("http")]
        if non_url_files:
            if validate(non_url_files, headers, False) != 0:
                return 1
        
        # Use stacked loading if multiple files, otherwise use single file
        if len(definitions_files) > 1:
            # Store the list in the generator context for stacked loading
            primary_definitions_file = "|".join(definitions_files)  # Marker for stacked loading
        else:
            primary_definitions_file = definitions_files[0]
        
        renderer = TemplateRenderer(generator_context,
            project_name, language, style, output_dir,
            primary_definitions_file, headers, args.template_dirs, template_args,
            suppress_code_output, suppress_schema_output
        )
        renderer.generate()

        for schema in SchemaUtils.schema_files_collected:
            renderer = TemplateRenderer(generator_context,
                project_name, language, style, output_dir,
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
