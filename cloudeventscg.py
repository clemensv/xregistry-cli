import os
import json
import jinja2
import urllib.request
import re
import argparse
import urllib.parse

current_url = None

def regex_search(string, pattern):
    if string:
        match = re.findall(pattern, string)
        if match:
            return match
    return []

def csharp_identifier(string):
   if string:
       return re.sub("[^A-Za-z0-9_]", "_", string)
   return string 

def pascal(string):
    if not string:
        return string
    words = []
    if '_' in string:
        # snake_case
        words = re.split(r'_', string)
    elif string[0].isupper():
        # PascalCase
        words = re.findall(r'[A-Z][^A-Z]*', string)
    else:
        # camelCase
        words = re.findall(r'[a-z]+|[A-Z][^A-Z]*', string)
    return ''.join(word.capitalize() for word in words)

def camel_case(string):
    if not string:
        return string
    if '_' in string:
        # snake_case
        words = re.split(r'_', string)
    elif string[0].isupper():
        # PascalCase
        words = re.findall(r'[A-Z][^A-Z]*', string)
    else:
        # default case: return string as-is
        return string
    camel_case = words[0].lower()
    for word in words[1:]:
        camel_case += word.capitalize()
    return camel_case

def strip_namespace(class_reference):
    return re.sub(r'^.+\.', '', class_reference)

schemas = set()

def schema_type(schema_url : str):
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
     match = re.search(r"/schemas/([\.\w]+)$",schema_url)
     if match:
        return match.group(1)     
   return "object"  

schemas_handled = set()

def generate(project_name : str, language: str, style: str, output_dir: str, definitions_file: str, headers : dict):
    global current_url

    # Load definitions
    if definitions_file.startswith("http"):
        req = urllib.request.Request(definitions_file, headers=headers)
        with urllib.request.urlopen(req) as url:
            # URIs may redirect and we only want to handle each file once
            current_url = url.url
            parsed_url = urllib.parse.urlparse(url.url)
            definitions_file = urllib.parse.urlunparse(parsed_url._replace(fragment=''))
            if definitions_file not in schemas_handled:   
                schemas_handled.add(definitions_file)
            else:
               return
            docroot = json.loads(url.read().decode())
    else:
        with open(os.path.join(os.getcwd(), definitions_file), "r") as f:
            docroot = json.loads(f.read())
    
    # if we get just one group, wrap it as it if were a groups doc
    if style != "schema" and 'id' in docroot:
        new_root = {}
        new_root[docroot['id']] = docroot
        docroot = new_root

    # Load templates
    pt = os.path.dirname(os.path.realpath(__file__))
    if style == "schema":
        template_dir = os.path.join(pt, "templates", language, "_schemas")
    else:
        template_dir = os.path.join(pt, "templates", language, style)

    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader)
    env.filters['regex_search'] = regex_search
    env.filters['pascal'] = pascal
    env.filters['strip_namespace'] = strip_namespace
    env.filters['schema_type'] = schema_type
    env.filters['camel_case'] = camel_case
    env.filters['csharp_identifier'] = csharp_identifier
    
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if not file.endswith(".jinja") or file.startswith("_"):
                continue

            template_path = file
            template = env.get_template(template_path)
            output_path = os.path.join(os.getcwd(), output_dir, file[:-6].replace("{projectname}", project_name))

            if not os.path.exists(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))

            with open(output_path, "w") as f:
                f.write(template.render(groups=docroot, project_name=project_name))
    
    if style == "schema":
        template = env.get_template("_json.jinja")
        output_path = os.path.join(os.getcwd(), output_dir, os.path.basename(definitions_file).split(".")[0] + "." + language)
      
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        
        with open(output_path, "w") as f:
            f.write(template.render(schema=docroot, project_name=project_name))
    
def main():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Specify the arguments
    parser.add_argument("--projectname", dest="project_name", required=True, help="The project name (namespace name) for the output")
    parser.add_argument("--language", dest="language", required=True, help="The language to use for the generated code")
    parser.add_argument("--style", dest="style", required=True, help="The style of the generated code")
    parser.add_argument("--output", dest="output_dir", required=True, help="The directory where the generated code should be saved")
    parser.add_argument("--definitions", dest="definitions_file", required=True, help="The file or URL containing the definitions")
    parser.add_argument("--requestheaders", nargs="*", dest="headers", required=False, help="Extra HTTP headers in the format 'key=value'")

    # Parse the command line arguments
    args = parser.parse_args()

    # ok to have = in base64 values 
    headers = {header.split("=", 1)[0]: header.split("=", 1)[1] for header in args.headers}

    # Call the generate() function with the parsed arguments
    generate(args.project_name, args.language, args.style, args.output_dir, args.definitions_file, headers)

    for schema in schemas:
        generate(args.project_name,args.language, "schema", args.output_dir, schema, headers)

if __name__ == "__main__":
    main()