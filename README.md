# CloudEvent Generator
This project generates CloudEvent sender and receiver code from a given CloudEvent definitions file.

## Installation
Install the script

```
pip install git+https://github.com/clemensv/cedisco-codegen.git
```

(Mind that the templates need to be exist on the local disk right now, in the "templates" directory where the script is run. That requirement will go away)

## Usage
To generate code, run the following command:

```
cloudeventscg --language <language> --style <style> --output <output directory> --definitions <definitions file or URI>
```

where language is the programming language to generate code for (e.g. python, csharp, java), style is the output style (e.g. azurefunctions, awslambda, proxy), output is the directory to write the generated code to, and definitions is the path to the CloudEvent definitions file or the URI to the definitions file.

## Templates
Templates for code generation are stored in the templates directory. The directory structure is as follows:

```
templates/
├── <language>/
│   └── <style>/
│       ├── <template>.jinja
│       ├── <template>.jinja
│       ├── ...
│       └── <template>.jinja
├── <language>/
│   └── <style>/
│       ├── <template>.jinja
│       ├── <template>.jinja
│       ├── ...
│       └── <template>.jinja
└── ...
```

The template files have the same name as the target file, with the .jinja extension.
