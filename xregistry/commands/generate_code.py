# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,too-many-lines,global-variable-not-assigned,global-variable-undefined,global-statement,line-too-long
# mypy: disable-error-code="import-untyped"

import datetime
import json
import urllib.request
import urllib.parse
import re
import glob
import os
import tempfile
from typing import Any, Dict, List, Set
import uuid
import yaml
import jinja2

import jsonpointer
import avrotize

from jinja2 import Template, nodes
from jinja2.ext import Extension
from jinja2 import TemplateAssertionError, TemplateSyntaxError, TemplateRuntimeError, TemplateNotFound

from .validate_definitions import validate
from .core import load_definitions, get_schemas_handled, add_schema_to_handled, reset_schemas_handled, set_current_url

JsonNode = Dict[str, 'JsonNode'] | List['JsonNode'] | str | None

# These are the global variables that are switched
# to True when a schema is found that uses Avro or Protobuf,
# respectively. When either of these is True, the generator
# will run a second time for the output to consistently include
# Avro and/or Protobuf dependencies
uses_avro: bool = False
uses_protobuf: bool = False


def geturlhost(url: str) -> str | None:
    return urllib.parse.urlparse(url).hostname


def geturlpath(url: str) -> str:
    return urllib.parse.urlparse(url).path


def geturlscheme(url: str) -> str:
    return urllib.parse.urlparse(url).scheme


def geturlport(url: str) -> str:
    return str(urllib.parse.urlparse(url).port)


# Create a global stack structure
context_stacks = dict()
context_dict = dict()
current_dir = ""

# Jinja extension to push a value onto a named stack


def push(value, stack_name):
    """ Push a value onto a named stack. """
    global context_stacks
    if stack_name not in context_stacks:
        context_stacks[stack_name] = list()
    context_stacks[stack_name].append(value)
    return ""


def pushfile(value, name):
    """ Push a value onto a named stack. """
    global context_stacks
    if "files" not in context_stacks:
        context_stacks["files"] = list()
    context_stacks["files"].append((os.path.join(current_dir, name), value))
    return ""

# Jinja extension to pop a value from a named stack


def pop(stack_name):
    """ Pop a value from a named stack. """
    global context_stacks
    if stack_name not in context_stacks:
        context_stacks[stack_name] = list()
    return context_stacks[stack_name].pop()

# Jinja extension to get the full contents of a named stack


def stack(stack_name):
    """ Get the full contents of a named stack. """
    global context_stacks
    if stack_name not in context_stacks:
        context_stacks[stack_name] = list()
    return context_stacks[stack_name]

# Jinja extension to set a value


def save(value, prop_name):
    """ Save a value. """
    global context_dict
    context_dict[prop_name] = value
    return value

# Jinja extension to get a value


def get(prop_name):
    """ Get a value. """
    global context_dict
    if prop_name in context_dict:
        return context_dict[prop_name]
    return ""


# Jinja tag to exit the current template because
# something went wrong
class ExitExtension(Extension):
    tags = set(['exit'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        return nodes.CallBlock(self.call_method('_exit', [], lineno=lineno), [], [], []).set_lineno(lineno)

    def _exit(self, caller):
        raise StopIteration()


class UuidExtension(Extension):
    tags = {'uuid'}

    def parse(self, parser) -> nodes.Output:
        lineno = parser.stream.expect("name:uuid").lineno
        context = nodes.ContextReference()
        result = self.call_method("_render", [context], lineno=lineno)
        return nodes.Output([result], lineno=lineno)

    def _render(self, context) -> str:
        return uuid.uuid4().hex


class TimeExtension(Extension):
    tags = {'time'}

    def parse(self, parser) -> nodes.Output:
        lineno = parser.stream.expect("name:time").lineno
        context = nodes.ContextReference()
        result = self.call_method("_render", [context], lineno=lineno)
        return nodes.Output([result], lineno=lineno)

    def _render(self, context) -> str:
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# Jinja filter that checks whether the given property exists
# anywhere in the doc with the value prefixed with the given string (case-insensitive)
def exists(obj, prop, value):
    """ Check whether the given property exists anywhere in the doc with the value prefixed with the given string (case-insensitive) """
    def recursive_search(obj, prop, value):
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key.lower().startswith(prop) and isinstance(val, str) and val.lower().startswith(value):
                    return True
                if recursive_search(val, prop, value):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if recursive_search(item, prop, value):
                    return True
        return False

    return recursive_search(obj, prop, value)


def existswithout(obj, prop, value, propother, valueother):
    """ 
    Check whether the given property exists anywhere in the doc with the value prefixed with the given string (case-insensitive),
    but only if the other property does not exist with the other value.
    """
    def recursive_search(obj, prop, value, propother, valueother):
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key.lower().startswith(prop) and isinstance(val, str) and val.lower().startswith(value):
                    if not exists(obj, propother, valueother):
                        return True
                if recursive_search(val, prop, value, propother, valueother):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if recursive_search(item, prop, value, propother, valueother):
                    return True
        return False

    return recursive_search(obj, prop, value, propother, valueother)

# Jinja filter to perform a regex search. Returns a list of matches.


def regex_search(string, pattern):
    """ Perform a regex search. Returns a list of matches."""
    if string:
        match = re.findall(pattern, string)
        if match:
            return match
    return []


# Jinja filter to perform a regex search. Returns the found string.
def regex_replace(string, pattern, replacement):
    """ Perform a regex search. Returns the found string. """
    if string:
        return re.sub(pattern, replacement, string)
    return string


# Jinja filter to replace all characters that are not valid
# in C# identifiers with an underscore
def strip_invalid_identifier_characters(string):
    """ Replace all characters that are not valid in C# identifiers with an underscore. """
    if string:
        return re.sub(r'[^A-Za-z0-9_\.]', '_', string)
    return string


# Jinja filter that turns a string expression into PascalCase
# The input can be snake_case or camelCase or any other string
def pascal(string):
    """ Turn a string expression into PascalCase. """
    if '::' in string:
        strings = string.split('::')
        return strings[0] + '::' + '::'.join(pascal(s) for s in strings[1:])
    if '.' in string:
        strings = string.split('.')
        return '.'.join(pascal(s) for s in strings)
    if not string or len(string) == 0:
        return string
    words = []
    if '_' in string:
        # snake_case
        words = re.split(r'_', string)
    elif string[0].isupper():
        # PascalCase
        words = re.findall(r'[A-Z][a-z0-9_]*\.?', string)
    else:
        # camelCase
        words = re.findall(r'[a-z0-9]+\.?|[A-Z][a-z0-9_]*\.?', string)
    result = ''.join(word.capitalize() for word in words)
    return result


# Jinja filter that turns a string expression into snake_case
# The input can be PascalCase, camelCase, snake_case, or any other text

def snake(string):
    """ Turn a string expression into snake_case. """
    if '::' in string:
        strings = string.split('::')
        return strings[0] + '::' + '::'.join(snake(s) for s in strings[1:])
    if '.' in string:
        strings = string.split('.')
        return '.'.join(snake(s) for s in strings)
    if not string:
        return string
    result = re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()
    return result


# Jinja filter that turns a string expression into camelCase
# The input can be snake_case or PascalCase or any other string
def camel(string):
    """ Turn a string expression into camelCase. """
    if not string:
        return string
    if '::' in string:
        strings = string.split('::')
        return strings[0] + '::' + '::'.join(camel(s) for s in strings[1:])
    if '.' in string:
        strings = string.split('.')
        return '.'.join(camel(s) for s in strings)
    if '_' in string:
        # snake_case
        words = re.split(r'_', string)
    elif string[0].isupper():
        # PascalCase
        words = re.findall(r'[A-Z][^A-Z]*\.?', string)
    else:
        # default case: return string as-is
        return string
    camels = words[0].lower()
    for word in words[1:]:
        camels += word.capitalize()
    return camels

# Jinja filter that left-justified pads a string with spaces
# to the specified length


def pad(string, length):
    """ Left-justified pad a string with spaces to the specified length. """
    if string:
        return string.ljust(length)
    return string


# Jinja filter that strips the namespace/package portion off
# an expression. Assumes dot-notation, e.g. namespace.class
def strip_namespace(class_reference):
    """ Strip the namespace/package portion off an expression. Assumes dot-notation, e.g. namespace.class. """
    if class_reference:
        return re.sub(r'^.+\.', '', class_reference)
    return class_reference

# Jinja filter that gets the namespace/package portion off
# an expression. Assumes dot-notation, e.g. namespace.class


def namespace(class_reference, namespace_prefix=""):
    """ Get the namespace/package portion off an expression. Assumes dot-notation, e.g. namespace.class. """
    if class_reference:
        if '.' in class_reference:
            ns = re.sub(r'\.[^.]+$', '', class_reference)
            if namespace_prefix:
                # if ns.startswith(namespace_prefix):
                #    return ns
                # if namespace_prefix.startswith(ns):
                #    return namespace_prefix
                if ns:
                    return namespace_prefix + "." + ns
                else:
                    return namespace_prefix
            else:
                return ns
        else:
            return namespace_prefix
    return class_reference


def namespace_dot(class_reference, namespace_prefix=""):
    """

    Get the namespace/package portion off an expression. Assumes dot-notation, e.g. namespace.class

    Args:
        class_reference: The class reference.
        namespace_prefix: The namespace prefix.

    Returns:
        The namespace/package portion of the expression.

    """
    ns = namespace(class_reference, namespace_prefix)
    if ns:
        return ns + "."
    return ns

# Jinja filter that concats the namespace/package portions of
# an expression, removing the dots.


def strip_dots(class_reference) -> str:
    if class_reference:
        return "".join(class_reference.split("."))
    return class_reference

# Jinja filter that formats the given object as YAML


def toyaml(obj: Any, indent: int = 4) -> str:
    """

    Convert an object to a YAML string.

    Args:
        obj (Any): Input object to convert to YAML.
        indent (int, optional): Indent. Defaults to 4.

    Returns:
        str: YAML string.
    """
    return yaml.dump(obj, default_flow_style=False, indent=indent)


def proto(proto_text: str) -> str:
    """

    Convert a proto text to a formatted proto text.

    Args:
        proto_text (str): Input proto text.

    Returns:
        str: Formatted proto text.
    """
    # Add newlines after ';'
    proto_text = re.sub(r"([;{}])", r"\1\n", proto_text)

    # Indent all lines after '{' or '}'
    indent = 0
    lines = proto_text.split("\n")
    for i, line in enumerate(lines):
        line = re.sub(r"^\s*", "", line)
        if "}" in line:
            indent -= 1
        lines[i] = "    "*indent + line
        if "{" in line:
            indent += 1
    proto_text = "\n".join(lines)

    # Remove extra newlines
    proto_text = re.sub(r"\n{3,}", "\n\n", proto_text)

    return proto_text


# Jinja filter that determines the type name of an expression
# given a schema URL, specifically in CloudEvents' dataschema
# attribute. Schema URLs are collected by the filter as a side
# effect and then given to the generator
schema_files_collected: Set[str] = set()
schema_references_collected: Set[str] = set()


def get_json_pointer(root: JsonNode, node: JsonNode) -> str:
    """ Get the JSON Pointer to a node in a JSON document. """
    # This helper function recursively finds the path to the node.
    def find_path(current, target, path):
        if current is target:
            return path
        elif isinstance(current, dict):
            for k, v in current.items():
                new_path = find_path(v, target, path + [k])
                if new_path is not None:
                    return new_path
        elif isinstance(current, list):
            for i, item in enumerate(current):
                new_path = find_path(item, target, path + [str(i)])
                if new_path is not None:
                    return new_path
        return None

    # This function converts the path to a JSON Pointer string.
    def path_to_pointer(path):
        pointer = ""
        for p in path:
            # Escaping special characters in JSON Pointer
            escaped = p.replace("~", "~0").replace("/", "~1")
            pointer += f"/{escaped}"
        return pointer

    # Find the path from root to the node and convert it to JSON Pointer
    path = find_path(root, node, [])
    if path is None:
        raise RuntimeError("Node not found in document")
    return path_to_pointer(path)


def schema_type(schema_ref: JsonNode, project_name: str, root: JsonNode, schema_format: str = "jsonschema/draft-07"):
    """ Get the schema type from a schema reference. """

    global schema_files_collected
    global schema_references_collected

    class_name: str = ''
    schema_obj: JsonNode = None

    def resolve_pointer(root: JsonNode, schema_ref: str) -> JsonNode:
        obj = jsonpointer.resolve_pointer(root, schema_ref)
        if isinstance(obj, dict) or isinstance(obj, list) or isinstance(obj, str):
            return obj
        else:
            raise RuntimeError("Schema not found: " + schema_ref)

    if schema_format.lower().startswith("proto") and isinstance(schema_ref, str) and is_proto_doc(schema_ref):
        ptr = get_json_pointer(root, schema_ref)
        # we actually need the parent of the schema object, so we remove the last segment
        ptr = ptr.rsplit("/", 1)[0]
        schema_references_collected.add('#' + ptr)
        schema_format = schema_format.lower().split("/")[0]
        schema_obj = schema_ref
        schema_ref = '#' + ptr
    elif isinstance(schema_ref, str):
        # if the schema URL is a fragment, then it is a local reference
        if ":" in schema_ref:
            schema_ref, class_name = schema_ref.split(":")
        if schema_ref.startswith("#"):
            if not schema_ref in schema_references_collected:
                schema_references_collected.add(schema_ref)
            schema_obj = resolve_pointer(root, schema_ref[1:])
        else:
            # split the schema URL into a base URL and a fragment
            schema_ref, fragment = urllib.parse.urldefrag(schema_ref)
            # if the schema URL is a full URL, then it is an external reference
            _, schema_obj = load_definitions(schema_ref, {}, True)
            if fragment:
                fragment, class_name = fragment.split(":")
                schema_obj = resolve_pointer(schema_obj, fragment)

        schema_version = None
        if isinstance(schema_obj, dict) and "versions" in schema_obj and isinstance(schema_obj['versions'], dict):
            latestversion = str(schema_obj.get('latestversionid', ''))
            if not latestversion or latestversion not in schema_obj['versions']:
                # get all the versions and use the lexically greatest
                versions = schema_obj['versions']
                latestversion = max(versions.keys())
            if not latestversion in schema_obj['versions']:
                raise RuntimeError(
                    "Schema version not found: " + latestversion)
            schema_version = schema_obj['versions'][latestversion]
            if not class_name:
                class_name = str(schema_obj.get("id", ''))
            parent_reference = schema_ref.rsplit("/", 2)[0]
            parent = jsonpointer.resolve_pointer(root, parent_reference[1:])
            if parent and isinstance(parent, dict):
                prefix = parent.get("id", '')
                if not class_name.startswith(prefix):
                    class_name = prefix + '.' + class_name
        elif isinstance(schema_obj, dict):
            schema_version = schema_obj
            parent_reference = schema_ref.rsplit("/", 1)[0]
            parent = jsonpointer.resolve_pointer(root, parent_reference[1:])
            if parent and isinstance(parent, dict) and not class_name:
                class_name = parent.get("id", class_name)
            parent_reference = parent_reference.rsplit("/", 2)[0]
            parent = jsonpointer.resolve_pointer(root, parent_reference[1:])
            if parent and isinstance(parent, dict):
                prefix = parent.get("id", '')
                if not class_name.startswith(prefix):
                    class_name = prefix + '.' + class_name
        if not schema_version or not isinstance(schema_version, dict):
            raise RuntimeError("Schema version not found: " + schema_ref)
        if not "format" in schema_version or not isinstance(schema_version["format"], str) or schema_format != schema_version["format"]:
            raise RuntimeError("Schema format mismatch: " + schema_format + " != " + (
                str(schema_version["format"]) if "format" in schema_version else ''))
        schema_format = schema_version["format"].lower().split("/")[0]
        if "schemaurl" in schema_version:
            external_schema_url = str(schema_version["schemaurl"])
            _, schema_obj = load_definitions(external_schema_url, {}, True)
            if not schema_obj:
                raise RuntimeError("Schema not found: " + external_schema_url)
        elif "schema" in schema_version:
            schema_obj = schema_version["schema"]
        else:
            raise RuntimeError("Schema not found: " + schema_ref)
    else:
        ptr = get_json_pointer(root, schema_ref)
        # we actually need the parent of the schema object, so we remove the last segment
        ptr = ptr.rsplit("/", 1)[0]
        schema_references_collected.add('#' + ptr)
        schema_format = schema_format.lower().split("/")[0]
        schema_obj = schema_ref
        schema_ref = '#' + ptr

    if schema_format.startswith("avro"):
        if isinstance(schema_obj, dict) and "type" in schema_obj and schema_obj["type"] == "record":
            ref = ''
            if "namespace" in schema_obj:
                ref = str(schema_obj["namespace"]) + \
                    "." + str(schema_obj["name"])
            else:
                ref = str(schema_obj["name"])
            # if a class_name had been given, it must match
            if class_name:
                if ref != class_name:
                    raise RuntimeError(
                        "Avro: Class name reference mismatch for top-level record object: " + ref + " != " + class_name)
            return project_name + '.' + ref
        elif isinstance(schema_obj, list):
            if not class_name:
                raise RuntimeError(
                    "Avro: Explicit class name reference (':{classname}' suffix) required for Avro schema with top-level union: ")
            for record in schema_obj:
                if isinstance(record, dict) and "type" in record and record["type"] == "record":
                    ref = ''
                    if "namespace" in record:
                        ref = str(record["namespace"]) + \
                            "." + str(record["name"])
                    else:
                        ref = str(record["name"])
                    # if a class_name had been given, it must match
                    if ref == class_name:
                        return project_name + '.' + ref
        raise RuntimeError(
            "Avro: Top-level record object not found in Avro schema: ")
    elif schema_format.startswith("proto"):
        if isinstance(schema_obj, str):
            # namespace is the last segment of the schema URL
            if class_name:
                # find the top-level message object in the proto schema using regex
                local_class_name = strip_namespace(class_name)
                match = re.search(r"message[\s]+([\w]+)[\s]*{", schema_obj)
                if local_class_name and match:
                    for g in match.groups():
                        if g.lower() == local_class_name.lower():
                            return project_name + '.' + class_name
                if match and match.groups() and len(match.groups()) == 1:
                    class_name = namespace_dot(class_name) + match.groups()[0]
                    return project_name + '.' + class_name
                else:
                    raise RuntimeError(
                        f"Proto: Top-level message {class_name} not found in Proto schema")
            else:
                match = re.search(r"message[\s]+([\w]+)[\s]*{", schema_obj)
                if match:
                    # if we have more than 1 match, we cannot determine the class name
                    if len(match.groups()) > 1:
                        raise RuntimeError(
                            "Proto: Multiple top-level message objects found in Proto schema: ")
                    return project_name + '.' + match.group(1)
                else:
                    raise RuntimeError(
                        "Proto: Top-level message object not found in Proto schema: ")
        raise RuntimeError(
            "Proto: Top-level message object not found in Proto schema: ")
    else:
        if class_name:
            return project_name + '.' + class_name
        # otherwise return the last element of the fragment	unless the penultimate
        # segment name is "versions". Then return the parent segment of
        # versions.
        path_elements = schema_ref.split('/')
        if path_elements[-2] == "versions":
            return path_elements[-3]
        else:
            return path_elements[-1]


def schema_object(root: dict, schema_url: str):
    """ Returns the object in the document that the schema URL points to """
    try:
        obj = jsonpointer.resolve_pointer(root, schema_url[1:].split(":")[0])
    except jsonpointer.JsonPointerException:
        return None
    return obj


def latest_dict_entry(dict: dict):
    """ Returns the dictionary entry with the last key """
    # find the length m of the longest key in the dictionary
    # left justify each key with spaces to length m to make a list in which all keys have same length
    # then sort the keys and trim them
    # return the dictionary entry with the last key
    m = max([len(k) for k in dict.keys()])
    return dict[sorted([k.ljust(m) for k in dict.keys()])[-1].strip()]


def concat_namespace(namespace: str, class_name: str):
    """ Concatenates a namespace and a class name """
    if namespace:
        return namespace + "." + class_name
    return class_name


def generate(project_name: str, language: str, style: str, output_dir: str,
             definitions_file_arg: str, headers: dict, template_dirs: list, template_args: dict,
             suppress_code_output: bool, suppress_schema_output: bool):
    """ 
    The core generator function that drives the Jinja templates 

    Args:
        project_name: the name of the project
        language: the language to generate code for
        style: the style of code to generate
        output_dir: the directory to write the generated code to
        definitions_file_arg: the path to the definitions file
        headers: a dictionary of headers to use when resolving references
        template_dirs: a list of directories to search for templates
        template_args: a dictionary of arguments to pass to the templates
        suppress_code_output: if True, do not output generated code. This will still run through all templates and collect schema references
        suppress_schema_output: if True, do not output generated schemas
    """

    global schema_references_collected

    # Load definitions
    definitions_file, docroot = load_definitions(
        definitions_file_arg, headers, style == "schema")
    if not definitions_file or not docroot:
        raise RuntimeError(
            "definitions file not found or invalid {}".format(definitions_file_arg))

    # Load templates
    pt = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
    code_template_dir = os.path.join(pt, "templates", language, style)
    code_template_dirs = [code_template_dir]  # without includes
    code_template_and_include_dirs = [code_template_dir, os.path.join(
        pt, "templates", language, "_common")]  # with includes
    schema_template_dirs = [os.path.join(
        pt, "templates", language, "_schemas")]

    for template_dir in template_dirs if template_dirs else []:
        template_dir = os.path.join(os.path.curdir, template_dir)
        if not os.path.isdir(template_dir):
            raise RuntimeError(
                "template directory not found {}".format(template_dir))
        # if a template directory exists for the language and style, override the default
        code_template_dir = os.path.join(template_dir, language, style)
        if os.path.exists(code_template_dir) and os.path.isdir(code_template_dir):
            code_template_dirs = [code_template_dir]  # without includes
            code_template_and_include_dirs = [code_template_dir, os.path.join(
                pt, "templates", language, "_common")]  # with includes
            schema_template_dirs = [os.path.join(
                pt, "templates", language, "_schemas")]
            # first found wins
            break

    code_env = setup_jinja_env(code_template_and_include_dirs)
    schema_env = setup_jinja_env(schema_template_dirs)
    render_code_templates(project_name, style, output_dir, docroot,
                          code_template_dirs, code_env, False, template_args, suppress_code_output)
    render_code_templates(project_name, style, output_dir, docroot,
                          schema_template_dirs, schema_env, False, template_args, suppress_schema_output)

    # now we need to handle any local schema references we found in the document
    # we redo the overall loop until we have handled all the schema references
    # check whether there are references in schema_references_collected
    # that are not in   handled
    while not schema_references_collected.issubset(get_schemas_handled()):
        # we need to iterate over a copy of the set because we may add to it
        for schema_reference in set(schema_references_collected):
            if schema_reference not in get_schemas_handled():
                add_schema_to_handled(schema_reference)
                set_current_url(None)
                schema_format = None
                class_name = ''
                schema_format_short = ''

                # split off a suffix reference with ':'
                if ":" in schema_reference:
                    schema_reference, class_name = schema_reference.split(":")

                # if the scheme reference is a JSON Pointer reference, we resolve it
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
                        match = jsonpointer.resolve_pointer(
                            docroot, schema_reference[1:])
                        if not match:
                            continue
                        schema_root = match
                    except jsonpointer.JsonPointerException as e:
                        print("Error resolving JSON Pointer: " + str(e))
                        continue
                else:
                    type_ref = ''
                    if '#' in schema_reference:
                        schema_reference, type_ref = schema_reference.split(
                            "#")
                    schema_reference, docroot = load_definitions(
                        schema_reference, headers, True)
                    if type_ref:
                        try:
                            match = jsonpointer.resolve_pointer(
                                docroot, type_ref)
                            if not match:
                                continue
                            schema_root = match
                        except jsonpointer.JsonPointerException as e:
                            print("Error resolving JSON Pointer: " + str(e))
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
                        parent = jsonpointer.resolve_pointer(
                            docroot, parent_reference[1:])
                        if parent and isinstance(parent, dict):
                            prefix = parent.get("id", '')
                            if not class_name.startswith(prefix):
                                class_name = prefix + '.' + class_name
                        versions = schema_root["versions"]
                        if not isinstance(versions, dict):
                            raise RuntimeError(
                                "Schema versions not found: " + schema_reference if schema_reference else '')
                        max_key_length = max([len(key)
                                             for key in versions.keys()])
                        sorted_keys = sorted(
                            versions.keys(), key=lambda key: key.rjust(max_key_length))
                        schema_version = versions[sorted_keys[-1]]
                    elif "schema" in schema_root or "schemaurl" in schema_root or "schema" in schema_root:
                        # the reference pointed to a schema version definition
                        schema_version = schema_root
                        parent_reference = schema_reference.rsplit("/", 1)[0]
                        parent = jsonpointer.resolve_pointer(
                            docroot, parent_reference[1:])
                        if parent and isinstance(parent, dict) and not class_name:
                            class_name = parent.get("id", class_name)
                        parent_reference = parent_reference.rsplit("/", 2)[0]
                        parent = jsonpointer.resolve_pointer(
                            docroot, parent_reference[1:])
                        if parent and isinstance(parent, dict):
                            prefix = parent.get("id", '')
                            if not class_name.startswith(prefix):
                                class_name = prefix + '.' + class_name

                    if schema_version and isinstance(schema_version, dict):
                        schema_format = ''
                        if "schemaformat" in schema_version:
                            schema_format = schema_version["schemaformat"]
                        elif "format" in schema_version:
                            schema_format = schema_version["format"]

                        if not schema_format:
                            raise RuntimeError(
                                "Schema format not found: " + schema_reference if schema_reference else '')

                        # case c): if the schema version contains a schemaurl attribute, then we need to
                        # add the schemaurl to the list of schemas to be processed and continue
                        if "schemaurl" in schema_version:
                            schema_url = schema_version["schemaurl"]
                            if schema_url not in schema_files_collected:
                                schema_files_collected.add(schema_url)
                            continue
                        elif "schema" in schema_version or "schema" in schema_version:
                            # case b): the schema version does not contain a schemaurl attribute, so we
                            # assume that the schema is inline and we can proceed to render it
                            if "schema" in schema_version:
                                schema_root = schema_version["schema"]
                            else:
                                schema_root = schema_version["schema"]

                            set_current_url(schema_reference)
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
                        if is_proto_doc(schema_root):
                            schema_format_short = 'proto'
                            schema_format = 'proto3'
                            schema_root = schema_root
                        else:
                            raise RuntimeError(
                                "Schema format not found: " + schema_reference if schema_reference else '')

                    if not isinstance(schema_reference, str):
                        raise RuntimeError(
                            "Schema reference not found: " + schema_reference if schema_reference else '')

                    if language in ["py", "cs", "java", "js", "ts"] and schema_format_short != "proto":
                        if schema_format_short == "json" and isinstance(schema_root, dict) or isinstance(schema_root, list):
                            schema_root = convert_jsons_to_avro(schema_reference, schema_root, namespace_name=namespace(class_name if class_name else ''), class_name=pascal(strip_namespace(class_name)))
                            schema_format_short = "avro"
                        avro_enabled = template_args.get("avro-encoding", "false")=="true"
                        json_enabled = template_args.get("json-encoding", "true")=="true"
                        if language == "py":
                            avrotize.convert_avro_schema_to_python(
                                schema_root, output_dir, package_name=project_name, dataclasses_json_annotation=json_enabled, avro_annotation=avro_enabled)
                        elif language == "cs":
                            avrotize.convert_avro_schema_to_csharp(schema_root, output_dir, base_namespace=pascal(
                                project_name), pascal_properties=True, system_text_json_annotation=json_enabled, avro_annotation=avro_enabled)
                        elif language == "java":
                            avrotize.convert_avro_schema_to_java(
                                schema_root, output_dir, package_name=project_name, jackson_annotation=json_enabled, avro_annotation=avro_enabled)
                        elif language == "js":
                            avrotize.convert_avro_schema_to_javascript(
                                schema_root, output_dir, package_name=project_name, avro_annotation=avro_enabled)
                        elif language == "ts":
                            avrotize.convert_avro_schema_to_typescript(
                                schema_root, output_dir, package_name=project_name, avro_annotation=avro_enabled, typedjson_annotation=json_enabled)
                    else:
                        render_schema_templates(schema_format_short, project_name, class_name, language,
                                                output_dir, definitions_file, schema_root, schema_template_dirs, schema_env, template_args, suppress_schema_output)
                    continue
                else:
                    print("Warning: unable to find schema reference " +
                          schema_reference if schema_reference else '')

    render_code_templates(project_name, style, output_dir, docroot,
                          code_template_dirs, code_env, True, template_args, suppress_code_output)

    # reset the references collected in this file
    schema_references_collected = set()

    if style == "schema":
        render_schema_templates(None, project_name, None, language,
                                output_dir, definitions_file, docroot, schema_template_dirs, schema_env, template_args, suppress_schema_output)


def convert_proto_to_avro(schema_reference: str, schema_root: str):
    """ Convert a proto schema to an Avro schema. """
    if schema_reference.startswith("#"):
        proto_file = tempfile.NamedTemporaryFile(delete=False, suffix=".proto")
        try:
            avro_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".avsc")
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


def convert_jsons_to_avro(schema_reference: str, schema_root: JsonNode, namespace_name: str = '', class_name: str = ''):
    """ Convert a JSON schema to an Avro schema. """
    if schema_reference.startswith("#"):
        jsons_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jsons")
        try:
            avro_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".avsc")
            try:
                jsons_file.write(json.dumps(schema_root).encode('utf-8'))
                jsons_file.close()
                avrotize.convert_jsons_to_avro(
                    jsons_file.name, avro_file.name, namespace=namespace_name, root_class_name=class_name)
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
                schema_reference, avro_file.name, namespace=namespace_name)
            schema_root = json.loads(avro_file.read())
        finally:
            avro_file.close()
            os.unlink(avro_file.name)
    return schema_root


def render_code_templates(project_name: str, style: str, output_dir: str, docroot: JsonNode,
                          code_template_dirs: list, env: jinja2.Environment, post_process: bool, template_args: dict, suppress_output: bool = False):
    """ 

    Render code templates.

    for templates, except in _schemas, the filename may lead (!) with the following patterns
        {projectname} is replaced by the project name
        {classname} is replaced by the name of the generated class
        {classfull} is replaced by the qualified name of the generated class
        {classdir} is replaced by a directory name that reflects the
                namespace/package name plus {classname}
    the {class*} patterns break the input information set up such that the
    generator is fed just one CloudEvent definition but the information set
    remains anchored at "messagegroups"

    """

    if not isinstance(docroot, dict):
        raise RuntimeError("Document root is not a dictionary")
    class_name = None
    for template_dir in code_template_dirs:
        for root, dirs, files in os.walk(template_dir):
            relpath = os.path.relpath(root, template_dir).replace("\\", "/")
            if relpath == ".":
                relpath = ""

            for file in files:
                if not file.endswith(".jinja") or (not post_process and file.startswith("_")) or (post_process and not file.startswith("_")):
                    continue

                template_path = relpath + "/" + file
                # all codegen for CE is anchored on the included messagegroups
                scope = docroot
                class_name = ''

                file_dir = file_dir_base = os.path.join(
                    output_dir, os.path.join(*relpath.split("/")))
                # strip the jinja suffix
                file_name_base = file[:-6]
                if post_process:
                    file_name_base = file_name_base[1:]

                try:
                    template = env.get_template(template_path)
                except TemplateAssertionError as err:
                    print(f"{err.name} ({err.lineno}): {err}")
                    exit(1)
                except TemplateSyntaxError as err:
                    print(f"{err.name}: ({err.lineno}): {err}")
                    exit(1)

                file_name_base = file_name_base.replace("{projectname}",
                                                        pascal(project_name))
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
                            raise RuntimeError(
                                "messagegroups is not a dictionary")
                        for id, definitiongroup in group_dict.items():
                            # create a snippet that only has the current definitiongroup
                            subscope: JsonNode = {
                                "endpoints": endpoints,
                                "schemagroups": schemagroups,
                                "messagegroups": {
                                    f"{id}": definitiongroup
                                }
                            }
                            class_name = id
                            scope_parts = id.split(".")
                            class_package_name = scope_parts[-1]
                            package_name = id
                            if not package_name:
                                package_name = project_name
                            elif not package_name.startswith(project_name):
                                package_name = project_name + "." + package_name
                            if not class_package_name:
                                raise RuntimeError("class name not found")
                            if file_name_base.find("{classdir}") > -1:
                                file_dir = os.path.join(file_dir_base,
                                                        os.path.join(*package_name.split("."))).lower()
                                file_name = file_name_base.replace(
                                    "{classdir}", pascal(class_package_name))
                                class_name = f'{package_name}.{file_name.split(".")[0]}'
                            else:
                                file_name = file_name_base.replace(
                                    "{classfull}", id).replace("{classname}", pascal(class_package_name))
                            if not class_name:
                                raise RuntimeError("class name not found")
                            render_template(project_name, class_name, subscope, file_dir,
                                            file_name, template, template_args, suppress_output)
                    continue  # skip back to the outer loop

                if file_name.startswith("{projectdir}"):
                    file_dir = os.path.join(file_dir_base, os.path.join(
                        *project_name.split("."))).lower()
                    file_name = file_name_base.replace("{projectdir}", "")

                render_template(project_name, class_name, scope, file_dir,
                                file_name, template, template_args, suppress_output)


def is_proto_doc(docroot: JsonNode) -> bool:
    """ Check if the document is a proto document. """
    return isinstance(docroot, str) and re.search(r"syntax[\s]*=[\s]*\"proto3\"", docroot) is not None


def render_schema_templates(schema_type: str | None, project_name: str, class_name: str | None, language: str,
                            output_dir: str, definitions_file: str, docroot: JsonNode, schema_template_dirs: list, env: jinja2.Environment,
                            template_args: dict, suppress_output: bool = False):
    global uses_protobuf
    global uses_avro

    scope = docroot
    if schema_type is None:
        if is_proto_doc(docroot):
            schema_type = "proto"
        elif isinstance(docroot, dict) and "type" in docroot and docroot["type"] == "record":
            schema_type = "avro"
        else:
            schema_type = "json"

    if schema_type == "proto":
        uses_protobuf = True
        if isinstance(docroot, str) and is_proto_doc(docroot):
            # find the specific message we are looking for in the proto file
            local_class_name = strip_namespace(class_name)
            match = re.search(r"message[\s]+([\w]+)[\s]*{", docroot)
            found = False
            if local_class_name and match:
                for g in match.groups():
                    if g.lower() == local_class_name.lower():
                        class_name = namespace_dot(class_name) + g
                        found = True
                        break
            if not found and match and match.groups() and len(match.groups()) == 1:
                class_name = namespace_dot(class_name) + match.groups()[0]
            elif not found:
                raise RuntimeError(
                    f"Proto: Top-level message {class_name} not found in Proto schema")
    elif schema_type == "avro":
        uses_avro = True
        if isinstance(docroot, dict) and "type" in docroot and docroot["type"] == "record":
            class_name = concat_namespace(
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
                    class_name = concat_namespace(
                        str(record.get("namespace", "")), str(record["name"]))
                    break
            raise RuntimeError(
                "Avro: Top-level record object not found in Avro schema: ")

    file_dir = file_dir_base = output_dir
    if class_name is None:
        class_name = os.path.basename(definitions_file).split(".")[0]
    for template_dir in schema_template_dirs:
        schema_files = glob.glob(
            f"**/_{schema_type}.*.jinja", root_dir=template_dir, recursive=True)
        for schema_file in schema_files:
            # we needed to add the template_dir to the path for glob,
            # but strip it back out here since we operate on the plain name
            schema_file = schema_file.replace("\\", "/")
            try:
                template = env.get_template(schema_file)
            except Exception as err:
                print(err)
                exit(1)

            relpath = os.path.dirname(schema_file)
            if relpath == ".":
                relpath = ""
            schema_file = os.path.basename(schema_file)
            file_name_base = schema_file[len(schema_type) + 2:][:-6]
            file_dir = os.path.join(
                file_dir_base, os.path.join(*relpath.split("/")))

            # if the file name is just the language indicator,
            # eg. "cs", take the filename of the schema doc
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
                    "{classdir}", pascal(class_package_name))

            # remember the schema class name we generated a file for
            if not class_name in stack("classfiles"):
                push(class_name, "classfiles")

            # generate the file
            render_template(project_name, class_name, scope, file_dir,
                            file_name, template, template_args, suppress_output)


def render_template(project_name: str, class_name: str, scope: JsonNode, file_dir: str, file_name: str, template: Template, template_args: dict, suppress_output: bool = False):
    """ Renders a Jinja template to a file """

    global uses_protobuf
    global uses_avro
    global current_dir

    try:
        output_path = os.path.join(os.getcwd(), file_dir, file_name)

        if not suppress_output and not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        try:
            current_dir = os.path.dirname(output_path)
            args = template_args.copy() if template_args is not None else {}
            args["root"] = scope
            args["project_name"] = project_name
            args["class_name"] = class_name
            args["uses_avro"] = uses_avro
            args["uses_protobuf"] = uses_protobuf
            rendered = template.render(args)
            if not suppress_output:
                with open(output_path, "w", encoding='utf-8') as f:
                    f.write(rendered)
        except TypeError as err:
            # this is the result of the exit tag in the template
            if err.args[0].find("Undefined found") > -1:
                if not suppress_output and os.path.exists(output_path):
                    os.remove(output_path)
            else:
                print(f"{template.name}: {err}")
                exit(1)
    except TemplateNotFound as err:
        print(f"{template.name}: Include file not found: {err}")
        exit(1)
    except TemplateRuntimeError as err:
        print(err)
        exit(1)

# creates the Jinja environment and loads the extensions


def setup_jinja_env(template_dirs: list[str]):
    loader = jinja2.FileSystemLoader(template_dirs, followlinks=True)
    env = jinja2.Environment(loader=loader, extensions=[
                             ExitExtension, UuidExtension, TimeExtension])
    env.filters['regex_search'] = regex_search
    env.filters['regex_replace'] = regex_replace
    env.filters['pascal'] = pascal
    env.filters['snake'] = snake
    env.filters['strip_namespace'] = strip_namespace
    env.filters['namespace'] = namespace
    env.filters['namespace_dot'] = namespace_dot
    env.filters['strip_dots'] = strip_dots
    env.filters['schema_type'] = schema_type
    env.filters['camel'] = camel
    env.filters['strip_invalid_identifier_characters'] = strip_invalid_identifier_characters
    env.filters['pad'] = pad
    env.filters['toyaml'] = toyaml
    env.filters['proto'] = proto
    env.filters['exists'] = exists
    env.filters['existswithout'] = existswithout
    env.filters['push'] = push
    env.filters['pushfile'] = pushfile
    env.filters['save'] = save
    env.globals['pop'] = pop
    env.globals['stack'] = stack
    env.globals['get'] = get
    env.globals['schema_object'] = schema_object
    env.globals['latest_dict_entry'] = latest_dict_entry
    env.globals['geturlhost'] = geturlhost
    env.globals['geturlpath'] = geturlpath
    env.globals['geturlport'] = geturlport
    env.globals['geturlscheme'] = geturlscheme
    return env


def generate_code(args) -> int:
    suppress_schema_output = args.no_schema
    suppress_code_output = args.no_code

    if args.headers:
        # ok to have = in base64 values
        headers = {
            header.split("=", 1)[0]: header.split("=", 1)[1]
            for header in args.headers
        }
    else:
        headers = {}

    template_args = {}
    if args.template_args:
        for arg in args.template_args:
            key, value = arg.split("=", 1)
            template_args[key] = value

    # initialize globals
    global schema_files_collected
    global schema_references_collected
    global uses_avro
    global uses_protobuf
    global context_stacks

    # ok, what? why is this a loop?
    # if uses_avro or uses_protobuf are set in the first run, we need to run the loop a second time
    for _ in range(0, 2):

        schema_files_collected = set()
        reset_schemas_handled()
        schema_references_collected = set()
        set_current_url(None)
        context_stacks = dict()

        try:
            # Call the generate() function with the parsed arguments
            if validate(args.definitions_file, headers, False) != 0:
                return 1

            generate(args.project_name, args.language, args.style, args.output_dir,
                     args.definitions_file, headers, args.template_dirs, template_args, suppress_code_output, suppress_schema_output)

            # generate external schemas
            for schema in schema_files_collected:
                generate(args.project_name, args.language, "schema", args.output_dir,  schema, headers,
                         args.template_dirs, template_args, suppress_code_output, suppress_schema_output)

            if stack("files"):
                for file, content in stack("files"):
                    with open(file, "w", encoding='utf-8') as f:
                        f.write(content)

            if not uses_avro and not uses_protobuf:
                break
        except SystemExit:
            return 1
        # pylint: disable=broad-exception-caught
        except Exception as err:
            print(err)
            raise err # re-raise the exception
    return 0
