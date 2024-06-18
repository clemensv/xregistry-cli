# pylint: disable=too-many-arguments, line-too-long

"""Renderer for templates."""

import glob
import json
import os
import re
import tempfile
import uuid
import xml.etree.ElementTree as ET
import toml
from typing import Any, Dict, List, Optional, Union

import avrotize
import jinja2
import jsonpointer
from jinja2 import Template, TemplateAssertionError, TemplateNotFound, TemplateRuntimeError, TemplateSyntaxError

from xregistry.cli import logger
from xregistry.generator.generator_context import GeneratorContext
from xregistry.generator.jinja_extensions import JinjaExtensions
from xregistry.generator.jinja_filters import JinjaFilters
from xregistry.generator.schema_utils import SchemaUtils
from xregistry.generator.url_utils import URLUtils

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, None]

class TemplateRenderer:
    """Renderer for templates."""

    def __init__(self, ctx: GeneratorContext, project_name: str, language: str, style: str, output_dir: str,
                 definitions_file_arg: str, headers: Dict[str, str], template_dirs: List[str], template_args: Dict[str, Any],
                 suppress_code_output: bool, suppress_schema_output: bool) -> None:
        self.ctx = ctx
        self.project_name = project_name
        self.language = language
        self.style = style
        self.output_dir = output_dir
        self.definitions_file_arg = definitions_file_arg
        self.headers = headers
        self.template_dirs = template_dirs
        self.template_args = template_args
        self.suppress_code_output = suppress_code_output
        self.suppress_schema_output = suppress_schema_output

        self.ctx.uses_avro = False
        self.ctx.uses_protobuf = False
        logger.debug("Initialized TemplateRenderer")

    def generate(self) -> None:
        """Generate code and schemas from templates."""
        definitions_file, docroot = self.ctx.loader.load(
            self.definitions_file_arg, self.headers, self.style == "schema")
        if not definitions_file or not docroot:
            raise RuntimeError(f"Definitions file not found or invalid {self.definitions_file_arg}")

        solution_dir = os.path.join(self.output_dir)
        project_data_dir = os.path.join(solution_dir, f"{self.project_name}_data")
        project_dir = os.path.join(solution_dir, self.project_name)

        self.template_args["project_data_dir"] = project_data_dir
        self.template_args["project_dir"] = project_dir
        
        self.ctx.set_current_dir(project_dir)

        pt = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
        code_template_dir = os.path.join(pt, "templates", self.language, self.style)
        code_template_dirs = [code_template_dir]
        code_template_and_include_dirs = [code_template_dir, os.path.join(pt, "templates", self.language, "_common")]
        schema_template_dirs = [os.path.join(pt, "templates", self.language, "_schemas")]

        for template_dir in self.template_dirs if self.template_dirs else []:
            template_dir = os.path.join(os.path.curdir, template_dir)
            if not os.path.isdir(template_dir):
                raise RuntimeError(f"Template directory not found {template_dir}")
            code_template_dir = os.path.join(template_dir, self.language, self.style)
            if os.path.exists(code_template_dir) and os.path.isdir(code_template_dir):
                code_template_dirs = [code_template_dir]
                code_template_and_include_dirs = [code_template_dir, os.path.join(pt, "templates", self.language, "_common")]
                schema_template_dirs = [os.path.join(pt, "templates", self.language, "_schemas")]
                break

        code_env = self.setup_jinja_env(code_template_and_include_dirs)
        schema_env = self.setup_jinja_env(schema_template_dirs)

        self.render_code_templates(self.project_name, self.style, project_dir, docroot,
                                   code_template_dirs, code_env, False, self.template_args, self.suppress_code_output)
        self.render_code_templates(self.project_name, self.style, project_data_dir, docroot,
                                   schema_template_dirs, schema_env, False, self.template_args, self.suppress_schema_output)

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
                        schema_reference, class_name = schema_reference.split(":")

                    # If the scheme reference is a JSON Pointer reference, we resolve it
                    # to an object in the document. Remove a leading # if present
                    if schema_reference.startswith("#"):
                        path_elements = schema_reference.split('/')
                        if path_elements[-2] == "versions":
                            definitions_file = path_elements[-3]
                        else:
                            definitions_file = path_elements[-1]

                        if not class_name:
                            class_name = definitions_file

                        try:
                            match = jsonpointer.resolve_pointer(docroot, schema_reference[1:])
                            if not match:
                                continue
                            schema_root = match
                        except jsonpointer.JsonPointerException as e:
                            logger.error("Error resolving JSON Pointer: %s", str(e))
                            continue
                    else:
                        type_ref = ''
                        if '#' in schema_reference:
                            schema_reference, type_ref = schema_reference.split("#")
                        schema_reference, docroot = self.ctx.loader.load(schema_reference, self.headers, True)
                        if type_ref:
                            try:
                                match = jsonpointer.resolve_pointer(docroot, type_ref)
                                if not match:
                                    continue
                                schema_root = match
                            except jsonpointer.JsonPointerException as e:
                                logger.error("Error resolving JSON Pointer: %s", str(e))
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
                                class_name = str(schema_root.get("id", ''))
                            parent_reference = schema_reference.rsplit("/", 2)[0]
                            parent = jsonpointer.resolve_pointer(docroot, parent_reference[1:])
                            if parent and isinstance(parent, dict):
                                prefix = parent.get("id", '')
                                if not class_name.startswith(prefix):
                                    class_name = prefix + '.' + class_name
                            versions = schema_root["versions"]
                            if not isinstance(versions, dict):
                                raise RuntimeError(
                                    "Schema versions not found: " + schema_reference if schema_reference else '')
                            max_key_length = max([len(key) for key in versions.keys()])
                            sorted_keys = sorted(versions.keys(), key=lambda key: key.rjust(max_key_length)) # pylint: disable=cell-var-from-loop
                            schema_version = versions[sorted_keys[-1]]
                        elif "schema" in schema_root or "schemaurl" in schema_root or "schema" in schema_root:
                            # the reference pointed to a schema version definition
                            schema_version = schema_root
                            parent_reference = schema_reference.rsplit("/", 1)[0]
                            parent = jsonpointer.resolve_pointer(docroot, parent_reference[1:])
                            if parent and isinstance(parent, dict) and not class_name:
                                class_name = parent.get("id", class_name)
                            parent_reference = parent_reference.rsplit("/", 2)[0]
                            parent = jsonpointer.resolve_pointer(docroot, parent_reference[1:])
                            if parent and isinstance(parent, dict):
                                prefix = parent.get("id", '')
                                if not class_name.startswith(prefix):
                                    class_name = prefix + '.' + class_name

                        if schema_version and isinstance(schema_version, dict):
                            schema_format = ''
                            if "schemaformat" in schema_version:
                                schema_format = str(schema_version["schemaformat"])
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
                                    SchemaUtils.schema_files_collected.add(schema_url)
                                continue
                            elif "schema" in schema_version or "schema" in schema_version:
                                # case b): the schema version does not contain a schemaurl attribute, so we
                                # assume that the schema is inline and we can proceed to render it
                                if "schema" in schema_version:
                                    schema_root = schema_version["schema"]
                                else:
                                    schema_root = schema_version["schema"]

                                self.ctx.loader.set_current_url(schema_reference)
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
                                schema_root = self.convert_jsons_to_avro(
                                    schema_reference, schema_root,
                                    namespace_name=JinjaFilters.namespace(class_name if class_name else ''),
                                    class_name=JinjaFilters.pascal(JinjaFilters.strip_namespace(class_name))
                                )
                                schema_format_short = "avro"
                            avro_enabled = self.template_args.get("avro-encoding", "false") == "true"
                            json_enabled = self.template_args.get("json-encoding", "true") == "true"
                            if self.language == "py":
                                avrotize.convert_avro_schema_to_python(
                                    schema_root, project_data_dir, package_name=self.project_name,
                                    dataclasses_json_annotation=json_enabled, avro_annotation=avro_enabled
                                )
                            elif self.language == "cs":
                                avrotize.convert_avro_schema_to_csharp(
                                    schema_root, project_data_dir, base_namespace=JinjaFilters.pascal(self.project_name),
                                    pascal_properties=True, system_text_json_annotation=json_enabled, avro_annotation=avro_enabled
                                )
                            elif self.language == "java":
                                avrotize.convert_avro_schema_to_java(
                                    schema_root, project_data_dir, package_name=self.project_name,
                                    jackson_annotation=json_enabled, avro_annotation=avro_enabled
                                )
                            elif self.language == "js":
                                avrotize.convert_avro_schema_to_javascript(
                                    schema_root, project_data_dir, package_name=self.project_name, avro_annotation=avro_enabled
                                )
                            elif self.language == "ts":
                                avrotize.convert_avro_schema_to_typescript(
                                    schema_root, project_data_dir, package_name=self.project_name,
                                    avro_annotation=avro_enabled, typedjson_annotation=json_enabled
                                )
                        else:
                            self.render_schema_templates(
                                schema_format_short, self.project_name, class_name, self.language,
                                project_data_dir, definitions_file, schema_root, schema_template_dirs,
                                schema_env, self.template_args, self.suppress_schema_output
                            )
                        continue
                    else:
                        logger.warning("Unable to find schema reference %s", schema_reference if schema_reference else '')

        self.render_code_templates(
            self.project_name, self.style, project_dir, docroot,
            code_template_dirs, code_env, True, self.template_args, self.suppress_code_output
        )

        SchemaUtils.schema_references_collected = set()

        if self.style == "schema":
            self.render_schema_templates(
                None, self.project_name, None, self.language,
                project_dir, definitions_file, docroot, schema_template_dirs, schema_env,
                self.template_args, self.suppress_schema_output
            )


    def convert_proto_to_avro(self, schema_reference: str, schema_root: str) -> JsonNode:
        """Convert a proto schema to an Avro schema."""
        logger.debug("Converting proto schema to Avro schema")
        if schema_reference.startswith("#"):
            proto_file = tempfile.NamedTemporaryFile(delete=False, suffix=".proto")
            try:
                avro_file = tempfile.NamedTemporaryFile(delete=False, suffix=".avsc")
                try:
                    proto_file.write(schema_root.encode('utf-8'))
                    proto_file.close()
                    avrotize.convert_proto_to_avro(proto_file.name, avro_file.name)
                    schema_root = json.loads(avro_file.read())
                finally:
                    avro_file.close()
                    os.unlink(avro_file.name)
            finally:
                os.unlink(proto_file.name)
        else:
            avro_file = tempfile.NamedTemporaryFile(delete=False, suffix=".avsc")
            try:
                avrotize.convert_proto_to_avro(schema_reference, avro_file.name)
                schema_root = json.loads(avro_file.read())
            finally:
                avro_file.close()
                os.unlink(avro_file.name)
        return schema_root

    def convert_jsons_to_avro(self, schema_reference: str, schema_root: JsonNode, namespace_name: str = '', class_name: str = '') -> JsonNode:
        """Convert a JSON schema to an Avro schema."""
        logger.debug("Converting JSON schema to Avro schema")
        if schema_reference.startswith("#"):
            jsons_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jsons")
            try:
                avro_file = tempfile.NamedTemporaryFile(delete=False, suffix=".avsc")
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
            avro_file = tempfile.NamedTemporaryFile(delete=False, suffix=".avsc")
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
            self, project_name: str, style: str, output_dir: str, docroot: JsonNode,
            code_template_dirs: List[str], env: jinja2.Environment, post_process: bool,
            template_args: Dict[str, Any], suppress_output: bool = False) -> None:
        """Render code templates."""
        logger.debug("Rendering code templates for project: %s, style: %s", project_name, style)
        if not isinstance(docroot, dict):
            raise RuntimeError("Document root is not a dictionary")
        class_name = None
        for template_dir in code_template_dirs:
            for root, _, files in os.walk(template_dir):
                relpath = os.path.relpath(root, template_dir).replace("\\", "/")
                if relpath == ".":
                    relpath = ""

                for file in files:
                    if not file.endswith(".jinja") or (not post_process and file.startswith("_")) or (post_process and not file.startswith("_")):
                        continue

                    template_path = relpath + "/" + file
                    scope = docroot
                    class_name = ''

                    file_dir = file_dir_base = os.path.join(output_dir, os.path.join(*relpath.split("/")))
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

                    file_name_base = file_name_base.replace("{projectname}", JinjaFilters.pascal(project_name))
                    file_name = file_name_base
                    if file_name.startswith("{class"):
                        if isinstance(scope, dict) and "messagegroups" in scope:
                            if "endpoints" in docroot:
                                endpoints = docroot["endpoints"]
                            else:
                                endpoints = None
                            if "schemagroups" in docroot:
                                schemagroups = docroot["schemagroups"]
                            else:
                                schemagroups = None

                            group_dict = scope["messagegroups"]
                            if not isinstance(group_dict, dict):
                                raise RuntimeError("Messagegroups is not a dictionary")
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
                                class_package_name = scope_parts[-1]
                                package_name = id_
                                if not package_name:
                                    package_name = project_name
                                elif not package_name.startswith(project_name):
                                    package_name = project_name + "." + package_name
                                if not class_package_name:
                                    raise RuntimeError("Class name not found")
                                if file_name_base.find("{classdir}") > -1:
                                    file_dir = os.path.join(file_dir_base, os.path.join(*package_name.split(".")).lower())
                                    file_name = file_name_base.replace("{classdir}", JinjaFilters.pascal(class_package_name))
                                    class_name = f'{package_name}.{file_name.split(".")[0]}'
                                else:
                                    file_name = file_name_base.replace("{classfull}", id_).replace("{classname}", JinjaFilters.pascal(class_package_name))
                                if not class_name:
                                    raise RuntimeError("Class name not found")
                                self.render_template(project_name, class_name, subscope, file_dir, file_name, template, template_args, suppress_output)
                        continue

                    if file_name.startswith("{projectsrc}"):
                        file_dir = os.path.join(file_dir_base, "src", os.path.join(*project_name.split("."))).lower()
                        file_name = file_name_base.replace("{projectsrc}", "")
                    if file_name.startswith("{projectdir}"):
                        file_dir = os.path.join(file_dir_base, os.path.join(*project_name.split("."))).lower()
                        file_name = file_name_base.replace("{projectdir}", "")
                    if file_name.startswith("{rootdir}"):
                        file_dir = self.output_dir
                        file_name = file_name_base.replace("{rootdir}", "")
                    
                    self.render_template(project_name, class_name, scope, file_dir, file_name, template, template_args, suppress_output)

    def render_schema_templates(
            self, schema_type: Optional[str], project_name: str, class_name: Optional[str], language: str,
            output_dir: str, definitions_file: str, docroot: JsonNode, schema_template_dirs: List[str],
            env: jinja2.Environment, template_args: Dict[str, Any], suppress_output: bool = False) -> None:
        """Render schema templates."""
      
        scope = docroot
        if schema_type is None:
            if self.is_proto_doc(docroot):
                schema_type = "proto"
            elif isinstance(docroot, dict) and "type" in docroot and docroot["type"] == "record":
                schema_type = "avro"
            else:
                schema_type = "json"

        if schema_type == "proto":
            self.ctx.uses_protobuf = True
            if isinstance(docroot, str) and self.is_proto_doc(docroot) and class_name:
                local_class_name = JinjaFilters.strip_namespace(class_name)
                match = re.search(r"message[\s]+([\w]+)[\s]*{", docroot)
                found = False
                if local_class_name and match:
                    for g in match.groups():
                        if g.lower() == local_class_name.lower():
                            class_name = JinjaFilters.namespace_dot(class_name) + g
                            found = True
                            break
                if not found and match and match.groups() and len(match.groups()) == 1:
                    class_name = JinjaFilters.namespace_dot(str(class_name)) + match.groups()[0]
                elif not found:
                    raise RuntimeError(f"Proto: Top-level message {class_name} not found in Proto schema")
        elif schema_type == "avro":
            self.ctx.uses_avro = True
            if isinstance(docroot, dict) and "type" in docroot and docroot["type"] == "record":
                class_name = SchemaUtils.concat_namespace(
                    str(docroot.get("namespace", "")), str(docroot["name"]))
            elif isinstance(docroot, list):
                if class_name:
                    cns = class_name.split(".", 1)
                    if len(cns) == 2:
                        ns = cns[0]
                        cn = cns[1]
                    else:
                        ns = ""
                        cn = cns[0]
                for record in docroot:
                    if isinstance(record, dict) and "type" in record and record["type"] == "record" \
                            and "namespace" in record and "name" in record \
                            and str(record["name"]).lower() == cn and str(record["namespace"]).lower() == ns:
                        class_name = SchemaUtils.concat_namespace(
                            str(record.get("namespace", "")), str(record["name"]))
                        break
                raise RuntimeError("Avro: Top-level record object not found in Avro schema: ")

        file_dir = file_dir_base = output_dir
        if class_name is None:
            class_name = os.path.basename(definitions_file).split(".")[0]
        for template_dir in schema_template_dirs:
            schema_files = glob.glob(
                f"**/_{schema_type}.*.jinja", root_dir=template_dir, recursive=True)
            for schema_file in schema_files:
                schema_file = schema_file.replace("\\", "/")
                try:
                    template = env.get_template(schema_file)
                except Exception as err: # pylint: disable=broad-except
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
                file_name_base = file_name_base.replace(
                    "{projectname}", project_name)
                file_name_base = file_name_base.replace("{classname}", class_name)

                file_name = file_name_base
                if file_name_base.find("{classdir}") > -1:
                    scope_parts = class_name.split(".")
                    class_package_name = scope_parts[-1]
                    package_name = '.'.join(scope_parts[:-1])
                    if not package_name.startswith(project_name):
                        package_name = project_name + "." + package_name

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
                    project_name, class_name, scope, file_dir,
                    file_name, template, template_args, suppress_output)


    def render_template(
            self, project_name: str, class_name: str, scope: JsonNode, file_dir: str, file_name: str,
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
                args["project_name"] = project_name
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
    def dependency(language: str, runtime_version:str, dependency_name:str):
        """Get the dependency string for a given language, runtime version, and dependency name."""
        # Define the path to the master project file based on the language and runtime version
        if language == 'cs':
            master_project_path = os.path.join(os.path.dirname(__file__), f'../dependencies/cs/{runtime_version}/dependencies.csproj')
        elif language == 'py':
            master_project_path = os.path.join(os.path.dirname(__file__), f'../dependencies/python/{runtime_version}/pyproject.toml')
        elif language == 'ts':
            master_project_path = os.path.join(os.path.dirname(__file__), f'../dependencies/typescript/{runtime_version}/package.json')
        elif language == 'java':
            master_project_path = os.path.join(os.path.dirname(__file__), f'../dependencies/java/{runtime_version}/pom.xml')
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
                        dependency_str = ET.tostring(package, encoding='unicode')
                        return dependency_str
                if not triedadd:
                    os.system(f"dotnet add {master_project_path} package {dependency_name}")
                    triedadd = True
                else:
                    raise ValueError(f"Dependency '{dependency_name}' not found in runtime version '{runtime_version}' for language '{language}'.")

        elif language == 'py':
            # Parse the pyproject.toml file
            with open(master_project_path, 'r') as file:
                pyproject_data = toml.load(file)

            # Find the desired dependency
            dependencies = pyproject_data.get('tool', {}).get('poetry', {}).get('dependencies', {})
            if dependency_name in dependencies:
                version = dependencies[dependency_name]
                dependency_str = f"{dependency_name} = \"{version}\""
                return dependency_str

            # If the dependency is not found, raise an error
            raise ValueError(f"Dependency '{dependency_name}' not found in runtime version '{runtime_version}' for language '{language}'.")

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
            raise ValueError(f"Dependency '{dependency_name}' not found in runtime version '{runtime_version}' for language '{language}'.")

        elif language == 'java':
            # Parse the pom.xml file
            tree = ET.parse(master_project_path)
            root = tree.getroot()

            # Find the desired dependency
            for dependency in root.findall(".//dependency"):
                artifact_id = dependency.find('artifactId')
                if artifact_id is not None and artifact_id.text == dependency_name:
                    # Convert the XML element back to string including its children
                    dependency_str = ET.tostring(dependency, encoding='unicode')
                    return dependency_str

            # If the dependency is not found, raise an error
            raise ValueError(f"Dependency '{dependency_name}' not found in runtime version '{runtime_version}' for language '{language}'.")

    def setup_jinja_env(self, template_dirs: List[str]) -> jinja2.Environment:
        """Create the Jinja environment and load extensions."""
        logger.debug("Setting up Jinja environment with template dirs: %s", template_dirs)
        loader = jinja2.FileSystemLoader(template_dirs, followlinks=True)
        env = jinja2.Environment(loader=loader, extensions=[JinjaExtensions.ExitExtension, JinjaExtensions.TimeExtension])
        env.filters['regex_search'] = JinjaFilters.regex_search
        env.filters['regex_replace'] = JinjaFilters.regex_replace
        env.filters['pascal'] = JinjaFilters.pascal
        env.filters['snake'] = JinjaFilters.snake
        env.filters['strip_namespace'] = JinjaFilters.strip_namespace
        env.filters['namespace'] = JinjaFilters.namespace
        env.filters['namespace_dot'] = JinjaFilters.namespace_dot
        env.filters['concat_namespace'] = JinjaFilters.concat_namespace
        env.filters['strip_dots'] = JinjaFilters.strip_dots
        env.filters['lstrip'] = JinjaFilters.lstrip
        env.filters['schema_type'] = lambda schema_ref, project_name, root, schema_format: SchemaUtils.schema_type(self.ctx, schema_ref, project_name, root, schema_format)
        env.filters['camel'] = JinjaFilters.camel
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

    def is_proto_doc(self, docroot: JsonNode) -> bool:
        """Check if the document is a proto document."""
        return isinstance(docroot, str) and re.search(r"syntax[\s]*=[\s]*\"proto3\"", docroot) is not None
