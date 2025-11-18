# pylint: disable=too-many-arguments, line-too-long, too-many-locals, too-many-branches, too-many-statements, too-many-nested-blocks, too-many-instance-attributes

"""Renderer for templates."""

from ast import main
import glob
import json
import os
import re
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union
import toml

import avrotize
import jinja2
import jsonpointer
from jinja2 import Template, TemplateAssertionError, TemplateNotFound, TemplateRuntimeError, TemplateSyntaxError
import urllib
import urllib.parse

from xregistry.cli import logger
from xregistry.generator.generator_context import GeneratorContext
from xregistry.generator.jinja_extensions import JinjaExtensions, TemplateError
from xregistry.generator.jinja_filters import JinjaFilters
from xregistry.generator.schema_utils import SchemaUtils
from xregistry.generator.url_utils import URLUtils

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]

string_resolver_filters = {
    'lower': lambda x: x.lower(),
    'upper': lambda x: x.upper(),
    'pascal': JinjaFilters.pascal,
    'camel': JinjaFilters.camel,
    'snake': JinjaFilters.snake,
    'dotdash': lambda x: x.replace('.', '-'),
    'dashdot': lambda x: x.replace('-', '.'),
    'dotunderscore': lambda x: x.replace('.', '_'),
    'underscoredot': lambda x: x.replace('_', '.'),
}

class TemplateRenderer:
    """Renderer for templates."""

    def __init__(self, ctx: GeneratorContext, project_name: str, language: str, style: str, output_dir: str,
                 xreg_file_arg: str, headers: Dict[str, str], template_dirs: List[str], template_args: Dict[str, Any],
                 suppress_code_output: bool, suppress_schema_output: bool) -> None:
        self.ctx = ctx
        self.project_name = project_name
        self.language = language
        self.style = style
        self.output_dir = output_dir
        self.xreg_file_arg = xreg_file_arg
        self.headers = headers
        self.template_dirs = template_dirs
        self.template_args = template_args
        self.suppress_code_output = suppress_code_output
        self.suppress_schema_output = suppress_schema_output
        self.templateinfo: Dict[str, Any] = {}
        # Keep data_project_name same for all languages for template compatibility
        # Templates use {{ data_project_name }} in paths and imports
        self.data_project_name = f"{project_name}Data"
        self.data_project_dir = self.data_project_name
        self.main_project_name = project_name
        self.src_layout = False

        # Add resource handling for the refactoring
        self.handled_resources: set[str] = set()

        self.ctx.uses_avro = False
        self.ctx.uses_protobuf = False
        logger.debug("Initialized TemplateRenderer")

    def generate(self) -> None:
        """Generate code and schemas from templates."""

        self.ctx.base_uri = self.xreg_file_arg
        
        # Check if this is a stacked file list (marked with | separator)
        if "|" in self.xreg_file_arg and not self.xreg_file_arg.startswith("http"):
            # Multiple files to stack
            definitions_files = self.xreg_file_arg.split("|")
            # Use the first file for base_uri
            if definitions_files[0].startswith("http"):
                parsed_uri = urllib.parse.urlparse(definitions_files[0])
                path_segments = parsed_uri.path.split('/')
                groups_index = next((i for i, segment in enumerate(path_segments) if segment.endswith("groups")), None)
                if groups_index is not None:
                    self.ctx.base_uri = urllib.parse.urlunparse(parsed_uri._replace(path='/'.join(path_segments[:groups_index])))
                else:
                    self.ctx.base_uri = definitions_files[0]
            else:
                self.ctx.base_uri = definitions_files[0]
            
            xreg_file, xregistry_document = self.ctx.loader.load_stacked(
                definitions_files, self.headers, self.style == "schema",
                messagegroup_filter=self.ctx.messagegroup_filter,
                endpoint_filter=self.ctx.endpoint_filter)
        else:
            # Single file
            if self.xreg_file_arg.startswith("http"):
                parsed_uri = urllib.parse.urlparse(self.xreg_file_arg)
                path_segments = parsed_uri.path.split('/')
                groups_index = next((i for i, segment in enumerate(path_segments) if segment.endswith("groups")), None)
                if groups_index is not None:
                    self.ctx.base_uri = urllib.parse.urlunparse(parsed_uri._replace(path='/'.join(path_segments[:groups_index])))
                else:
                    self.ctx.base_uri = self.xreg_file_arg

            # Use load_with_dependencies for HTTP URLs to automatically fetch related resources
            if self.xreg_file_arg.startswith("http"):
                xreg_file, xregistry_document = self.ctx.loader.load_with_dependencies(
                    self.xreg_file_arg, self.headers, 
                    messagegroup_filter=self.ctx.messagegroup_filter, 
                    endpoint_filter=self.ctx.endpoint_filter)
            else:
                xreg_file, xregistry_document = self.ctx.loader.load(
                    self.xreg_file_arg, self.headers, self.style == "schema", 
                    messagegroup_filter=self.ctx.messagegroup_filter, 
                    endpoint_filter=self.ctx.endpoint_filter)
        
        if not xreg_file or not xregistry_document:
            raise RuntimeError(
                f"Definitions file not found or invalid {self.xreg_file_arg}")

        pt = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
        code_template_dir = os.path.join(
            pt, "templates", self.language, self.style)
        if not os.path.exists(code_template_dir):
            raise RuntimeError(
                f"Code template directory not found: {code_template_dir}")

        if os.path.exists(os.path.join(code_template_dir, "_templateinfo.json")):
            with open(os.path.join(code_template_dir, "_templateinfo.json"), "r", encoding='utf-8') as f:
                self.templateinfo = json.load(f)
                if "src_layout" in self.templateinfo:
                    self.src_layout = self.templateinfo["src_layout"]
                if "main_project_name" in self.templateinfo:
                    self.main_project_name = self.resolve_string(self.templateinfo["main_project_name"], {"project_name": self.project_name})
                if "data_project_name" in self.templateinfo:
                    self.data_project_name =  self.resolve_string(self.templateinfo["data_project_name"], {"project_name": self.project_name})
                    self.data_project_dir = self.data_project_name
                if "data_project_dir" in self.templateinfo:
                    self.data_project_dir = self.resolve_string(self.templateinfo["data_project_dir"], {"project_name": self.project_name})

        solution_dir = os.path.join(self.output_dir)
        if self.src_layout:
            solution_dir = os.path.join(self.output_dir, "src")
        project_data_dir = os.path.join(solution_dir, self.data_project_dir)
        project_dir = os.path.join(solution_dir, self.main_project_name)

        self.template_args["project_data_dir"] = project_data_dir
        self.template_args["project_dir"] = project_dir

        self.ctx.set_current_dir(project_dir)

        code_template_dirs = [code_template_dir]
        code_template_and_include_dirs = [code_template_dir, os.path.join(
            pt, "templates", self.language, "_common")]
        schema_template_dirs = [os.path.join(
            pt, "templates", self.language, "_schemas")]

        for template_dir in self.template_dirs if self.template_dirs else []:
            template_dir = os.path.join(os.path.curdir, template_dir)
            if not os.path.isdir(template_dir):
                raise RuntimeError(
                    f"Template directory not found {template_dir}")
            code_template_dir = os.path.join(
                template_dir, self.language, self.style)
            if os.path.exists(code_template_dir) and os.path.isdir(code_template_dir):
                code_template_dirs = [code_template_dir]
                code_template_and_include_dirs = [code_template_dir, os.path.join(
                    pt, "templates", self.language, "_common")]
                schema_template_dirs = [os.path.join(
                    pt, "templates", self.language, "_schemas")]
                break

        code_env = self.setup_jinja_env(code_template_and_include_dirs)
        schema_env = self.setup_jinja_env(schema_template_dirs)

        #  render from code template directories
        self.render_code_templates(self.project_name, self.main_project_name, self.data_project_name, self.style, project_dir, xregistry_document,
                                   code_template_dirs, code_env, False, self.template_args, self.suppress_code_output)
        # render from schema template directories
        self.render_code_templates(self.project_name, self.main_project_name, self.data_project_name, self.style, project_data_dir, xregistry_document,
                                   schema_template_dirs, schema_env, False, self.template_args, self.suppress_schema_output)
        
        # Add filter to jinja environments for marking resources as handled
        code_env.filters['mark_handled'] = self.mark_resource_handled
        schema_env.filters['mark_handled'] = self.mark_resource_handled
        
        # Process unhandled schemas using the composed document
        avrotize_queue = []
        unhandled_schemas = self.get_unhandled_schema_references(xregistry_document)
        
        for schema_reference in unhandled_schemas:
            schema_data = self.resolve_schema_reference_in_document(schema_reference, xregistry_document)
            if not schema_data:
                logger.warning("Could not resolve schema reference: %s", schema_reference)
                continue
                
            schema_info = self.extract_schema_info_from_resolved_data(schema_reference, schema_data)
            if not schema_info:
                logger.warning("Could not extract schema info for: %s", schema_reference)
                continue
            
            # Check if this schema should be processed with avrotize
            if self.should_use_avrotize(schema_info):
                # Convert JSON Schema to Avro if needed
                if schema_info["format_short"] == "jsonschema":
                    self.convert_json_to_avro_if_needed(schema_info)
                # Convert Proto to Avro if needed
                elif schema_info["format_short"] == "proto":
                    self.convert_proto_to_avro_if_needed(schema_info)
                
                avrotize_queue.append(schema_info)
            else:
                # Render schema directly with templates
                self.render_schema_templates(
                    schema_info["format_short"], self.data_project_name, schema_info["class_name"],
                    self.language, project_data_dir, "schema_file", schema_info["content"], 
                    schema_template_dirs, schema_env, self.template_args, self.suppress_schema_output
                )        
        # Process avrotize queue using the refactored approach
        if len(avrotize_queue) > 0:
            avro_enabled = self.template_args.get("avro-encoding", "false") == "true" or any("avro" in a["format_short"] for a in avrotize_queue)
            json_enabled = self.template_args.get("json-encoding", "true") == "true"
            merged_schema = []
            for schema_info in avrotize_queue:
                content = schema_info["content"]
                if isinstance(content, list):
                    merged_schema.extend(content)
                else:
                    merged_schema.append(content)
            
            if len(merged_schema) == 1:
                merged_schema = merged_schema[0]

            if self.language == "py":
                avrotize.convert_avro_schema_to_python(
                    merged_schema, project_data_dir, package_name=self.data_project_name,
                    dataclasses_json_annotation=json_enabled, avro_annotation=avro_enabled
                )
            elif self.language == "cs":
                avrotize.convert_avro_schema_to_csharp(
                    merged_schema, project_data_dir, base_namespace=JinjaFilters.pascal(self.data_project_name),
                    pascal_properties=True, system_text_json_annotation=json_enabled, avro_annotation=avro_enabled
                )
            elif self.language == "java":
                # Java: use lowercase package name to match Maven artifact conventions
                java_package_name = self.data_project_name.lower().replace('-', '_')
                avrotize.convert_avro_schema_to_java(
                    merged_schema, project_data_dir, package_name=java_package_name,
                    jackson_annotation=json_enabled, avro_annotation=avro_enabled
                )
            elif self.language == "js":
                avrotize.convert_avro_schema_to_javascript(
                    merged_schema, project_data_dir, package_name=self.data_project_name, avro_annotation=avro_enabled
                )
            elif self.language == "ts":
                avrotize.convert_avro_schema_to_typescript(
                    merged_schema, project_data_dir, package_name=self.data_project_name,
                    avro_annotation=avro_enabled, typedjson_annotation=json_enabled
                )
            elif self.language == "go":
                avrotize.convert_avro_schema_to_go(
                    merged_schema, project_data_dir, package_name=self.data_project_name,
                    avro_annotation=avro_enabled, json_annotation=json_enabled
                )
        self.render_code_templates(
            self.project_name, self.main_project_name, self.data_project_name, self.style, project_dir, xregistry_document,
            code_template_dirs, code_env, True, self.template_args, self.suppress_code_output
        )

        # REFACTORED: Schema references are now handled directly by the composed document
        # SchemaUtils.schema_references_collected = set()  # No longer needed

        if self.style == "schema":
            self.render_schema_templates(
                None, self.main_project_name, None, self.language,
                project_dir, xreg_file, xregistry_document, schema_template_dirs, schema_env,
                self.template_args, self.suppress_schema_output
            )

    def convert_proto_to_avro(self, schema_reference: str, schema_root: str) -> JsonNode:
        """Convert a proto schema to an Avro schema."""
        logger.debug("Converting proto schema to Avro schema")
        if schema_reference.startswith("#"):
            proto_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".proto")
            try:
                avro_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".avsc")
                try:
                    proto_file.write(schema_root.encode('utf-8'))
                    proto_file.close()
                    avrotize.convert_proto_to_avro(
                        proto_file.name, avro_file.name)
                    schema_root = json.loads(avro_file.read())
                finally:
                    avro_file.close()
                    os.unlink(avro_file.name)
            finally:
                os.unlink(proto_file.name)
        else:
            avro_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".avsc")
            try:
                avrotize.convert_proto_to_avro(
                    schema_reference, avro_file.name)
                schema_root = json.loads(avro_file.read())
            finally:
                avro_file.close()
                os.unlink(avro_file.name)
        return schema_root

    def convert_jsons_to_avro(self, schema_reference: str, schema_root: JsonNode, namespace_name: str = '', class_name: str = '') -> JsonNode:
        """Convert a JSON schema to an Avro schema."""
        logger.debug("Converting JSON schema to Avro schema")
        if schema_reference.startswith("#"):
            jsons_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".jsons")
            try:
                avro_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".avsc")
                try:
                    jsons_file.write(json.dumps(schema_root).encode('utf-8'))
                    jsons_file.close()
                    avrotize.convert_jsons_to_avro(
                        jsons_file.name, avro_file.name, namespace=namespace_name, root_class_name=class_name
                    )
                    schema_root = json.loads(avro_file.read())
                finally:
                    avro_file.close()
                    os.unlink(avro_file.name)
            finally:
                os.unlink(jsons_file.name)
        else:
            avro_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".avsc")
            try:
                avrotize.convert_jsons_to_avro(
                    schema_reference, avro_file.name, namespace=namespace_name
                )
                schema_root = json.loads(avro_file.read())
            finally:
                avro_file.close()
                os.unlink(avro_file.name)
        return schema_root

    def render_code_templates(
            self, code_project_name: str, main_project_name: str, data_project_name: str,
            style: str, output_dir: str, xregistry_document: JsonNode,
            code_template_dirs: List[str], env: jinja2.Environment, post_process: bool,
            template_args: Dict[str, Any], suppress_output: bool = False) -> None:
        """Render code templates."""
        logger.debug(
            "Rendering code templates for project: %s, style: %s", code_project_name, style)
        if not isinstance(xregistry_document, dict):
            raise RuntimeError("Document root is not a dictionary")
        class_name = None
        for template_dir in code_template_dirs:
            for root, _, files in os.walk(template_dir):
                relpath = os.path.relpath(
                    root, template_dir).replace("\\", "/")
                if relpath == ".":
                    relpath = ""

                for file in files:
                    if not file.endswith(".jinja") or (not post_process and file.startswith("_")) or (post_process and not file.startswith("_")):
                        continue

                    template_path = relpath + "/" + file
                    scope = xregistry_document
                    class_name = ''

                    file_dir = file_dir_base = os.path.join(
                        output_dir, os.path.join(*relpath.split("/")))
                    file_name_base = file[:-6]
                    if post_process:
                        file_name_base = file_name_base[1:]

                    try:
                        template = env.get_template(template_path)
                    except TemplateAssertionError as err:
                        logger.error("%s (%s): %s", err.name, err.lineno, err)
                        exit(1)
                    except TemplateSyntaxError as err:
                        logger.error("%s: (%s): %s", err.name, err.lineno, err)
                        exit(1)

                    file_name_base = self.resolve_string(file_name_base, {
                                                            "projectname": code_project_name,
                                                            "mainprojectname": main_project_name,
                                                            "dataprojectname": data_project_name,
                                                        })
                    file_name = file_name_base
                    if file_name.startswith("{class"):
                        if isinstance(scope, dict) and "messagegroups" in scope:
                            if "endpoints" in xregistry_document:
                                endpoints = xregistry_document["endpoints"]
                            else:
                                endpoints = None
                            if "schemagroups" in xregistry_document:
                                schemagroups = xregistry_document["schemagroups"]
                            else:
                                schemagroups = None

                            group_dict = scope["messagegroups"]
                            if not isinstance(group_dict, dict):
                                raise RuntimeError(
                                    "Messagegroups is not a dictionary")
                            for id_, definitiongroup in group_dict.items():
                                subscope: JsonNode = {
                                    "endpoints": endpoints,
                                    "schemagroups": schemagroups,
                                    "messagegroups": {
                                        f"{id_}": definitiongroup
                                    }
                                }
                                class_name = id_
                                scope_parts = id_.split(".")
                                package_class_name = scope_parts[-1]
                                package_name = id_
                                if not package_name:
                                    package_name = code_project_name
                                elif not package_name.startswith(code_project_name):
                                    package_name = code_project_name + "." + package_name
                                if not package_class_name:
                                    raise RuntimeError("Class name not found")
                                if file_name_base.find("{classdir}") > -1:
                                    file_dir = os.path.join(file_dir_base, os.path.join(*package_name.split(".")).lower())
                                    file_name = self.resolve_string(file_name_base, {"classdir": JinjaFilters.pascal(package_class_name) })
                                    class_name = f'{package_name}.{file_name.split(".")[0]}'
                                else:
                                    file_name = self.resolve_string(file_name_base, {
                                        "classfull": id_, 
                                        "classname": package_class_name,
                                        "classpackage": package_name})
                                    if '.' in file_name:
                                        file_dir = os.path.join(file_dir_base, os.path.join(*file_name.split(".")[:-1]))
                                        file_name = file_name.split(".")[-1]
                                        class_name = f'{package_name}.{file_name}'
                                if not class_name:
                                    raise RuntimeError("Class name not found")
                                self.render_template(
                                    code_project_name, main_project_name, data_project_name,
                                    class_name, subscope, file_dir, file_name, template, template_args, suppress_output)
                        continue

                    has_rootdir = file_name_base.startswith("{rootdir")
                    code_project_dir = code_project_name.replace(".", "/")+("/" if code_project_name else "")
                    file_name = self.resolve_string(file_name_base, {
                        "mainprojectdir": main_project_name.replace(".", "/")+("/" if main_project_name else ""),
                        "dataprojectdir": data_project_name.replace(".", "/")+("/" if data_project_name else ""),
                        "testdir": "tests/" if not self.src_layout else "../tests/",
                        "projectdir": code_project_dir,
                        "projectsrc": f'src/{code_project_dir}',
                        "rootdir": '',
                    })
                    if '/' in file_name:
                        scope_parts = file_name.split("/")
                        file_dir = os.path.join(file_dir_base if not has_rootdir else self.output_dir, os.path.join(*scope_parts[:-1]))
                        file_name = scope_parts[-1]
                    else:
                        file_dir = file_dir_base if not has_rootdir else self.output_dir

                    self.render_template(code_project_name, main_project_name, data_project_name,
                                         class_name, scope, file_dir,
                                         file_name, template, template_args, suppress_output)

    def render_schema_templates(
            self, schema_type: Optional[str], schema_project_name: str, class_name: Optional[str], language: str,
            output_dir: str, xreg_file: str, xregistry_document: JsonNode, schema_template_dirs: List[str],
            env: jinja2.Environment, template_args: Dict[str, Any], suppress_output: bool = False) -> None:
        """Render schema templates."""

        scope = xregistry_document
        if schema_type is None:
            if self.is_proto_doc(xregistry_document):
                schema_type = "proto"
            elif isinstance(xregistry_document, dict) and "type" in xregistry_document and xregistry_document["type"] == "record":
                schema_type = "avro"
            else:
                schema_type = "json"

        if schema_type == "proto":
            self.ctx.uses_protobuf = True
            if isinstance(xregistry_document, str) and self.is_proto_doc(xregistry_document) and class_name:
                local_class_name = JinjaFilters.strip_namespace(class_name)
                match = re.search(r"message[\s]+([\w]+)[\s]*{", xregistry_document)
                found = False
                if local_class_name and match:
                    for g in match.groups():
                        if g.lower() == local_class_name.lower():
                            class_name = JinjaFilters.namespace_dot(
                                class_name) + g
                            found = True
                            break
                if not found and match and match.groups() and len(match.groups()) == 1:
                    class_name = JinjaFilters.namespace_dot(
                        str(class_name)) + match.groups()[0]
                elif not found:
                    raise RuntimeError(
                        f"Proto: Top-level message {class_name} not found in Proto schema")
        elif schema_type == "avro":
            self.ctx.uses_avro = True
            if isinstance(xregistry_document, dict) and "type" in xregistry_document and xregistry_document["type"] == "record":
                class_name = self.concat_namespace(
                    str(xregistry_document.get("namespace", "")), str(xregistry_document["name"]))
            elif isinstance(xregistry_document, list):
                if class_name:
                    cns = class_name.split(".", 1)
                    if len(cns) == 2:
                        ns = cns[0]
                        cn = cns[1]
                    else:
                        ns = ""
                        cn = cns[0]
                for record in xregistry_document:
                    if isinstance(record, dict) and "type" in record and record["type"] == "record" \
                            and "namespace" in record and "name" in record \
                            and str(record["name"]).lower() == cn and str(record["namespace"]).lower() == ns:
                        class_name = self.concat_namespace(
                            str(record.get("namespace", "")), str(record["name"]))
                        break
                raise RuntimeError(
                    "Avro: Top-level record object not found in Avro schema: ")

        file_dir = file_dir_base = output_dir
        if class_name is None:
            class_name = os.path.basename(xreg_file).split(".")[0]
        for template_dir in schema_template_dirs:
            schema_files = glob.glob(
                f"**/_{schema_type}.*.jinja", root_dir=template_dir, recursive=True)
            for schema_file in schema_files:
                schema_file = schema_file.replace("\\", "/")
                try:
                    template = env.get_template(schema_file)
                except Exception as err:  # pylint: disable=broad-except
                    logger.error("%s", err)
                    exit(1)

                relpath = os.path.dirname(schema_file)
                if relpath == ".":
                    relpath = ""
                schema_file = os.path.basename(schema_file)
                file_name_base = schema_file[len(schema_type) + 2:][:-6]
                file_dir = os.path.join(
                    file_dir_base, os.path.join(*relpath.split("/")))

                if file_name_base == language or file_name_base == "proto" or file_name_base == "avsc":
                    file_name_base = class_name + "." + file_name_base
                file_name_base = file_name_base.replace("{projectname}", schema_project_name)
                file_name_base = file_name_base.replace("{classname}", class_name)

                file_name = file_name_base
                if file_name_base.find("{classdir}") > -1:
                    scope_parts = class_name.split(".")
                    class_package_name = scope_parts[-1]
                    package_name = '.'.join(scope_parts[:-1])
                    if not package_name.startswith(schema_project_name):
                        package_name = schema_project_name + "." + package_name

                    file_dir = os.path.join(file_dir, os.path.join(
                        *package_name.split(".")).lower())
                    file_name = file_name_base.replace(
                        "{classdir}", JinjaFilters.pascal(class_package_name))
                if file_name_base.startswith("{rootdir}"):
                    file_dir = self.output_dir
                    file_name = file_name_base.replace("{rootdir}", "")

                if not class_name in self.ctx.stacks.stack("classfiles"):
                    self.ctx.stacks.push(class_name, "classfiles")

                self.render_template(
                    schema_project_name, '', '', class_name, scope, file_dir,
                    file_name, template, template_args, suppress_output)

    def render_template(
            self, template_project_name: str, main_project_name: str, data_project_name: str,
            class_name: str, scope: JsonNode, file_dir: str, file_name: str,
            template: Template, template_args: Dict[str, Any], suppress_output: bool = False) -> None:
        """Render a template."""

        try:
            output_path = os.path.join(os.getcwd(), file_dir, file_name)

            if not suppress_output and not os.path.exists(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))
            try:
                self.ctx.current_dir = os.path.dirname(output_path)
                args = template_args.copy() if template_args is not None else {}
                args["uuid"] = uuid.uuid4
                args["root"] = scope
                args["project_name"] = template_project_name
                args["main_project_name"] = main_project_name
                args["data_project_name"] = data_project_name
                args["class_name"] = class_name
                args["self.ctx.uses_avro"] = self.ctx.uses_avro
                args["self.ctx.uses_protobuf"] = self.ctx.uses_protobuf
                try:
                    rendered = template.render(args)
                except Exception as render_err:
                    # Print detailed information about the rendering error
                    import traceback
                    print(f"\n=== Template Rendering Error in {template.name} ===", file=sys.stderr)
                    print(f"Error: {render_err}", file=sys.stderr)
                    print(f"Error type: {type(render_err)}", file=sys.stderr)
                    print("\nTemplate arguments:", file=sys.stderr)
                    for key in sorted(args.keys()):
                        if key != "root":
                            print(f"  {key}: {args[key]}", file=sys.stderr)
                    print("\nFull traceback:", file=sys.stderr)
                    traceback.print_exc()
                    raise
                if not suppress_output:
                    with open(output_path, "w", encoding='utf-8') as f:
                        f.write(rendered)
            except TypeError as err:
                if "Undefined found" in str(err):
                    if not suppress_output and os.path.exists(output_path):
                        os.remove(output_path)
                else:
                    logger.error("%s: %s", template.name, err)
                    exit(1)
        except TemplateNotFound as err:
            logger.error("%s: Include file not found: %s", template.name, err)
            exit(1)
        except TemplateError as err:
            logger.error("%s: Template error: %s", template.name, err)
            exit(1)
        except TemplateRuntimeError as err:
            import traceback
            logger.error("%s: %s", template.name, err)
            logger.error("Full traceback:\n%s", traceback.format_exc())
            exit(1)

    @staticmethod
    def resolve_string(template: str, replacements: Dict[str, str]):
        """Resolve a string template with placeholders using the given replacements."""
        # Regex to find placeholders with optional filter using | or !
        pattern = re.compile(r'\{(\w+)((?:~[\w\.]+)*)(?:\s*([|!]\s*\w+\s*)*)\}')

        # Function to replace match with the correct value
        def replace_match(match):
            var_name = match.group(1)
            suffix_chain = match.group(2)
            filter_chain = match.group(3)

            # Initialize the value with the main variable's replacement
            if var_name in replacements:
                value = replacements[var_name]
                # Process suffixes
                if suffix_chain:
                    suffixes = suffix_chain.split('~')[1:]  # Split by '~' and skip the first empty split
                    for suffix in suffixes:
                        value += ('/' if value and not value[-1]=='/' else '') + suffix
                    value += '/'
                # Apply filters
                if filter_chain:
                    filters_to_apply = re.findall(r'[|!]\s*(\w+)', filter_chain)
                    for filter_name in filters_to_apply:
                        if filter_name in string_resolver_filters:
                            value = string_resolver_filters[filter_name](value)
                        else:
                            return match.group(0)  # return the whole match if there's an issue with the filter                
                return value
            else:
                return match.group(0)  # return the whole match if there's an issue with the variable
        
        return pattern.sub(replace_match, template)

    @staticmethod
    def dependency(language: str, runtime_version: str, dependency_name: str):
        """Get the dependency string for a given language, runtime version, and dependency name."""
        # Define the path to the master project file based on the language and runtime version
        if language == 'cs':
            master_project_path = os.path.join(os.path.dirname(
                __file__), f'../dependencies/cs/{runtime_version}/dependencies.csproj')
        elif language == 'py':
            master_project_path = os.path.join(os.path.dirname(
                __file__), f'../dependencies/python/{runtime_version}/pyproject.toml')
        elif language == 'ts':
            master_project_path = os.path.join(os.path.dirname(
                __file__), f'../dependencies/typescript/{runtime_version}/package.json')
        elif language == 'java':
            master_project_path = os.path.join(os.path.dirname(
                __file__), f'../dependencies/java/{runtime_version}/pom.xml')
        else:
            raise ValueError(f"Unsupported language: {language}")

        if language == 'cs':
            triedadd = False
            while True:
                # Find the desired dependency
                tree = ET.parse(master_project_path)
                root = tree.getroot()
                for package in root.findall(".//PackageReference"):
                    if package.get('Include') == dependency_name:
                        # Convert the XML element back to string including its children
                        dependency_str = ET.tostring(
                            package, encoding='unicode')
                        return dependency_str
                if not triedadd:
                    os.system(
                        f"dotnet add {master_project_path} package {dependency_name}")
                    triedadd = True
                else:
                    raise ValueError(
                        f"Dependency '{dependency_name}' not found in runtime version '{runtime_version}' for language '{language}'.")

        elif language == 'py':
            # Parse the pyproject.toml file
            with open(master_project_path, 'r', encoding='utf-8') as file:
                pyproject_data = toml.load(file)

            # Find the desired dependency
            dependencies = pyproject_data.get('tool', {}).get(
                'poetry', {}).get('dependencies', {})
            if dependency_name in dependencies:
                version = dependencies[dependency_name]
                dependency_str = f"{dependency_name} = \"{version}\""
                return dependency_str

            # If the dependency is not found, raise an error
            raise ValueError(
                f"Dependency '{dependency_name}' not found in runtime version '{runtime_version}' for language '{language}'.")

        elif language == 'ts':
            # Parse the package.json file
            with open(master_project_path, 'r') as file:
                package_data = json.load(file)

            # Find the desired dependency
            dependencies = package_data.get('dependencies', {})
            if dependency_name in dependencies:
                version = dependencies[dependency_name]
                dependency_str = f"\"{dependency_name}\": \"{version}\""
                return dependency_str

            # If the dependency is not found, raise an error
            raise ValueError(
                f"Dependency '{dependency_name}' not found in runtime version '{runtime_version}' for language '{language}'.")

        elif language == 'java':
            # Parse the pom.xml file
            tree = ET.parse(master_project_path)
            root = tree.getroot()

            # Find the desired dependency
            for dependency in root.findall(".//dependency"):
                artifact_id = dependency.find('artifactId')
                if artifact_id is not None and artifact_id.text == dependency_name:
                    # Convert the XML element back to string including its children
                    dependency_str = ET.tostring(
                        dependency, encoding='unicode')
                    return dependency_str

            # If the dependency is not found, raise an error
            raise ValueError(
                f"Dependency '{dependency_name}' not found in runtime version '{runtime_version}' for language '{language}'.")

    def setup_jinja_env(self, template_dirs: List[str]) -> jinja2.Environment:
        """Create the Jinja environment and load extensions."""
        logger.debug(
            "Setting up Jinja environment with template dirs: %s", template_dirs)
        loader = jinja2.FileSystemLoader(template_dirs, followlinks=True)
        env = jinja2.Environment(loader=loader, extensions=[
                                 JinjaExtensions.ExitExtension, JinjaExtensions.TimeExtension, JinjaExtensions.ErrorExtension])
        env.filters['regex_search'] = JinjaFilters.regex_search
        env.filters['regex_replace'] = JinjaFilters.regex_replace
        env.filters['pascal'] = JinjaFilters.pascal
        env.filters['snake'] = JinjaFilters.snake
        env.filters['camel'] = JinjaFilters.camel
        env.filters['dotdash'] = JinjaFilters.dotdash
        env.filters['dashdot'] = JinjaFilters.dashdot
        env.filters['dotunderscore'] = JinjaFilters.dotunderscore
        env.filters['underscoredot'] = JinjaFilters.underscoredot
        env.filters['strip_namespace'] = JinjaFilters.strip_namespace
        env.filters['namespace'] = JinjaFilters.namespace
        env.filters['namespace_dot'] = JinjaFilters.namespace_dot
        env.filters['concat_namespace'] = JinjaFilters.concat_namespace
        env.filters['strip_dots'] = JinjaFilters.strip_dots
        env.filters['lstrip'] = JinjaFilters.lstrip
        env.filters['schema_type'] = lambda schema_ref, project_name, root, schema_format: SchemaUtils.schema_type(
            self.ctx, schema_ref, project_name, root, schema_format)
        env.filters['strip_invalid_identifier_characters'] = JinjaFilters.strip_invalid_identifier_characters
        env.filters['pad'] = JinjaFilters.pad
        env.filters['toyaml'] = JinjaFilters.to_yaml
        env.filters['proto'] = JinjaFilters.proto
        env.filters['go_type'] = JinjaFilters.go_type
        env.filters['exists'] = JinjaFilters.exists
        env.filters['existswithout'] = JinjaFilters.exists_without
        env.filters['push'] = self.ctx.stacks.push
        env.filters['pushfile'] = self.ctx.stacks.push_file
        env.filters['save'] = self.ctx.stacks.save
        env.globals['pop'] = self.ctx.stacks.pop
        env.globals['schema_object'] = SchemaUtils.schema_object
        env.globals['latest_dict_entry'] = SchemaUtils.latest_dict_entry
        env.globals['geturlhost'] = URLUtils.get_url_host
        env.globals['geturlpath'] = URLUtils.get_url_path
        env.globals['geturlport'] = URLUtils.get_url_port
        env.globals['geturlscheme'] = URLUtils.get_url_scheme
        env.globals['dependency'] = self.dependency
        return env

    def is_proto_doc(self, xregistry_document: JsonNode) -> bool:
        """Check if the document is a proto document."""
        return isinstance(xregistry_document, str) and re.search(r"syntax[\s]*=[\s]*\"proto3\"", xregistry_document) is not None

    def mark_resource_handled(self, resource_ref: str) -> str:
        """Mark a resource as handled by templates."""
        self.handled_resources.add(resource_ref)
        return resource_ref

    def is_resource_handled(self, resource_ref: str) -> bool:
        """Check if resource is handled."""
        return resource_ref in self.handled_resources

    def concat_namespace(self, namespace: str, class_name: str) -> str:
        """Concatenate a namespace and a class name."""
        if namespace:
            return f"{namespace}.{class_name}"
        return class_name

    def collect_schema_references_from_document(self, document: JsonNode) -> set[str]:
        """Collect all schema references from the composed document."""
        schema_refs = set()
        
        def scan_for_schemas(obj: JsonNode, path: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}/{key}" if path else key
                    
                    # Look for schema reference properties
                    if key in ["dataschema", "schema", "schemaurl"] and isinstance(value, str):
                        schema_refs.add(value)
                    
                    # Look for inline schemas
                    elif key == "schema" and isinstance(value, (dict, str)):
                        schema_pointer = f"#{path}/schema"
                        schema_refs.add(schema_pointer)
                    
                    # Recursively scan nested objects
                    scan_for_schemas(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    scan_for_schemas(item, f"{path}[{i}]")
        
        scan_for_schemas(document)
        return schema_refs

    def get_unhandled_schema_references(self, document: JsonNode) -> set[str]:
        """Get schema references that haven't been marked as handled."""
        all_schemas = self.collect_schema_references_from_document(document)
        return all_schemas - self.handled_resources

    def resolve_schema_reference_in_document(self, schema_ref: str, document: JsonNode) -> Optional[JsonNode]:
        """Resolve a schema reference in the composed document."""
        try:
            if schema_ref.startswith("#"):
                # xRegistry fragment reference - convert to JSON pointer format
                # xRegistry uses: #schemagroups/group/schemas/name/versions/v1/schema
                # JSON Pointer needs: /schemagroups/group/schemas/name/versions/v1/schema
                pointer = schema_ref[1:]  # Remove #
                if not pointer.startswith('/'):
                    pointer = '/' + pointer  # Add leading / for JSON Pointer
                result = jsonpointer.resolve_pointer(document, pointer)
                return result  # type: ignore
            else:
                # For external references, they should already be resolved in the composed document
                # We can scan the document to find them
                return self._find_external_schema_in_document(schema_ref, document)
        except (jsonpointer.JsonPointerException, Exception) as e:
            logger.warning("Failed to resolve schema reference %s: %s", schema_ref, str(e))
            return None

    def _find_external_schema_in_document(self, schema_url: str, document: JsonNode) -> Optional[JsonNode]:
        """Find an external schema that was resolved into the composed document."""
        # This is a simplified approach - in practice, the loader should track 
        # the mapping of external URLs to their resolved locations
        logger.debug("Looking for external schema: %s", schema_url)
        return None

    def extract_schema_info_from_resolved_data(self, schema_ref: str, schema_data: JsonNode) -> Optional[Dict[str, Any]]:
        """Extract schema information from resolved schema data."""
        if not schema_data:
            return None

        # Handle string schemas (likely proto)
        if isinstance(schema_data, str):
            if self.is_proto_doc(schema_data):
                return {
                    "reference": schema_ref,
                    "content": schema_data,
                    "format": "proto3",
                    "format_short": "proto",
                    "class_name": self._extract_proto_class_name(schema_data, "")
                }
            return None

        # Handle dictionary schemas
        if isinstance(schema_data, dict):
            return self._extract_schema_info_from_dict(schema_ref, schema_data)

        return None

    def _extract_schema_info_from_dict(self, schema_ref: str, schema_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract schema info from a dictionary."""
        # Handle raw JSON Schema documents (when ref points directly to /schema property)
        # These have '$schema', 'type', 'properties' etc but not xRegistry metadata
        if self._looks_like_raw_schema(schema_dict):
            return self._extract_from_raw_schema(schema_ref, schema_dict)
        
        # Handle schema definitions with versions
        if "versions" in schema_dict and isinstance(schema_dict["versions"], dict):
            latest_version_id = schema_dict.get("defaultversionid")
            if not latest_version_id or latest_version_id not in schema_dict["versions"]:
                latest_version_id = max(schema_dict["versions"].keys())
            
            schema_version = schema_dict["versions"][latest_version_id]
            if isinstance(schema_version, dict):
                return self._extract_from_schema_version(schema_ref, schema_version, schema_dict)

        # Handle direct schema versions
        elif "versionid" in schema_dict or "format" in schema_dict or "dataschemaformat" in schema_dict:
            return self._extract_from_schema_version(schema_ref, schema_dict, schema_dict)

        return None
    
    def _looks_like_raw_schema(self, schema_dict: Dict[str, Any]) -> bool:
        """Check if this looks like a raw schema document (JSON Schema, Avro, etc)."""
        # JSON Schema indicators
        if "type" in schema_dict and "properties" in schema_dict:
            return True
        if "$schema" in schema_dict:
            return True
        # Avro indicators
        if schema_dict.get("type") == "record" and "fields" in schema_dict:
            return True
        return False
    
    def _extract_from_raw_schema(self, schema_ref: str, schema_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract info from a raw schema document."""
        # Try to infer format from content
        if "$schema" in schema_dict or ("type" in schema_dict and "properties" in schema_dict):
            format_type = "jsonschema/draft-07"
        elif schema_dict.get("type") == "record" and "fields" in schema_dict:
            format_type = "avro/1.11.0"
        else:
            format_type = "jsonschema/draft-07"  # Default assumption
        
        # Extract class name from the schema reference path
        # e.g., #schemagroups/Group/schemas/SchemaName/versions/1/schema -> SchemaName
        class_name = self._extract_class_name_from_ref(schema_ref)
        namespace = self._extract_namespace_from_ref(schema_ref)
        
        return {
            "reference": schema_ref,
            "content": schema_dict,
            "format": format_type,
            "format_short": format_type.split("/")[0],
            "class_name": class_name,
            "namespace": namespace
        }
    
    def _extract_class_name_from_ref(self, schema_ref: str) -> str:
        """Extract schema/class name from reference path."""
        # Parse path like: #schemagroups/Group/schemas/SchemaName/versions/1/schema
        # or: #/schemagroups/Group/schemas/SchemaName/versions/1/schema
        parts = schema_ref.strip('#/').split('/')
        try:
            # Look for the schema name (after 'schemas' and before 'versions')
            if 'schemas' in parts:
                schemas_idx = parts.index('schemas')
                if schemas_idx + 1 < len(parts):
                    return parts[schemas_idx + 1]
        except (ValueError, IndexError):
            pass
        return "Schema"  # Fallback
    
    def _extract_namespace_from_ref(self, schema_ref: str) -> str:
        """Extract schema group name from reference path to use as namespace."""
        # Parse path like: #schemagroups/Contoso.ERP.Events/schemas/SchemaName/versions/1/schema
        # Extract: Contoso.ERP.Events
        parts = schema_ref.strip('#/').split('/')
        try:
            if 'schemagroups' in parts:
                sg_idx = parts.index('schemagroups')
                if sg_idx + 1 < len(parts):
                    return parts[sg_idx + 1]
        except (ValueError, IndexError):
            pass
        return ""  # Fallback to empty namespace

    def _extract_from_schema_version(self, schema_ref: str, schema_version: Dict[str, Any], 
                                   parent_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract info from a schema version."""
        # Get format
        schema_format = schema_version.get("dataschemaformat") or schema_version.get("format", "")
        if not schema_format:
            return None

        # Get content
        if "schema" in schema_version:
            content = schema_version["schema"]
        elif "schemaurl" in schema_version:
            # External schema - should be resolved in document already
            logger.warning("External schema URL in version, skipping: %s", schema_version["schemaurl"])
            return None
        else:
            return None

        # Extract names
        schema_id = schema_version.get("schemaid") or parent_schema.get("schemaid", "")
        class_name = schema_id

        # Extract group from reference path
        schema_group_id = ""
        if schema_ref.startswith("#"):
            path_parts = schema_ref.split("/")
            for i, part in enumerate(path_parts):
                if part == "schemagroups" and i + 1 < len(path_parts):
                    schema_group_id = path_parts[i + 1]
                    break

        # Build qualified class name
        if schema_group_id and class_name and not class_name.startswith(schema_group_id):
            class_name = f"{schema_group_id}.{class_name}"

        format_short = self._get_format_short(schema_format)

        return {
            "reference": schema_ref,
            "content": content,
            "format": schema_format,
            "format_short": format_short,
            "class_name": class_name,
            "schema_id": schema_id,
            "schema_group_id": schema_group_id
        }

    def _get_format_short(self, schema_format: str) -> str:
        """Get short format identifier."""
        format_lower = schema_format.lower()
        if format_lower.startswith("proto"):
            return "proto"
        elif format_lower.startswith("jsonschema"):
            return "json"
        elif format_lower.startswith("avro"):
            return "avro"
        return "unknown"

    def _extract_proto_class_name(self, proto_content: str, class_hint: str) -> str:
        """Extract class name from proto content."""
        match = re.search(r"message[\s]+([\w]+)[\s]*{", proto_content)
        if match:
            return match.group(1)
        return class_hint or "Message"

    def should_use_avrotize(self, schema_info: Dict[str, Any]) -> bool:
        """Check if schema should be processed with avrotize."""
        return self.language in ["py", "cs", "java", "js", "ts", "go"]

    def convert_json_to_avro_if_needed(self, schema_info: Dict[str, Any]) -> None:
        """Convert JSON schema to Avro if needed."""
        if schema_info["format_short"] == "jsonschema":
            namespace = schema_info.get("namespace", "")
            schema_info["content"] = self._convert_json_to_avro(
                schema_info["content"], schema_info["class_name"], namespace
            )
            schema_info["format_short"] = "avro"

    def convert_proto_to_avro_if_needed(self, schema_info: Dict[str, Any]) -> None:
        """Convert Protobuf schema to Avro if needed."""
        if schema_info["format_short"] == "proto":
            import avrotize.prototoavro as prototoavro
            import tempfile
            import os
            
            # prototoavro works with files, so we need temp files
            proto_content = schema_info["content"]
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.proto', delete=False) as proto_file:
                proto_file.write(proto_content)
                temp_proto_path = proto_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as avro_file:
                temp_avro_path = avro_file.name
            
            try:
                # Convert proto to avro (automatically detects proto2 vs proto3)
                prototoavro.convert_proto_to_avro(temp_proto_path, temp_avro_path)
                
                # Read the converted avro schema
                with open(temp_avro_path, 'r', encoding='utf-8') as f:
                    import json
                    avro_schema = json.load(f)
                
                schema_info["content"] = avro_schema
                schema_info["format_short"] = "avro"
            finally:
                # Clean up temp files
                if os.path.exists(temp_proto_path):
                    os.unlink(temp_proto_path)
                if os.path.exists(temp_avro_path):
                    os.unlink(temp_avro_path)

    def _convert_json_to_avro(self, json_schema: JsonNode, class_name: str, namespace: str = "") -> JsonNode:
        """Basic JSON to Avro conversion."""
        if isinstance(json_schema, dict):
            # Basic conversion
            # Ensure class name is PascalCase for Java compatibility
            pascal_class_name = JinjaFilters.pascal(class_name.split('.')[-1]) if class_name else "Record"
            avro_schema = {
                "type": "record",
                "name": pascal_class_name,
                "namespace": namespace,
                "fields": []
            }
            
            if "properties" in json_schema and isinstance(json_schema["properties"], dict):
                for prop_name, prop_def in json_schema["properties"].items():
                    field = {
                        "name": prop_name,
                        "type": self._convert_json_type_to_avro(prop_def)
                    }
                    avro_schema["fields"].append(field)
            
            return avro_schema
        
        return json_schema

    def _convert_json_type_to_avro(self, json_type_def: Any) -> Any:
        """Convert JSON type to Avro type."""
        if isinstance(json_type_def, dict):
            json_type = json_type_def.get("type", "string")
            type_map = {
                "string": "string",
                "number": "double", 
                "integer": "long",
                "boolean": "boolean"
            }
            return type_map.get(json_type, "string")
        return "string"
