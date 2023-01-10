# CloudEvents Discovery Code Generator

This (experimental, rapidly evolving) project generates CloudEvent sender and
receiver code from a given CloudEvent discovery event definitions service
endpoint or file.

> THE GENERATED CODE ISN'T EXPECTED TO WORK YET. 
> CURRENT DEV FOCUS IS THE CODEGEN INFRA

It can currently generate CloudEvents HTTP client proxies for Python, Java, and
C# and Azure Functions handlers in C# for Azure Service Bus, Azure Event Grid,
Azure Event Hubs, and HTTP triggers.

Embedded is also a class generator for JSON using the same infra that is driven
by the needs of the discovered message/event definition sets. 

## Installation

To try this out, install the script

```
pip install git+https://github.com/clemensv/cedisco-codegen.git
```

You will then need a working CloudEvents discovery endpoint, which are still
hard to come by or you need a set of CloudEvent Discovery documents. 

There's currently one sample doc at [samples/cloudevents-discovery/Microsoft.Storage.disco](samples/cloudevents-discovery/Microsoft.Storage.disco) which you can point to with the --definitions option.

```
cedisco_codegen --language cs --definitions samples/cloudevents-discovery/Microsoft.Storage.disco --projectname MyServiceBusHandler --output ~/demos/grid --style azfunctioneventgrid
```

> Mind that this document's root will still shift and > the templates will adjust accordingly.

## Usage
To generate code, run the following command:

```
cedisco_codegen --projectname <projectname> --language <language> --style <style> --output <output directory> --definitions <definitions file or URI>
```

where language is the programming language to generate code for (e.g. python,
csharp, java), style is the output style (e.g. azurefunctions, awslambda,
proxy), output is the directory to write the generated code to, and definitions
is the path to the CloudEvent definitions file or the URI to the definitions
file.

## Templates

Templates for code generation are stored in the templates directory. The
directory structure is as follows:

```
templates/
├── <language>/
│   └── <style>/
│       ├── <template>.jinja
│       ├── ...
│       └── <template>.jinja
├── <language>/
│   └── <style>/
│       ├── <template>.jinja
│       ├── ...
│       └── <template>.jinja
└── ...
```

The template files have the same name as the target file, with the .jinja
extension. There are a few expansion macros for the file names.

The Jinja2 template has been extended with a few code-gen specific extensions
available in the core Python script.
