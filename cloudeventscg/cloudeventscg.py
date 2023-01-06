import os
import json
import jinja2
import urllib.request
import re

def regex_search(string, pattern):
    if string:
        match = re.findall(pattern, string)
        if match:
            return match
    return []

def generate(language: str, style: str, output_dir: str, definitions_file: str):
    # Load definitions
    if definitions_file.startswith("http"):
        with urllib.request.urlopen(definitions_file) as url:
            groups = json.loads(url.read().decode())
    else:
        with open(definitions_file, "r") as f:
            groups = json.loads(f.read())

    # Load templates
    template_dir = os.path.join("templates", language, style)
    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader)
    env.filters['regex_search'] = regex_search

    # Render templates
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if not file.endswith(".jinja"):
                continue

            template_path = file
            template = env.get_template(template_path)
            output_path = os.path.join(output_dir, file[:-6])

            if not os.path.exists(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))

            with open(output_path, "w") as f:
                f.write(template.render(groups=groups, project_name="MyProject"))

if __name__ == "__main__":
    generate("python", "proxy", "tmp", "https://cediscoveryinterop.azurewebsites.net/registry/groups?code=")