import os
import json
import yaml
import jinja2
import urllib.request
import re
import argparse
import urllib.parse
import glob
import jsonpointer
from jinja2 import nodes
from jinja2.ext import Extension


# Jinja tag to exit the current template because
# something went wrong
class ExitException(Exception):
    pass


class ExitExtension(Extension):
    tags = set(['exit'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        return nodes.CallBlock(self.call_method('_exit', []), [], [],
                               []).set_lineno(lineno)

    def _exit(self, name, timeout, caller):
        raise ExitException("¯\_(ツ)_/¯")


# The current_url represents that last file that has been
# loaded in the current process and is currently being handled
# this is used to resolve relative URLs in found URL references
current_url = None


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
def csharp_identifier(string):
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
def camel_case(string):
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
    camel_case = words[0].lower()
    for word in words[1:]:
        camel_case += word.capitalize()
    return camel_case

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
def namespace(class_reference):
    if class_reference:
        return re.sub(r'\.[^.]+$', '', class_reference)
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

# Jinja filter that determines the type name of an expression
# given a schema URL, specifically in CloudEvents' dataschema
# attribute. Schema URLs are collected by the filter as a side
# effect and then given to the generator
schema_files_collected = set()
schema_references_collected = set()

def schema_type(schema_url: str):
    global schema_files_collected
    global current_url
    global schema_references_collected

    # if the schema URL is a fragment, then it is a local reference
    if schema_url.startswith("#"):
        if not schema_url in schema_references_collected:
            schema_references_collected.add(schema_url)
        # return the last element of the fragment unless the penultimate
        # segment name is "versions". Then return the parent segment of
        # versions.
        path_elements = schema_url.split('/')
        if path_elements[-2] == "versions":
            return path_elements[-3]
        else:
            return path_elements[-1]

    if current_url:
        schema_url = urllib.parse.urljoin(current_url, schema_url)

    parsed_url = urllib.parse.urlparse(schema_url)
    if parsed_url.fragment:
        fragment = parsed_url.fragment
        path_elements = fragment.split('/')
        plain_url = urllib.parse.urlunparse(parsed_url._replace(fragment=''))
        # if the URL is not already in the list of schemas, add it
        if plain_url not in schema_files_collected:
            schema_files_collected.add(schema_url)
        return path_elements[-1]
    else:
        if schema_url not in schema_files_collected:
            schema_files_collected.add(schema_url)
        match = re.search(r"/schemas/([\.\w]+)$", schema_url)
        if match:
            return match.group(1)
    return "object"


# the core generator function that drives the Jinja templates
schemas_handled = set()


def generate(project_name: str, language: str, style: str, output_dir: str,
             definitions_file: str, headers: dict):
    global current_url
    global schema_references_collected

    # Load definitions
    definitions_file, docroot = load_definitions(definitions_file, style,
                                                 headers)
    if not definitions_file:
        return

    # Load templates
    pt = os.path.dirname(os.path.realpath(__file__))
    schema_template_dir = os.path.join(pt, "templates", language, "_schemas")
    code_template_dir = os.path.join(pt, "templates", language, style)

    code_env = setup_jinja_env(code_template_dir)
    schema_env = setup_jinja_env(schema_template_dir)
    render_code_templates(project_name, style, output_dir, docroot,
                          code_template_dir, code_env)
    
    # now we need to handle any local schema references we found in the document
 
    # we redo the overall loop until we have handled all the schema references
    # check whether there are references in schema_references_collected 
    # that are not in schemas_handled
    while not schema_references_collected.issubset(schemas_handled):
         # we need to iterate over a copy of the set because we may add to it
        for schema_reference in set(schema_references_collected):
            if schema_reference not in schemas_handled:
                schemas_handled.add(schema_reference)
                current_url = None

                # if the scheme reference is a JSON Pointer reference, we resolve it
                # to an object in the document. Remove a leading # if present
                if schema_reference.startswith("#"):
                    path_elements = schema_reference.split('/')
                    if path_elements[-2] == "versions":
                        definitions_file = path_elements[-3]
                    else:
                        definitions_file = path_elements[-1]

                    try:
                        match = jsonpointer.resolve_pointer(docroot, schema_reference[1:])
                        if not match:
                            continue
                        schema_root = match
                    except jsonpointer.JsonPointerException as e:
                        print("Error resolving JSON Pointer: " + str(e))
                        continue

                if schema_root:
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

                    if schema_version:
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
                            current_url = schema_reference
                            render_schema_templates("json", schema_template_dir, project_name, language,
                                                    output_dir, definitions_file, schema_root, schema_env)
                            continue
                        else:
                            print("Warning: unable to find schema reference " + schema_reference)

                    else:
                        # case a): the reference pointed to an inline schema in the message definition
                        render_schema_templates("json", schema_template_dir, project_name, language,
                                                    output_dir, definitions_file, schema_root, schema_env)
                        continue

                    render_schema_templates("json", schema_template_dir, project_name, language,
                                            output_dir, definitions_file, schema_root, schema_env)
                else:
                    print("Warning: unable to find schema reference " + schema_reference)
            
    # reset the references collected in this file 
    schema_references_collected = set()

    if style == "schema":
        render_schema_templates("json", schema_template_dir, project_name, language,
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
def render_code_templates(project_name, style, output_dir, docroot,
                          template_dir, env):
    class_name = None
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if not file.endswith(".jinja") or file.startswith("_"):
                continue

            template_path = file
            # all codegen for CE is anchored on the included groups
            scope = docroot

            file_dir = file_dir_base = output_dir
            ## strip the jinja suffix
            file_name_base = file[:-6]
            template = env.get_template(template_path)
            file_name_base = file_name_base.replace("{projectname}",
                                                    pascal(project_name))
            file_name = file_name_base
            if file_name.startswith("{class") and "groups" in scope:

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
                    if file_name_base.startswith("{classdir}"):
                        file_dir = os.path.join(file_dir_base,
                                                package_name.replace(".", "/"))
                        file_name = file_name_base.replace(
                            "{classdir}", pascal(class_name))
                    else:
                        file_name = file_name_base.replace(
                            "{classfull}", id).replace("{classname}",
                                                       pascal(class_name))
                    render_template(project_name, class_name, subscope, file_dir,
                                    file_name, template)
                continue  # skip back to the outer loop

            render_template(project_name, class_name, scope, file_dir, file_name, template)


def render_schema_templates(schema_type, template_dir, project_name, language,
                            output_dir, definitions_file, docroot, env):
    scope = docroot
    file_dir = file_dir_base = output_dir
    class_name = os.path.basename(definitions_file).split(".")[0]
    schema_files = glob.glob(
        os.path.join(template_dir,
                     "_{schema_type}.*.jinja".format(schema_type=schema_type)))
    for schema_file in schema_files:
        # we needed to add the template_dir to the path for glob,
        # but strip it back out here since we operate on teh plain name
        schema_file = os.path.basename(schema_file)
        template = env.get_template(schema_file)
        file_name_base = schema_file[len(schema_type) + 2:][:-6]
       
        # if the file name is just the language indicator,
        # eg. "cs", take the filename of the schema doc
        if file_name_base == language:
            file_name_base = pascal(class_name) + "." + language
        file_name_base = file_name_base.replace("{projectname}",
                                                pascal(project_name))
        file_name = file_name_base
        if file_name_base.startswith("{class"):
            if "definitions" in scope:
                for id, definition in scope['definitions'].items():
                    subscope = {"definitions": {}}
                    subscope['definitions'][id] = definition
                    scope_parts = id.split(".")
                    package_name = ".".join(scope_parts[:-1])
                    if not package_name:
                        package_name = project_name
                    class_name = scope_parts[-1]
                    if file_name_base.startswith("{classdir}"):
                        file_dir = os.path.join(file_dir_base,
                                                package_name.replace(".", "/"))
                        file_name = file_name_base.replace(
                            "{classdir}", pascal(class_name))
                    else:
                        file_name = file_name_base.replace(
                            "{classfull}", id).replace("{classname}",
                                                       pascal(class_name))
                    render_template(project_name, class_name, subscope, file_dir,
                                    file_name, template)
            continue  # skip back to the outer loop

        render_template(project_name, class_name, scope, file_dir, file_name, template)


def render_template(project_name, class_name, scope, file_dir, file_name, template):
    try:
        output_path = os.path.join(os.getcwd(), file_dir, file_name)

        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))

        try:
            with open(output_path, "w") as f:
                f.write(template.render(root=scope, project_name=project_name, class_name=class_name))
        except ExitException:
            os.remove(output_path)
    except Exception as err:
        print(err)
        exit(1)


# Load the definition file, which may be a JSON Schema
# or CloudEvents message group definition. Since URLs
# found in documents may be redirected by their hosts,
# the function returns the actual URL as the first return
# value and the parsed object representing the document's
# information set
def load_definitions_core(definitions_file: str, style: str, headers: dict):
    docroot: dict = {}
    global current_url
    try:
        if definitions_file.startswith("http"):
            req = urllib.request.Request(definitions_file, headers=headers)
            with urllib.request.urlopen(req) as url:
                # URIs may redirect and we only want to handle each file once
                current_url = url.url
                parsed_url = urllib.parse.urlparse(url.url)
                definitions_file = urllib.parse.urlunparse(
                    parsed_url._replace(fragment=''))
                if definitions_file not in schemas_handled:
                    schemas_handled.add(definitions_file)
                else:
                    return None, None
                docroot = json.loads(url.read().decode())
        else:
            if definitions_file not in schemas_handled:
                schemas_handled.add(definitions_file)
            else:
                return None, None
            with open(os.path.join(os.getcwd(), definitions_file), "r") as f:
                docroot = json.loads(f.read())
    except urllib.error.URLError as e:
        print("An error occurred while trying to open the URL: ", e)
        return None, None
    except json.decoder.JSONDecodeError as e:
        print("An error occurred while trying to parse the JSON file: ", e)
        return None, None
    except IOError as e:
        print("An error occurred while trying to access the file: ", e)
        return None, None

    return definitions_file, docroot


def load_definitions(definitions_file: str, style: str, headers: dict):
    # for a CloudEvents message definition group, we
    # normalize the document to be a groups doc
    definitions_file, docroot = load_definitions_core(definitions_file, style,
                                                      headers)

    if style == "schema":
        return definitions_file, docroot

    if "$schema" in docroot:
        if docroot["$schema"] != "https://cloudevents.io/schemas/discovery":
            print("unsupported schema:" + docroot["$schema"])
            return None, None
    if "groupsUrl" in docroot:
        _, subroot = load_definitions_core(docroot["groupsUrl"], style,
                                           headers)
        docroot["groups"] = subroot
        docroot["groupsUrl"] = None
    if "schemagroupsUrl" in docroot:
        _, subroot = load_definitions_core(docroot["schemagroupsUrl"], style,
                                           headers)
        docroot["schemagroups"] = subroot
        docroot["schemagroupsUrl"] = None
    if "endpointsUrl" in docroot:
        _, subroot = load_definitions_core(docroot["endpointsUrl"], style,
                                           headers)
        docroot["endpoints"] = subroot
        docroot["endpointsUrl"] = None

    # make sure the document is always of the same form, even if
    # the URL was a deep link. We can drill to the level of an
    # endpoint, a group, or a schemagroup
    newroot = {"$schema": "https://cloudevents.io/schemas/discovery"}

    # the doc is an dict
    if isinstance(docroot, dict) and "type" in docroot[list(
            docroot.keys())[0]]:
        dictentry = docroot[list(docroot.keys())[0]]
        if dictentry["type"] == "group":
            newroot["groups"] = docroot
        elif dictentry["type"] == "schemagroup":
            newroot["schemagroups"] = docroot
        elif dictentry["type"] == "endpoint":
            newroot["endpoints"] = docroot
        else:
            print("unknown doc structure")
            return None, None
        docroot = newroot

    # the doc is an object
    elif "type" in docroot:
        if docroot["type"] == "group":
            newroot["groups"] = {docroot["id"]: docroot}
        elif docroot["type"] == "schemagroup":
            newroot["schemagroups"] = {docroot["id"]: docroot}
        elif docroot["type"] == "endpoints":
            newroot["endpoints"] = {docroot["id"]: docroot}
        else:
            print("unknown type:" + docroot["type"])
            return None, None
        docroot = newroot

    return definitions_file, docroot


# creates the Jinja environment and loads the extensions
def setup_jinja_env(template_dir):
    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader, extensions=[ExitExtension])
    env.filters['regex_search'] = regex_search
    env.filters['regex_replace'] = regex_replace
    env.filters['pascal'] = pascal
    env.filters['snake'] = snake
    env.filters['strip_namespace'] = strip_namespace
    env.filters['namespace'] = namespace
    env.filters['concat_namespace'] = concat_namespace
    env.filters['schema_type'] = schema_type
    env.filters['camel_case'] = camel_case
    env.filters['csharp_identifier'] = csharp_identifier
    env.filters['pad'] = pad
    env.filters['toyaml'] = toyaml
    return env


def main():
   
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Specify the arguments
    parser.add_argument(
        "--projectname",
        dest="project_name",
        required=True,
        help="The project name (namespace name) for the output")
    parser.add_argument("--language",
                        dest="language",
                        required=True,
                        help="The language to use for the generated code")
    parser.add_argument("--style",
                        dest="style",
                        required=True,
                        help="The style of the generated code")
    parser.add_argument(
        "--output",
        dest="output_dir",
        required=True,
        help="The directory where the generated code should be saved")
    parser.add_argument("--definitions",
                        dest="definitions_file",
                        required=True,
                        help="The file or URL containing the definitions")
    parser.add_argument("--requestheaders",
                        nargs="*",
                        dest="headers",
                        required=False,
                        help="Extra HTTP headers in the format 'key=value'")

    # Parse the command line arguments
    args = parser.parse_args()

    if args.headers:
        # ok to have = in base64 values
        headers = {
            header.split("=", 1)[0]: header.split("=", 1)[1]
            for header in args.headers
        }
    else:
        headers = {}

    # initialize globals
    global schemas_handled
    global schema_files_collected
    global schema_references_collected
    global current_url

    schema_files_collected = set()
    schemas_handled = set()
    schema_references_collected = set()
    current_url = None

    # Call the generate() function with the parsed arguments
    generate(args.project_name, args.language, args.style, args.output_dir,
             args.definitions_file, headers)

    # generate external schemas
    for schema in schema_files_collected:
        generate(args.project_name, args.language, "schema", args.output_dir,
                 schema, headers)
    


if __name__ == "__main__":
    main()
