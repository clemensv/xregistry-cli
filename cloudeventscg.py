import os
import json
import jinja2
import urllib.request
import re
import argparse
import urllib.parse
import glob

# The current_url represents that last file that has been
# loaded in the current process and is currently being handled
# this is used to resolve relative URLs in found URL references
current_url = None


# Jinja filter to perform a regex search. Returns the found string.
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
    if not string:
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


# Jina filter that strips the namespace/package portion off
# an expression. Assumes dot-notation, e.g. namespace.class
def strip_namespace(class_reference):
    return re.sub(r'^.+\.', '', class_reference)

# Jina filter that concats the namespace/package portions of
# an expression, removing the dots. 
def concat_namespace(class_reference):
    return "".join(class_reference.split("."))


# Jina filter that determines the type name of an expression
# given a schema URL, specifically in CloudEvents' dataschema
# attribute. Schema URLs are collected by the filter as a side
# effect and then given to the generator
schemas = set()


def schema_type(schema_url: str):
    global schemas
    global current_url

    if schema_url.startswith("#"):
        return schema_url.split("/")[-1]

    if current_url:
        schema_url = urllib.parse.urljoin(current_url, schema_url)

    parsed_url = urllib.parse.urlparse(schema_url)
    if parsed_url.fragment:
        fragment = parsed_url.fragment
        path_elements = fragment.split('/')
        plain_url = urllib.parse.urlunparse(parsed_url._replace(fragment=''))
        if plain_url not in schemas:
            schemas.add(schema_url)
        return path_elements[-1]
    else:
        if schema_url not in schemas:
            schemas.add(schema_url)
        match = re.search(r"/schemas/([\.\w]+)$", schema_url)
        if match:
            return match.group(1)
    return "object"


# the core generator function that drives the Jinja templates
schemas_handled = set()


def generate(project_name: str, language: str, style: str, output_dir: str,
             definitions_file: str, headers: dict):
    global current_url

    # Load definitions
    definitions_file, docroot = load_definitions(definitions_file, style,
                                                 headers)
    if not definitions_file:
        return

    # Load templates
    pt = os.path.dirname(os.path.realpath(__file__))
    if style == "schema":
        template_dir = os.path.join(pt, "templates", language, "_schemas")
    else:
        template_dir = os.path.join(pt, "templates", language, style)

    env = setup_jinja_env(template_dir)
    render_code_templates(project_name, style, output_dir, docroot,
                          template_dir, env)
    if style == "schema":
        render_schema_templates("json", template_dir, project_name, language,
                                output_dir, definitions_file, docroot, env)


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

    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if not file.endswith(".jinja") or file.startswith("_"):
                continue

            template_path = file
            scope = docroot
            file_dir = file_dir_base = output_dir
            ## strip the jinja suffix
            file_name_base = file[:-6]
            template = env.get_template(template_path)
            file_name_base = file_name_base.replace("{projectname}", pascal(project_name))
            file_name = file_name_base
            if file_name.startswith("{class"):
                for id, group in scope.items():
                    subscope = {}
                    subscope[id] = group
                    scope_parts = id.split(".")
                    package_name = id
                    if not package_name:
                        package_name = project_name
                    class_name = scope_parts[-1]
                    if file_name_base.startswith("{classdir}"):
                        file_dir = os.path.join(file_dir_base,
                                                package_name.replace(".", "/"))
                        file_name = file_name_base.replace("{classdir}", pascal(class_name))
                    else:
                        file_name = file_name_base.replace("{classfull}", id).replace("{classname}", pascal(class_name))
                    render_template(project_name, subscope, file_dir, file_name, template)
                continue  # skip back to the outer loop

            render_template(project_name, scope, file_dir, file_name, template)


def render_schema_templates(schema_type, template_dir, project_name, language,
                            output_dir, definitions_file, docroot, env):
    scope = docroot
    file_dir = file_dir_base = output_dir
    schema_files = glob.glob(
        os.path.join(template_dir, "_{schema_type}.*.jinja".format(schema_type=schema_type)))
    for schema_file in schema_files:
        # we needed to add the template_dir to the path for glob, 
        # but strip it back out here since we operate on teh plain name
        schema_file = os.path.basename(schema_file)
        template = env.get_template(schema_file)
        file_name_base = schema_file[len(schema_type) + 2:][:-6]
        # if the file name is just the language indicator, 
        # eg. "cs", take the filename of the schema doc
        if file_name_base == language:
            file_name_base = os.path.basename(definitions_file).split(".")[0] + "." + language
        file_name_base = file_name_base.replace("{projectname}", pascal(project_name))
        file_name = file_name_base
        if file_name_base.startswith("{class"):
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
                    file_name = file_name_base.replace("{classdir}", pascal(class_name))
                else:
                    file_name = file_name_base.replace("{classfull}", id).replace(
                        "{classname}", pascal(class_name))
                render_template(project_name, subscope, file_dir, file_name,
                                template)
            continue  # skip back to the outer loop

        render_template(project_name, scope, file_dir, file_name, template)


def render_template(project_name, scope, file_dir, file_name, template):
    output_path = os.path.join(os.getcwd(), file_dir, file_name)

    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    with open(output_path, "w") as f:
        f.write(template.render(root=scope, project_name=project_name))


# Load the definition file, which may be a JSON Schema
# or CloudEvents message group definition. Since URLs
# found in documents may be redirected by their hosts,
# the function returns the actual URL as the first return
# value and the parsed object representing the document's
# information set
def load_definitions(definitions_file: str, style: str, headers: dict):
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

    # for a CloudEvents message definition group, we
    # normalize the document to be a groups doc
    if style != "schema" and 'id' in docroot:
        new_root = {}
        new_root[docroot['id']] = docroot
        docroot = new_root

    return definitions_file, docroot


# creates the Jinja environment and loads the extensions
def setup_jinja_env(template_dir):
    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader)
    env.filters['regex_search'] = regex_search
    env.filters['regex_replace'] = regex_replace
    env.filters['pascal'] = pascal
    env.filters['snake'] = snake
    env.filters['strip_namespace'] = strip_namespace
    env.filters['concat_namespace'] = concat_namespace
    env.filters['schema_type'] = schema_type
    env.filters['camel_case'] = camel_case
    env.filters['csharp_identifier'] = csharp_identifier
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

    # Call the generate() function with the parsed arguments
    generate(args.project_name, args.language, args.style, args.output_dir,
             args.definitions_file, headers)

    for schema in schemas:
        generate(args.project_name, args.language, "schema", args.output_dir,
                 schema, headers)


if __name__ == "__main__":
    main()