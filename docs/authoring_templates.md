# Authoring templates

Output of the code generator is driven by a set of templates that are stored in
the tool package's internal `templates` directory and are installed with the
tool.

Template authors write text files that are processed by the template engine. You
don't have to write any extensions or plugins to use the template engine. The
template language, which is an extension of the
[Jinja2](https://jinja.palletsprojects.com/en/3.0.x/templates/) template
language, is built into the tool and has a set of extensions specific to code
generation that cover even fairly complicated scenarios.

Custom templates can be provided by the user by creating a directory that has
the same structure as this templates directory and passing the path to the
`--templates` command line argument. Any templates found in the user-provided
directory will override the corresponding _language_ and _style_ of the built-in
templates and you can add new languages and styles.

The generator distinguishes between templates for endpoints and message
definition groups (those are the _styles_) and templates that generate code for
message payload schemas.

Templates for payload schemas are shared across any set of templates for a given
language. You can handle JSON Schema, Avro Schema, and Proto files explicitly at
the moment.

In the case of JSON Schema, the template is meant to generates classes for the
JSON Schema types. For serializer frameworks like Avro and Proto, the template
is expected to generate input files for the serializer framework's native
code-generators and add auxiliary files if needed.

## Directory structure

The content of the the `templates` directory is dynamic and extensible.

The common structure looks like this:

```text
templates
├── {language}
│   ├── _templateinfo.json
│   ├── _schemas[/subdir]
│   │   ├── _avro.{language}.jinja
│   │   ├── _json.{language}.jinja
│   │   └── _proto.proto.jinja
│   ├── _common
│   │   ├── amqp.jinja.include
│   │   ├── cloudevents.jinja.include
│   │   └── mqtt.jinja.include
│   ├── {style}[/subdir]
│   │   ├── _templateinfo.json
│   │   ├── {template}.jinja
│   │   └── ...
│   └── ...
└── ...
```

In a templates directory reside subdirectories for each of the supported output
languages. Adding support for a new language is as simple as adding a new
directory with a unique name. That name should correspond to the common file
name suffix for the language, e.g. if you were adding support for C++ you would
name the directory `cpp`.

The tool uses the name of the directory as the language identifier for the
`--language` command line argument. The language identifier is also used to find
the correct templates for automatic generation of schema serializer code as
shown in the illustration above.

Under each language directory, there are subdirectories for each template set.
Template sets are called "styles" to avoid conflations with other overloaded
terms. The tool uses the name of the subdirectory as the style identifier for
the `--style` command line argument.

The `_schemas` directory is special-cased and contains templates for generating
code for serializaing or otherwise handling message payload schemas. The
templates may reside in a subdirectory and that subdirectory is mirrored in the
output directory. If you want to organize all your generated serialization
classes for a given language in the output project's "data" directory, you can
place your templates in the `_schemas/data` directory. If you want JSON
serializer classes to be in the `data/json` directory, you can place the
JSON-specific template in the `_schemas/data/json` directory. More about schema
code generation [below](#Schema-code-generation).

The `_common` directory may include files for template macros that are shared
across all styles. Other directories that start with an underscore are ignored
and reserved for internal/future use.

The `_schemas` and `_common` directories are optional. If you don't need to
generate serializer code, you don't need to provide any templates in the
`_schemas`. If you don't need to share macros across styles, you don't need to
provide any templates in the `_common` directory.

The full set of templates for the C# language is [here](../xregistry/templates/cs).

## Template Info

For tools that wrap the code generator, like the VS Code extension, you can
place a `_templateinfo.json` file into the language directory to provide a
description for the language:

```json
{
  "description": "C# / .NET 6.0"
}
```

Inside each style directory, you can place a `_templateinfo.json` file that
provides a description for the style and a `priority` for sorting the list of
styles in a tool like the VS Code extension by relative importance:

```json
{
  "description": "Azure Functions HTTP trigger",
  "priority": 1
}
```

The default priority is 100, putting a style at/near the bottom of the list if
you don't specify a priority.

## Template styles

All code templates live grouped in style directories, each set typically
reflecting a full code project, including project files and other assets.

### Code generation approach

The general code generation philosophy is that the code generator should yield
code and assets that can be compiled and packaged without any further changes
and that the code contains extensibility hooks to integrate it into application
projects.

For instance, the code for C# consumers that is generated by the embedded
templates always includes a "dispatch interface" that can be implemented by the
application to handle messages. The dispatch interface shape is identical across
all transports and hosts but differs by message definition format. Shows here is
the dispatch interface for C# consumers that use the CloudEvents format:

```csharp
namespace Contoso.ERP.Consumer
{
    public interface IEventsDispatcher
    {
        Task OnReservationPlacedAsync(CloudEvent cloudEvent, OrderData data);
        Task OnPaymentsReceivedAsync(CloudEvent cloudEvent, PaymentData data);
        ...
    }
}
```

The implementation of the interface is then passed to the generated consumer
class, for instance in the factory methods that creates the consumer instance
for a declared endpoint.

```csharp
var consumer = new EventsEventConsumer(endpoint, eventsDispatcher);
```

In scenarios like Azure Functions, the dispatcher is added by dependency
injection.

```csharp
 private static void Main(string[] args)
{
    var host = new HostBuilder()
        .ConfigureServices(s =>
        {
            s.AddSingleton<IEventsDispatcher, MyEventsDispatcher>();
        })
        .Build();
    host.Run();
}
```

#### Code template files

All files you want to emit must be suffixed with `.jinja` and are run through
the Jinja template engine. If you don't put any Jinja template syntax in your
file, it will be copied verbatim to the output directory, with the ".jinja"
suffix stripped.

If you prefix a file with an underscore, it will be processed after all regular
files and also after all schema files have been generated. This is useful for
generating files that must know about all the generated classes or files, like a
project file. The underscore prefix is stripped from the output file name.

The filenames of the templates are used to determine the output file name.
Unless you use expansion macros, the file name is used as-is. For example, if
you have a template named `README.md.jinja`, the output file will be named
`README.md`.

Expansion macros are used to generate multiple files from a single template or
to rename the file based on a variable. The following macros are supported:

- `{projectname}` - expands into the name provided with the `--projectname`
  argument.
- `{classname}` - expands into the name of the generated class, which the tool
  infers from the schema document or the definition document. If the macro is
  used, the tool will modify the input document for the template such that it is
  scoped down to the definition or schema type that is supposed to be generated
  and call the template once for each type.
- `{classdir}` - this macro works like the {classname} option, but also creates
  a subdirectory reflecting the package name. This is specifically meant to help
  with Java conventions.

#### Schema file templates

The `_schemas` directory inside the language directory is special-cased and
contains the templates for the code generators for message payload schemas.

Schema languages are well-known by the code generator and templates must be
named for the schema format they support. All of these are optional:

- \_json.{language}.jinja - JSON Schema
- \_avro.{language}.jinja - Avro Schema
- \_proto.proto.jinja - Proto Schema
- \_proto.{language}.jinja - Proto Helpers
- \_avro.avsc.jinja - Apache Avro Schema
- \_avro.{language}.jinja - Apache Avro Helpers

Note that there may be a file with an extension .proto for Protobuf and a file
with an extension .avsc for Apache Avro. If a Protobuf schema is found, the
schema is passed to the .proto template as a string via `root` and the template
is then expected to produce an output .proto file, which might modify the input.
The equivalent happens for Apache Avro.

For example, the C# templates inject a "csharp_namespace" option. The `proto`
filter will pretty-print the proto schema. The `regex_replace` filter
necessarily strips the input's proto syntax declaration.

```jinja
syntax="proto3";

option csharp_namespace = "{{ project_name | pascal }}";

{{ root | proto | regex_replace('syntax[\\s]*=[\\s]*["\']proto3["\'];[\\s]*\n', '') }}
```

For Avro, the C# templates also add a namespace declaration to the Avro schema
and then iterate thorugh the schema types and emit them into the merged JSON
file, using the `tojson(3)` filter to pretty print the output fragments with an
indent level of 3.

```jinja
{%- set schema = root -%}
{%- set namespace = project_name | pascal -%}
{
    "namespace": "{{ namespace }}",
    {%- for attr, value in schema.items() %}
    {%- if attr != 'namespace' %}
    "{{ attr }}": {{ value | tojson(3) }},
    {%- endif %}
    {%- endfor %}
}
```

The code generator will call the template once for each schema type that must be
emitted based on the input definition. The required schema types are collected
"on the way" as the code generator traverses the input definition and the
templates use the [`schema_type`](#schema_type) filter to determine the correct
type name for a given referenced schema type for a payload.

For example, the C# code generator for CloudEvents uses the following template,
which infers required schema type names from the schemaurl property of
CloudEvents definitions with the help of the `schema_type` filter. The filter
does not collect duplicates.

```jinja
{%- for messagegroup_key, messagegroup in messagegroups.items() if (messagegroup | exists("format", "cloudevents" )) -%}
namespace {{ messagegroup.id | default(messagegroup_key) | namespace(project_name) | pascal }}
{
    public interface I{{ messagegroup.id | default(messagegroup_key) | strip_namespace | pascal }}Dispatcher
    {
        {%- for id, definition in messagegroup.messages.items() if (definition | exists( "format", "cloudevents" )) -%}
        {%- if definition.schemaurl -%}
        {%- set dataType = definition.schemaurl | schema_type | strip_namespace  | pascal -%}
        {%- else -%}
        {%- set dataType = "object" -%}
        {%- endif %}
        Task On{{ pascalDefinitionName | strip_namespace }}Async(CloudEvent cloudEvent, {{ dataType }} data);
        {%- endfor %}
    }
}
{%- endfor -%}
```

## Template variables

The input document, which is either a CloudEvents Discovery document or a schema
document, is passed to the template as a variable named `root`. The `root`
variable's structure reflects the respective input document.

- For code generators for message payload schemas, the `root` variable is the
  root of the CloudEvents Discovery document, corresponding to the CloudEvent
  Discovery schema type `document`. Underneath `root` are three collections:
  - `messagegroups` - a dictionary of message definition groups, keyed by the
    messagegroup's ID.
  - `schemagroups` - a dictionary of schema definition groups, keyed by the
    messagegroup's ID.
  - `endpoints` - a dictionary of endpoints, keyed by the endpoint's ID.
- For JSON schema, the `root` variable is the root of the JSON schema document.
- For Proto schema, the `root` variable is a `string` (!) containing the
  contents of the input file.
- For Avro schema, the `root` variable is the root of the Avro schema document.

As discussed above, the {classdir} and {classfile} filename expansion macros
will modify the input document given to the template and scope it to the current
object that shall be emitted.

Otherwise, the template always gets the full input document.

If the `--definitions` argument points to a URL or file name that
returns/contains a fragment of a CloudEvents discovery document, such as a
single `schemagroup` or `messagegroup` the generator will synthesize a full discovery
document around the fragment and pass it to the template.

### Filters

In addition to the many filters
[built into Jinja](https://jinja.palletsprojects.com/en/3.0.x/templates/#filters),
thje following extra filters are available for use in templates:

#### `pascal`

Converts a string (including those in camelCase and snake_case) to PascalCase

Example:

```jinja
{{ "foo_bar" | pascal }} -> FooBar
```

#### `camel`

Converts a string (including those in snake_case and PascalCase) to camelCase

Example:

```jinja
{{ "foo_bar" | camel }} -> fooBar
```

#### `snake`

Converts a string (including those in camelCase and PascalCase) to snake_case

Example:

```jinja
{{ "fooBar" | snake }} -> foo_bar
```

#### `pad(len)`

Left-justifies a string with spaces to the specified length. This is useful for
sorting version strings in a template.

Example:

```jinja
{{ "1.0" | pad(5) }} -> "  1.0"
{{ "1.0" | pad(5) }} -> " 11.0"
```

#### `strip_namespace`

Strips the namespace/package portion off an expression

Example:

```jinja
{{ "com.example.Foo" | strip_namespace }} -> Foo
```

#### `strip_invalid_identifier_characters`

Strips invalid characters from an identifier. This is useful for converting
strings to identifiers in languages that have stricter rules for identifiers.
All unsupported characters are replaced with an underscore.

Example:

```jinja
{{ "foo-bar" | strip_invalid_identifier_characters }} -> foo_bar
{{ "@foobar" | strip_invalid_identifier_characters }} -> _foobar
```

#### `namespace`

Gets the namespace/package portion of an expression

Example:

```jinja
{{ "com.example.Foo" | namespace }} -> com.example
```

#### `concat_namespace`

Concatenates the namespace/package portions of an expression

Example:

```jinja
{{ "com.example.Foo" | concat_namespace }} -> comexampleFoo
```

If you want to pascal case the expression, use the pascal filter first, e.g.

```jinja
{{ "com.example.Foo" | pascal | concat_namespace }} -> ComExampleFoo
```

#### `toyaml`

Formats the given object as YAML. This is useful for emitting parts of the input
document, for instance JSON Schema elements, into YAML documents. `tojson` is
already built into Jinja.

Example:

```jinja
{{ root | toyaml }}
```

#### `proto`

Pretty-prints the given string as a .proto file

Example:

```jinja
{{ root | proto }}
```

#### `schema_type`

Determines the type name of an expression given a schema URL. This filter has
the side-effect that all schema URLs and schema types are collected by the
generator and the schema types are emitted in the generated code.

Example:

```jinja
{{ "https://example.com/schema.json#/definitions/MyType" | schema_type }} -> MyType
```

#### `push(stack_name)`

Pushes a value onto a named stack. This is useful for collecting values in a
template and using them later. The corresponding [`pop`](#popstack_name) and
[`stack`](#stackstack_name) functions can be used to retrieve the values. Push "eats" its
input value and emits an empty string.

Example:

```jinja
{% "foo" | push("name") %}
```

#### `pushfile(name)`

Pushes a string value into a named output file. With this, you can dynamically
emit files as needed. The filter eats its input value and emits an empty string.

Example from the Java templates in amqp.jinja.include where a dispatch interface
class is emitted into a file named after the interface using the output of a
called macro:

```jinja
{%- macro DeclareDispatchInterfaces(project_name, root) -%}
{%- set messagegroups = root.messagegroups -%}
{%- if messagegroups | exists("binding", "amqp" ) %}
{%- for messagegroup_key, messagegroup in messagegroups.items() if (messagegroup | exists("binding", "amqp" )) -%}
{%- set pascalGroupName = messagegroup.id | default(messagegroup_key) | pascal -%}
{%- set interfaceName = "I"+(pascalGroupName | strip_namespace)+"AmqpDispatcher" -%}
{{- DeclareDispatchInterface(project_name, messagegroup, pascalGroupName, interfaceName) | pushfile(interfaceName+".java") -}}
{%- endfor -%}
{%- endif -%}
{%- endmacro -%}

---> interfaceName+".java" file with the contents of DeclareDispatchInterface
```

#### `save(prop_name)`

Saves a value in a named property. This is useful for collecting values in a
template and using them later, even in a different template. The corresponding
[`get`](#getprop_name) function can be used to retrieve the value.

Example:

```jinja
{% "foo" | save("name") %}
```

#### exists(prop, value)

Checks whether the given property exists anywhere in the given object scope with
the value prefixed with the given string (case-insensitive)

Example:

```jinja
{% if root | exists("format", "amqp") %}
    // do something
{% endif %}
```

#### regex_search(pattern)

Performs a regex search. Returns a list of matches.

Example:

```jinja
{% if "foo" | regex_search("f") %}
    // do something
{% endif %}
```

#### regex_replace(pattern, replacement)

Does a regex based replacement. Returns the result.

Example:

```jinja
{{ "foo_bar" | regex_replace("[^A-Za-z_]", "-") }} -> "foo-bar"
```

### Functions

You can use all expressions and functions defined by the Jinja2 standard
library. In addition, the following functions are available:

#### `pop(stack_name)`

Pops a value from a named stack collected with [`push`](#pushstack_name). This
works across template files. If the stack is empty, an empty string is returned.

Example:

```jinja
{% "foo" | push("name") %}
{% "bar" | push("name") %}
{% "baz" | push("name") %}
{{ pop("name") }} -> "baz"
{{ pop("name") }} -> "bar"
{{ pop("name") }} -> "foo"
```

#### `stack(stack_name)`

Gets the full contents of a named stack collected with
[`push`](#pushstack_name). This works across template files.

Example:

```jinja
{% "foo" | push("name") %}
{% "bar" | push("name") %}
{% "baz" | push("name") %}
{% for x in stack("name") %}{{ x }} {% endif %} -> foo bar faz
```

#### `get(prop_name)`

Gets the value of a named property collected with [`save`](#saveprop_name). This
works across template files.

Example:

```jinja
{% "foo" | save("name") %}
{{ get("name") }} -> "foo"
```

#### `latest_dict_entry(dict)`

Gets the "latest" entry from a dictionary, which is specifically designed to
work for the `versions` property of a schema object. The latest entry is the one
with the highest version number.

Example:

```jinja
{%- set schemaObj = schema_object(root, event.schemaurl ) -%}
    {%- if schemaObj.format is defined -%}
       {%- set schemaVersion = latest_dict_entry(schemaObj.versions) %}
```

#### `schema_object(root, schemaurl)`

Gets an object resolving a given relative URL. This is useful for getting the
schema object for a given event or command.

Example:

```jinja
{%- set schemaObj = schema_object(root, event.schemaurl ) -%}
    {%- if schemaObj.format is defined -%}
```

### Tags

You can use all tags defined by the Jinja2 standard library. In addition, the
following tags are available:

#### `{% exit %}`

Exits the template without producing any output. This is useful for skipping the
file if the input document doesn't contain the required information or if the
template creates output files using [`pushfile`](#pushfilename) and you don't
want a file to be emitted for the template itself.

Example:

```jinja
{% if root.type is not defined %}{% exit %}{% endif %}
```

#### `{% uuid %}`

Generates a UUID and emits it into the output. This is useful for generating
unique identifiers for things like namespaces. **(Consider this tag
deprecated. It will turn into a function)**.

Example:

```jinja
{% uuid %} -> 3e8c0b0a-1b5a-4b3f-8c1c-1b5a4b3f8c1c
```

#### `{% time %}`

Generates a timestamp and emits it into the output. **(Consider this tag
deprecated. It will turn into a function)**.

Example:

```jinja
{% time %} -> 2020-01-01T00:00:00Z
```
