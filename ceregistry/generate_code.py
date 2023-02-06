import datetime
import os
import json
import uuid
import yaml
import jinja2
import urllib.request
import re
import argparse
import urllib.parse
import glob
import jsonpointer
import pandas as pd

from jinja2 import nodes
from jinja2.ext import Extension
from jinja2 import TemplateAssertionError, TemplateSyntaxError, TemplateRuntimeError

from .validate_definitions import validate
from .core import *

# These are the global variables that are switched 
# to True when a schema is found that uses Avro or Protobuf,
# respectively. When either of these is True, the generator
# will run a second time for the output to consistently include
# Avro and/or Protobuf dependencies
uses_avro : bool = False
uses_protobuf : bool = False


# Create a global stack structure
context_stacks = dict()
context_dict = dict()

# Jinja extension to push a value onto a named stack
def push(value, stack_name):
    global context_stacks
    if stack_name not in context_stacks:
        context_stacks[stack_name] = list()
    context_stacks[stack_name].append(value)
    return ""

current_dir = ""

def pushfile(value, name):
    global context_stacks
    if "files" not in context_stacks:
        context_stacks["files"] = list()
    context_stacks["files"].append((os.path.join(current_dir,name), value))
    return ""

# Jinja extension to pop a value from a named stack
def pop(stack_name):
    global context_stacks
    if stack_name not in context_stacks:
        context_stacks[stack_name] = list()
    return context_stacks[stack_name].pop()

# Jinja extension to get the full contents of a named stack
def stack(stack_name):
    global context_stacks
    if stack_name not in context_stacks:
        context_stacks[stack_name] = list()
    return context_stacks[stack_name]

# Jinja extension to set a value
def save(value, prop_name):
    global context_dict
    context_dict[prop_name] = value
    return value

# Jinja extension to get a value
def get(prop_name):
    global context_dict
    if prop_name in context_dict:
        return context_dict[prop_name]
    return ""



# Jinja tag to exit the current template because
# something went wrong
class ExitExtension(Extension):
    tags = set(['exit'])

    def parse(self, parser):
        lineno = next(parser.stream)        
        return nodes.CallBlock(self.call_method('_exit', []), [], [],
                               []).set_lineno(lineno)

    def _exit(self, caller):
        raise StopIteration()

class UuidExtension(Extension):
    tags = { 'uuid'}

    def parse(self, parser) -> nodes.Output:
        lineno = parser.stream.expect("name:uuid").lineno
        context = nodes.ContextReference()
        result = self.call_method("_render", [context], lineno=lineno)
        return nodes.Output([result], lineno=lineno)

    def _render(self, context) -> str:
        return uuid.uuid4()

class TimeExtension(Extension):
    tags = { 'time'}

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
    df = pd.json_normalize(obj)
    result = df[df.filter(like=prop).applymap(lambda x: x.lower()).apply(lambda x: x.str.startswith(value))].any().any()
    return result


# Jinja filter to perform a regex search. Returns a list of matches.
def regex_search(string, pattern):
    if string:
        match = re.findall(pattern, string)
        if match:
            return match
    return []


# Jinja filter to perform a regex search. Returns the found string.
def regex_replace(string, pattern, replacement):
    if string:
        return re.sub(pattern, replacement, string)
    return string


# Jinja filter to replace all characters that are not valid
# in C# identifiers with an underscore
def strip_invalid_identifier_characters(string):
    if string:
        return re.sub("[^A-Za-z0-9_\.]", "_", string)
    return string


# Jinja filter that turns a string expression into PascalCase
# The input can be snake_case or camelCase or any other string
def pascal(string):
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
        words = re.findall(r'[a-z]+\.?|[A-Z][a-z0-9_]*\.?', string)
    result = ''.join(word.capitalize() for word in words)
    return result


#Jinja filter that turns a string expression into snake_case
#The input can be PascalCase, camelCase, snake_case, or any other text


def snake(string):
    if not string:
        return string
    result = re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()
    return result


# Jinja filter that turns a string expression into camelCase
# The input can be snake_case or PascalCase or any other string
def camel(string):
    if not string:
        return string
    if '_' in string:
        # snake_case
        words = re.split(r'_', string)
    elif string[0].isupper():
        # PascalCase
        words = re.findall(r'[A-Z][^A-Z]*\.?', string)
    else:
        # default case: return string as-is
        return string
    camel = words[0].lower()
    for word in words[1:]:
        camel += word.capitalize()
    return camel

# Jinja filter that left-justified pads a string with spaces
# to the specified length
def pad(string, length):
    if string:
        return string.ljust(length)
    return string


# Jinja filter that strips the namespace/package portion off
# an expression. Assumes dot-notation, e.g. namespace.class
def strip_namespace(class_reference):
    if class_reference:
        return re.sub(r'^.+\.', '', class_reference)
    return class_reference

# Jinja filter that gets the namespace/package portion off
# an expression. Assumes dot-notation, e.g. namespace.class
def namespace(class_reference, namespace_prefix=""):
    if class_reference:
        ns = re.sub(r'\.[^.]+$', '', class_reference)
        if namespace_prefix:
            if ns.startswith(namespace_prefix):
                return ns
            if namespace_prefix.startswith(ns):
                return namespace_prefix
            else:
                return namespace_prefix + "." + ns
        else:
            return ns
    return class_reference

# Jinja filter that concats the namespace/package portions of
# an expression, removing the dots.
def concat_namespace(class_reference):
    if class_reference:
        return "".join(class_reference.split("."))
    return class_reference

# Jinja filter that formats the given object as YAML
def toyaml(obj : any, indent : int = 4):
    return yaml.dump(obj, default_flow_style=False, indent=indent)

def proto(proto_text : str):
    # Add newlines after ';'
    proto_text = re.sub(r"([;{}])", r"\1\n", proto_text)

     # Indent all lines after '{' or '}'
    indent = 0
    lines = proto_text.split("\n")
    for i in range(len(lines)):
        line = re.sub(r"^\s*", "", lines[i])
        if "}" in line: indent -= 1
        lines[i] = "    "*indent + line
        if "{" in line: indent += 1
           
    proto_text = "\n".join(lines)

    # Remove extra newlines
    proto_text = re.sub(r"\n{3,}", "\n\n", proto_text)

    return proto_text

# Jinja filter that determines the type name of an expression
# given a schema URL, specifically in CloudEvents' dataschema
# attribute. Schema URLs are collected by the filter as a side
# effect and then given to the generator
schema_files_collected = set()
schema_references_collected = set()

def schema_type(schema_url: str):
    global schema_files_collected
    global schema_references_collected

    # if the schema URL is a fragment, then it is a local reference
    if schema_url.startswith("#"):
        if not schema_url in schema_references_collected:
            schema_references_collected.add(schema_url)
        
        # if the fragment ends with ":{type}" return that type
        # otherwise return the last element of the fragment	unless the penultimate
        # segment name is "versions". Then return the parent segment of
        # versions. 

        # handle the case where the fragment is "#/definitions/anything:{type}"
        if ":" in schema_url:
            return schema_url.split(":")[-1]        

        path_elements = schema_url.split('/')
        if path_elements[-2] == "versions":
            return path_elements[-3]
        else:
            return path_elements[-1]

    if get_current_url():
        schema_url = urllib.parse.urljoin(get_current_url(), schema_url)

    parsed_url = urllib.parse.urlparse(schema_url)
    if parsed_url.fragment:
        fragment = parsed_url.fragment
        path_elements = fragment.split('/')
        plain_url = urllib.parse.urlunparse(parsed_url._replace(fragment=''))
        # if the URL is not already in the list of schemas, add it
        if plain_url not in schema_files_collected:
            schema_files_collected.add(schema_url)
        # if the fragment ends with ":{type}" return that type
        # otherwise return the last element of the fragment
        if ":" in fragment:
            return fragment.split(":")[-1]
        elif path_elements[-2] == "versions":
            return path_elements[-3]        
        return path_elements[-1]
    else:
        if schema_url not in schema_files_collected:
            schema_files_collected.add(schema_url)
        match = re.search(r"/schemas/([\.\w]+)$", schema_url)
        if match:
            return match.group(1)
    return "object"

def schema_object(root: dict, schema_url: str):
    try:
        obj = jsonpointer.resolve_pointer(root, schema_url[1:].split(":")[0])
    except jsonpointer.JsonPointerException:
        return None
    return obj

def latest_dict_entry(dict: dict):
   # find the length m of the longest key in the dictionary
   # left justify each key with spaces to length m to make a list in which all keys have same length 
   # then sort the keys and trim them
   # return the dictionary entry with the last key
    m = max([len(k) for k in dict.keys()])
    return dict[sorted([k.ljust(m) for k in dict.keys()])[-1].strip()] 

# the core generator function that drives the Jinja templates
def generate(project_name: str, language: str, style: str, output_dir: str,
             definitions_file_arg: str, headers: dict, template_dirs: list, template_args: dict):
    global schema_references_collected
    
    # Load definitions
    definitions_file, docroot = load_definitions(definitions_file_arg, headers, style == "schema")
    if not definitions_file:
        raise RuntimeError("definitions file not found or invalid {}".format(definitions_file_arg))

    # Load templates
    pt = os.path.dirname(os.path.realpath(__file__))
    schema_template_dir = os.path.join(pt, "templates", language, "_schemas")
    code_template_dir = os.path.join(pt, "templates", language, style)
    code_include_dir = os.path.join(pt, "templates", language, "_common")

    code_env = setup_jinja_env([code_template_dir, code_include_dir])
    schema_env = setup_jinja_env([schema_template_dir])
    render_code_templates(project_name, style, output_dir, docroot,
                          code_template_dir, code_env, False, template_dirs, template_args)
    render_code_templates(project_name, style, output_dir, docroot,
                          schema_template_dir, schema_env, False, template_dirs, template_args)
    
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
                class_name = None

                # if the scheme reference is a JSON Pointer reference, we resolve it
                # to an object in the document. Remove a leading # if present
                if schema_reference.startswith("#"):
                    # split off a suffix reference with ':'
                    if ":" in schema_reference:
                        schema_reference, class_name = schema_reference.split(":")

                    path_elements = schema_reference.split('/')
                    if path_elements[-2] == "versions":
                        definitions_file = path_elements[-3]
                    else:
                        definitions_file = path_elements[-1]

                    if class_name is None:
                        class_name = definitions_file

                    try:
                        match = jsonpointer.resolve_pointer(docroot, schema_reference[1:])
                        if not match:
                            continue
                        schema_root = match
                    except jsonpointer.JsonPointerException as e:
                        print("Error resolving JSON Pointer: " + str(e))
                        continue
  
                if schema_root and isinstance(schema_root,dict):
                    # now we need to figure out what the reference points to. 
                    # a) This could be an inline schema inside a message definition
                    # b) This could be an inline schema inside a schema definition
                    # c) This could yet be a schema definition in a separate file referenced 
                    #    by the schemaUrl attribute inside a schema version referenced by
                    #    the local reference 

                    schema_version = None
                    if "type" in schema_root and schema_root["type"] == "schema" and "versions" in schema_root:
                        # the reference pointed to a schema definition. Now we need to find the
                        # most recent version in the versions dictionary by sorting the keys
                        # and picking the last one. To sort the keys, we need to make them the same length 
                        # by prepending spaces to the keys that are shorter than the longest key
                        versions = schema_root["versions"]
                        max_key_length = max([len(key) for key in versions.keys()])
                        sorted_keys = sorted(versions.keys(), key=lambda key: key.rjust(max_key_length))
                        schema_version = versions[sorted_keys[-1]]
                    elif "type" in schema_root and schema_root["type"] == "schemaversion":
                        # the reference pointed to a schema version definition
                        schema_version = schema_root

                    if schema_version and isinstance(schema_version,dict):
                        if "schemaformat" in schema_version:
                            schema_format = schema_version["schemaformat"]

                        # case c): if the schema version contains a schemaUrl attribute, then we need to
                        # add the schemaUrl to the list of schemas to be processed and continue
                        if "schemaUrl" in schema_version:
                            schema_url = schema_version["schemaUrl"]
                            if schema_url not in schema_files_collected:
                                schema_files_collected.add(schema_url)
                            continue
                        elif "schema" in schema_version:
                            # case b): the schema version does not contain a schemaUrl attribute, so we
                            # assume that the schema is inline and we can proceed to render it
                            schema_root = schema_version["schema"]
                            set_current_url (schema_reference)
                            schema_format_short = None

                            if "format" in schema_version:
                                format_string = schema_version["format"].lower()
                                if format_string.startswith("proto"):
                                    schema_format_short = "proto"
                                elif format_string.startswith("json"):
                                    schema_format_short = "json"
                                elif format_string.startswith("avro"):
                                    schema_format_short = "avro"
                            
                            render_schema_templates(schema_format_short, schema_template_dir, project_name, class_name, language,
                                                    output_dir, definitions_file, schema_root, schema_env, template_dirs, template_args)
                            continue
                        else:
                            print("Warning: unable to find schema reference " + schema_reference)

                    # schema_root is not a schema version or schema definition, so it is a schema      
                    schema_format_short = None 
                    if schema_format is not None and schema_format.lower().startswith("proto"):
                        schema_format_short = "proto"
                    elif schema_format is not None and schema_format.lower().startswith("avro"):
                        schema_format_short = "avro"
                    else:
                        schema_format_short = "json"
                                               
                    render_schema_templates(schema_format_short, schema_template_dir, project_name, class_name, language,
                                                output_dir, definitions_file, schema_root, schema_env, template_dirs, template_args)
                else:
                    print("Warning: unable to find schema reference " + schema_reference)
            
    render_code_templates(project_name, style, output_dir, docroot,
                          code_template_dir, code_env, True, template_dirs, template_args)
    
    
    # reset the references collected in this file 
    schema_references_collected = set()

    if style == "schema":
        render_schema_templates(None, schema_template_dir, project_name, None, language,
                                output_dir, definitions_file, docroot, schema_env)


# for templates, except in _schemas, the filename may lead (!) with the
# following patterns
# {projectname} is replaced by the project name
# {classname} is replaced by the name of the generated class
# {classfull} is replaced by the qualified name of the generated class
# {classdir} is replaced by a directory name that reflects the
#            namespace/package name plus {classname}
# the {class*} patterns break the input information set up such that the
# generator is fed just one CloudEvent definition but the information set
# remains anchored at "groups"
def render_code_templates(project_name : str, style : str, output_dir : str, docroot : dict,
                          template_dir : str, env : jinja2.Environment, post_process : bool, 
                          template_dirs : list, template_args : dict):
    class_name = None
    for root, dirs, files in os.walk(template_dir):
        relpath = os.path.relpath(root, template_dir).replace("\\", "/")
        if relpath == ".":
            relpath = ""

        for file in files:
            if not file.endswith(".jinja") or (not post_process and file.startswith("_")) or (post_process and not file.startswith("_")):
                continue

            template_path = relpath + "/" + file  
            # all codegen for CE is anchored on the included groups
            scope = docroot

            file_dir = file_dir_base = os.path.join(output_dir, os.path.join(*relpath.split("/")))
            ## strip the jinja suffix
            file_name_base = file[:-6]
            if post_process:
                file_name_base = file_name_base[1:]

            try:
                template = env.get_template(template_path)
            except TemplateAssertionError as err:
                print("{file} ({lineno}): {msg}".format(file=err.name, lineno=err.lineno, msg=err))
                exit(1)
            except TemplateSyntaxError as err:
                print("{file}: ({lineno}): {msg}".format(file=err.name, lineno=err.lineno, msg=err))
                exit(1)
            
            file_name_base = file_name_base.replace("{projectname}",
                                                    pascal(project_name))
            file_name = file_name_base
            if file_name.startswith("{class"):
                if "groups" in scope:
                    if "endpoints" in docroot: endpoints = docroot["endpoints"]
                    else: endpoints = None
                    if "schemagroups" in docroot:
                        schemagroups = docroot["schemagroups"]
                    else:
                        schemagroups = None

                    for id, group in scope["groups"].items():
                        # create a snippet that only has the current group
                        subscope = {
                            "endpoints": endpoints,
                            "schemagroups": schemagroups,
                            "groups": {}
                        }
                        subscope["groups"][id] = group
                        scope_parts = id.split(".")
                        package_name = id
                        if not package_name:
                            package_name = project_name
                        class_name = scope_parts[-1]
                        if file_name_base.find("{classdir}") > -1:
                            file_dir = os.path.join(file_dir_base, 
                                                    os.path.join(*package_name.split("."))).lower()
                            file_name = file_name_base.replace("{classdir}", pascal(class_name))
                        else:
                            file_name = file_name_base.replace(
                                "{classfull}", id).replace("{classname}",
                                                        pascal(class_name))
                        render_template(project_name, class_name, subscope, file_dir,
                                        file_name, template, template_args)
                continue  # skip back to the outer loop

            if file_name.startswith("{projectdir}"):
                file_dir = os.path.join(file_dir_base, os.path.join(*package_name.split("."))).lower()
                file_name = file_name_base.replace("{projectdir}", "")

            
            render_template(project_name, class_name, scope, file_dir, file_name, template, template_args)


def render_schema_templates(schema_type : str, template_dir : str, project_name : str, class_name : str, language : str,
                            output_dir : str, definitions_file : str, docroot : dict, env : jinja2.Environment,
                            template_dirs : list, template_args : dict):
    global uses_protobuf
    global uses_avro
    
    scope = docroot
    if schema_type is None:
        if isinstance(docroot,str) and re.search(r"syntax[\s]*=[\s]*\"proto3\"", docroot):
            schema_type = "proto"
        elif isinstance(docroot,dict) and "type" in docroot and docroot["type"] == "record":
            schema_type = "avro"
        else:
            schema_type = "json"

    if schema_type == "proto":
        uses_protobuf = True
    if schema_type == "avro":
        uses_avro = True

    file_dir = file_dir_base = output_dir
    if class_name is None:
        class_name = os.path.basename(definitions_file).split(".")[0]
    schema_files = glob.glob("**/_{schema_type}.*.jinja".format(schema_type=schema_type), root_dir=template_dir, recursive=True)
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
        file_dir = os.path.join(file_dir_base, os.path.join(*relpath.split("/")))
       
        # if the file name is just the language indicator,
        # eg. "cs", take the filename of the schema doc
        if file_name_base == language or file_name_base == "proto" or file_name_base == "avsc":
            file_name_base = pascal(class_name) + "." + file_name_base
        file_name_base = file_name_base.replace("{projectname}",
                                                pascal(project_name))
        file_name_base = file_name_base.replace("{classname}",
                                                pascal(class_name))
        
        file_name = file_name_base
        if file_name_base.find("{classdir}") > -1:
            file_dir = os.path.join(file_dir, os.path.join(*project_name.split(".")).lower())
            file_name = file_name_base.replace("{classdir}", pascal(class_name))
                
        
        # remember the schema class name we generated a file for 
        if not class_name in stack("classfiles"):
            push(class_name, "classfiles")
        
        
        # generate the file
        render_template(project_name, class_name, scope, file_dir, file_name, template, template_args)


def render_template(project_name : str, class_name : str, scope : dict, file_dir : str, file_name : str, template : str, template_args : dict):

    global uses_protobuf
    global uses_avro
    global current_dir
    
    try:
        output_path = os.path.join(os.getcwd(), file_dir, file_name)

        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))

        try:
            current_dir = os.path.dirname(output_path)
            args = template_args.copy() if template_args is not None else {}
            args["root"]=scope
            args["project_name"]=project_name
            args["class_name"]=class_name
            args["uses_avro"]=uses_avro
            args["uses_protobuf"]=uses_protobuf
            rendered = template.render(args)
            with open(output_path, "w") as f:
                f.write(rendered)
        except TypeError as err:
            # this is the result of the exit tag in the template
            if err.args[0].find("Undefined found") > -1:
                if ( os.path.exists(output_path) ):
                    os.remove(output_path)
            else:
                print("{file}: {msg}".format(file=template.name, msg=err))
                exit(1)
            
    except TemplateRuntimeError as err:
        print(err)
        exit(1)




# creates the Jinja environment and loads the extensions
def setup_jinja_env(template_dirs : list[str]):
    loader = jinja2.FileSystemLoader(template_dirs, followlinks=True)
    env = jinja2.Environment(loader=loader, extensions=[ExitExtension, UuidExtension, TimeExtension])
    env.filters['regex_search'] = regex_search
    env.filters['regex_replace'] = regex_replace
    env.filters['pascal'] = pascal
    env.filters['snake'] = snake
    env.filters['strip_namespace'] = strip_namespace
    env.filters['namespace'] = namespace
    env.filters['concat_namespace'] = concat_namespace
    env.filters['schema_type'] = schema_type
    env.filters['camel'] = camel
    env.filters['strip_invalid_identifier_characters'] = strip_invalid_identifier_characters
    env.filters['pad'] = pad
    env.filters['toyaml'] = toyaml
    env.filters['proto'] = proto
    env.filters['exists'] = exists
    env.filters['push'] = push
    env.filters['pushfile'] = pushfile
    env.filters['save'] = save
    env.globals['pop'] = pop
    env.globals['stack'] = stack
    env.globals['get'] = get
    env.globals['schema_object'] = schema_object
    env.globals['latest_dict_entry'] = latest_dict_entry
    return env


def generate_code(args) -> int:
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
    for int in range(0, 2):

        schema_files_collected = set()
        reset_schemas_handled()
        schema_references_collected = set()
        set_current_url(None)
        context_stacks = dict()

        try:
            # Call the generate() function with the parsed arguments
            if validate(args.definitions_file, headers) != 0:
                return 1
            
            generate(args.project_name, args.language, args.style, args.output_dir,
                    args.definitions_file, headers, args.template_dirs, template_args)

            # generate external schemas
            for schema in schema_files_collected:
                generate(args.project_name, args.language, "schema", args.output_dir,
                        schema, headers, args.template_dirs, template_args)
            
            if stack("files"):
                for file, content in stack("files"):
                    with open(file, "w") as f:
                        f.write(content)

            if not uses_avro and not uses_protobuf:
                break
        except SystemExit as err:
            return int(err.code)
        except Exception as err:
            print(err)
            return 1
        
    return 0
