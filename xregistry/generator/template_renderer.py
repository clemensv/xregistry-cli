# pylint: disable=too-many-arguments, line-too-long, too-many-locals, too-many-branches, too-many-statements, too-many-nested-blocks, too-many-instance-attributes

"""Renderer for templates."""

from ast import main
import glob
import json
import os
import re
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

from xregistry.cli import logger
from xregistry.generator.generator_context import GeneratorContext
from xregistry.generator.jinja_extensions import JinjaExtensions
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
        self.data_project_name = f"{project_name}_data"
        self.data_project_dir = self.data_project_name
        self.main_project_name = project_name
        self.src_layout = False

        self.ctx.uses_avro = False
        self.ctx.uses_protobuf = False
        logger.debug("Initialized TemplateRenderer")

    def generate(self) -> None:
        """Generate code and schemas from templates."""

        self.ctx.base_uri = self.xreg_file_arg
        if self.xreg_file_arg.startswith("http"):
            parsed_uri = urllib.parse.urlparse(self.xreg_file_arg)
            path_segments = parsed_uri.path.split('/')
            groups_index = next((i for i, segment in enumerate(path_segments) if segment.endswith("groups")), None)
            if groups_index is not None:
                self.ctx.base_uri = urllib.parse.urlunparse(parsed_uri._replace(path='/'.join(path_segments[:groups_index])))
            else:
                self.ctx.base_uri = self.xreg_file_arg

        xreg_file, xregistry_document = self.ctx.loader.load(
            self.xreg_file_arg, self.headers, self.style == "schema", messagegroup_filter=self.ctx.messagegroup_filter)
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
        
        avrotize_queue = []
        while not SchemaUtils.schema_references_collected.issubset(self.ctx.loader.get_schemas_handled()):
            for schema_reference in set(SchemaUtils.schema_references_collected):
                if schema_reference not in self.ctx.loader.get_schemas_handled():
                    self.ctx.loader.add_schema_to_handled(schema_reference)
                    self.ctx.loader.set_current_url(None)
                    schema_format = None
                    class_name = ''
                    schema_format_short = ''

                    # Split off a suffix reference with ':'
                    if ":" in schema_reference:
                        schema_reference, class_name = schema_reference.split(
                            ":")

                    # If the scheme reference is a JSON Pointer reference, we resolve it
                    # to an object in the document. Remove a leading # if present
                    schema_root = None
                    if schema_reference.startswith("#"):
                        path_elements = schema_reference.split('/')
                        if path_elements[-2] == "versions":
                            xreg_file = path_elements[-3]
                        else:
                            xreg_file = path_elements[-1]

                        if not class_name:
                            class_name = xreg_file

                        try:
                            match = jsonpointer.resolve_pointer(
                                xregistry_document, schema_reference[1:])
                            if not match:
                                continue
                            schema_root = match
                        except jsonpointer.JsonPointerException as e:
                            logger.error("Error resolving JSON Pointer: %s", str(e))
                    
                    if not schema_root:
                        if schema_reference.startswith("#"):
                            schema_reference = schema_reference[1:]

                        type_ref = ''
                        if '#' in schema_reference:
                            schema_reference, type_ref = schema_reference.split("#")
                        if schema_reference.startswith("/"):
                            schema_reference = urllib.parse.urljoin(self.ctx.base_uri, schema_reference)            
                            schema_reference, fragment = urllib.parse.urldefrag(schema_reference)
                        
                        schema_reference, schema_root = self.ctx.loader.load(
                            schema_reference, self.headers, True, 
                            ignore_handled=True,
                            messagegroup_filter=self.ctx.messagegroup_filter)
                        if type_ref:
                            try:
                                match = jsonpointer.resolve_pointer(
                                    xregistry_document, type_ref)
                                if not match:
                                    continue
                                schema_root = match
                            except jsonpointer.JsonPointerException as e:
                                logger.error(
                                    "Error resolving JSON Pointer: %s", str(e))
                                continue

                    if schema_root and isinstance(schema_root, dict) and isinstance(schema_reference, str):
                        # now we need to figure out what the reference points to.
                        # a) This could be an inline schema inside a message definition
                        # b) This could be an inline schema inside a schema definition
                        # c) This could yet be a schema definition in a separate file referenced
                        #    by the schemaurl attribute inside a schema version referenced by
                        #    the local reference

                        schema_version = None
                        if "versions" in schema_root:
                            # the reference pointed to a schema definition. Now we need to find the
                            # most recent version in the versions dictionary by sorting the keys
                            # and picking the last one. To sort the keys, we need to make them the same length
                            # by prepending spaces to the keys that are shorter than the longest key
                            if not class_name:
                                class_name = str(schema_root.get("schemaid", ''))
                            parent_reference = schema_reference.rsplit(
                                "/", 2)[0]
                            parent = jsonpointer.resolve_pointer(
                                xregistry_document, parent_reference[1:])
                            if parent and isinstance(parent, dict):
                                prefix = parent.get("schemagroupid", '')
                                if not class_name.startswith(prefix):
                                    class_name = prefix + '.' + class_name
                            versions = schema_root["versions"]
                            if not isinstance(versions, dict):
                                raise RuntimeError(
                                    "Schema versions not found: " + schema_reference if schema_reference else '')
                            max_key_length = max([len(key)
                                                 for key in versions.keys()])
                            sorted_keys = sorted(versions.keys(), key=lambda key: key.rjust(
                                max_key_length))  # pylint: disable=cell-var-from-loop
                            schema_version = versions[sorted_keys[-1]]
                        elif "schema" in schema_root or "schemaurl" in schema_root or "schema" in schema_root:
                            # the reference pointed to a schema version definition
                            schema_version = schema_root
                            if "schemaid" not in schema_root:
                                parent_reference = schema_reference.rsplit(
                                    "/", 1)[0]
                                parent = jsonpointer.resolve_pointer(
                                    xregistry_document, parent_reference[1:])
                                if parent and isinstance(parent, dict) and not class_name:
                                    class_name = parent.get("schemaid", class_name)
                            else:
                                class_name = schema_root.get("schemaid", class_name)
                            if "defaultversionurl" not in schema_root and "self" not in schema_root:
                                parent_reference = parent_reference.rsplit(
                                    "/", 2)[0]
                                parent = jsonpointer.resolve_pointer(
                                    xregistry_document, parent_reference[1:])
                                if parent and isinstance(parent, dict):
                                    prefix = parent.get("schemagroupid", '')
                                    if not class_name.startswith(prefix):
                                        class_name = prefix + '.' + class_name
                            else:
                                version_url = str(schema_root.get("defaultversionurl", schema_root.get("self", '')))
                                # version url is {baseurl}/schemagroups/{schemagroupid}/schemas/{schemaid}/versions/{versionid}
                                match = re.search(r"/schemagroups/([^/]+)/", version_url)
                                if match:
                                    prefix = match.group(1)
                                else:
                                    raise RuntimeError(f"Schema group ID not found in version URL: {version_url}")
                                if not class_name.startswith(prefix):
                                    class_name = prefix + '.' + class_name

                        if schema_version and isinstance(schema_version, dict):
                            schema_format = ''
                            if "dataschemaformat" in schema_version:
                                schema_format = str(
                                    schema_version["dataschemaformat"])
                            elif "format" in schema_version:
                                schema_format = str(schema_version["format"])

                            if not schema_format:
                                raise RuntimeError(
                                    "Schema format not found: " + schema_reference if schema_reference else '')

                            # case c): if the schema version contains a schemaurl attribute, then we need to
                            # add the schemaurl to the list of schemas to be processed and continue
                            if "schemaurl" in schema_version:
                                schema_url = str(schema_version["schemaurl"])
                                if schema_url not in SchemaUtils.schema_files_collected:
                                    SchemaUtils.schema_files_collected.add(
                                        schema_url)
                                continue
                            elif "schema" in schema_version or "schema" in schema_version:
                                # case b): the schema version does not contain a schemaurl attribute, so we
                                # assume that the schema is inline and we can proceed to render it
                                if "schema" in schema_version:
                                    schema_root = schema_version["schema"]
                                else:
                                    schema_root = schema_version["schema"]

                                self.ctx.loader.set_current_url(
                                    schema_reference)
                                schema_format_short = ''
                                format_string = schema_format.lower()
                                if format_string.startswith("proto"):
                                    schema_format_short = "proto"
                                elif format_string.startswith("jsonschema"):
                                    schema_format_short = "json"
                                elif format_string.startswith("avro"):
                                    schema_format_short = "avro"
                        elif schema_root and isinstance(schema_root, str):
                            # schema is a string, so we assume it's an inline schema
                            if self.is_proto_doc(schema_root):
                                schema_format_short = 'proto'
                                schema_format = 'proto3'
                            else:
                                raise RuntimeError(
                                    "Schema format not found: " + schema_reference if schema_reference else '')

                        if not isinstance(schema_reference, str):
                            raise RuntimeError(
                                "Schema reference not found: " + schema_reference if schema_reference else '')

                        if self.language in ["py", "cs", "java", "js", "ts"] and schema_format_short != "proto":
                            if schema_format_short == "json" and isinstance(schema_root, (dict, list)):
                                # For JSON schemas, always use schema_type to get full type name including namespace
                                full_type_name = SchemaUtils.schema_type(
                                    self.ctx, schema_reference, self.data_project_name, xregistry_document, schema_format or "jsonschema/draft-07"
                                )
                                schema_root = self.convert_jsons_to_avro(
                                    schema_reference, schema_root,
                                    namespace_name=JinjaFilters.namespace(
                                        full_type_name if full_type_name else ''),
                                    class_name=JinjaFilters.pascal(
                                        JinjaFilters.strip_namespace(full_type_name))
                                )
                                schema_format_short = "avro"
                            avrotize_queue.append({ "schema_reference": schema_reference, "schema_root": schema_root, "class_name": class_name, "schema_format_short": schema_format_short })
                        else:
                            self.render_schema_templates(
                                schema_format_short, self.data_project_name, class_name, self.language,
                                project_data_dir, xreg_file, schema_root, schema_template_dirs,
                                schema_env, self.template_args, self.suppress_schema_output
                            )
                        continue
                    else:
                        logger.warning("Unable to find schema reference %s",
                                       schema_reference if schema_reference else '')

        # process the avrotize queue into a single project
        if len(avrotize_queue) > 0:
            avro_enabled = self.template_args.get("avro-encoding", "false") == "true" or schema_format_short == any("avro" in a["schema_format_short"] for a in avrotize_queue)
            json_enabled = self.template_args.get("json-encoding", "true") == "true"
            merged_schema = []
            for a in avrotize_queue:
                if isinstance(a["schema_root"], list):
                    merged_schema.extend(a["schema_root"])
                else:
                    merged_schema.append(a["schema_root"])
            if len(merged_schema) == 1:
                merged_schema = merged_schema[0]

            if self.language == "py":
                avrotize.convert_avro_schema_to_python(
                    merged_schema, project_data_dir, package_name=self.data_project_name,
                    dataclasses_json_annotation=json_enabled, avro_annotation=avro_enabled
                )
                # avrotize now generates proper class exports in __init__.py - no post-processing needed
                # self._fix_python_data_package_init(project_data_dir, self.data_project_name)
            elif self.language == "cs":
                # Determine if we need to pass base_namespace:
                # - For native Avro schemas (e.g., fabrikam), namespaces are partial: "Net.Fabrikam.Telemetry"
                # - For JSON schemas converted to Avro (e.g., contoso), namespaces already include project name: "TestProjectData.Contoso.ERP.Events"
                # Check the first schema to see if its namespace already starts with the project name
                needs_base_namespace = False
                schema_list = merged_schema if isinstance(merged_schema, list) else [merged_schema]
                for schema in schema_list:
                    if isinstance(schema, dict) and 'namespace' in schema:
                        ns = schema['namespace']
                        if not ns.startswith(self.data_project_name):
                            needs_base_namespace = True
                        break
                
                avrotize.convert_avro_schema_to_csharp(
                    merged_schema, project_data_dir,
                    base_namespace=self.data_project_name if needs_base_namespace else '',
                    project_name=self.data_project_name,
                    pascal_properties=True, system_text_json_annotation=json_enabled, avro_annotation=avro_enabled
                )
            elif self.language == "java":
                avrotize.convert_avro_schema_to_java(
                    merged_schema, project_data_dir, package_name=self.data_project_name,
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
        self.render_code_templates(
            self.project_name, self.main_project_name, self.data_project_name, self.style, project_dir, xregistry_document,
            code_template_dirs, code_env, True, self.template_args, self.suppress_code_output
        )

        SchemaUtils.schema_references_collected = set()

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
                    print(f"DEBUG: Calling avrotize with namespace={namespace_name}, class={class_name}")
                    avrotize.convert_jsons_to_avro(
                        jsons_file.name, avro_file.name, namespace=namespace_name, root_class_name=class_name
                    )
                    schema_root = json.loads(avro_file.read())
                    schema_ns = schema_root.get('namespace', 'NO_NAMESPACE') if isinstance(schema_root, dict) else 'NOT_DICT'
                    print(f"DEBUG: After avrotize: schema namespace={schema_ns}")
                    logger.debug(f"Converted JSON to Avro: namespace={namespace_name}, class={class_name}, schema namespace={schema_ns}")
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
                                    file_name = self.resolve_string(file_name_base, {"classdir": package_class_name })
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
                class_name = SchemaUtils.concat_namespace(
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
                        class_name = SchemaUtils.concat_namespace(
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
                rendered = template.render(args)
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
        except TemplateRuntimeError as err:
            logger.error("%s", err)
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
                                 JinjaExtensions.ExitExtension, JinjaExtensions.TimeExtension])
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
        env.filters['exists'] = JinjaFilters.exists
        env.filters['existswithout'] = JinjaFilters.exists_without
        env.filters['push'] = self.ctx.stacks.push
        env.filters['pushfile'] = self.ctx.stacks.push_file
        env.filters['save'] = self.ctx.stacks.save
        env.globals['pop'] = self.ctx.stacks.pop
        env.globals['stack'] = self.ctx.stacks.stack
        env.globals['get'] = self.ctx.stacks.get
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
