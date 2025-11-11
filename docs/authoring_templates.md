# Authoring templates

Output of the code generator is driven by a set of templates that are stored in the tool package's internal `templates` directory and are installed with the tool.

Template authors write text files that are processed by the template engine. You don't have to write any extensions or plugins to use the template engine. The template language, which is an extension of the [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/templates/) template language, is built into the tool and has a set of extensions specific to code generation that cover even fairly complicated scenarios.

Custom templates can be provided by the user by creating a directory that has the same structure as this templates directory and passing the path to the `--templates` command line argument. Any templates found in the user-provided directory will override the corresponding _language_ and _style_ of the built-in templates and you can add new languages and styles.

The generator distinguishes between templates for endpoints and message definition groups (those are the _styles_).

## Directory structure

The content of the `templates` directory is dynamic and extensible.

The common structure looks like this:

```text
templates
├── {language}
│   ├── _templateinfo.json
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

In a templates directory reside subdirectories for each of the supported output languages. Adding support for a new language is as simple as adding a new directory with a unique name. That name should correspond to the common file name suffix for the language, e.g. if you were adding support for C++ you would name the directory `cpp`.

The tool uses the name of the directory as the language identifier for the `--language` command line argument. The language identifier is also used to find the correct templates for automatic generation of schema serializer code as shown in the illustration above.

Under each language directory, there are subdirectories for each template set. Template sets are called "styles" to avoid conflations with other overloaded terms. The tool uses the name of the subdirectory as the style identifier for the `--style` command line argument.

The `_common` directory may include files for template macros that are shared across all styles. Other directories that start with an underscore are ignored and reserved for internal/future use.

The `_common` directory is optional. If you don't need to share macros across styles, you don't need to provide any templates in the `_common` directory.

The full set of templates for the C# language is [here](../xregistry/templates/cs).

## Template Info

For tools that wrap the code generator, like the VS Code extension, you can place a `_templateinfo.json` file into the language directory to provide metadata for the language:

```json
{
  "description": "C# / .NET 6.0+",
  "priority": 1
}
```

Inside each style directory, you can place a `_templateinfo.json` file that provides metadata for the style. This file supports the following properties:

### Template Info Properties

#### `description` (string)

A human-readable description of the template language or style. This is displayed in tools like the VS Code extension to help users understand what the template generates.

Example: `"C# AMQP 1.0 Producer"`, `"TypeScript Apache Kafka Consumer"`

#### `priority` (number, default: 100)

An integer value used for sorting the list of templates in tools. Lower numbers appear higher in the list, indicating higher priority or importance. The default priority is 100, which places templates at/near the bottom of the list.

Example: `1` (high priority), `50` (medium priority), `100` (default/low priority)

#### `main_project_name` (string template, optional)

Specifies the name of the main project to be generated. This overrides the default project name. Supports template syntax with placeholders and filters.

Example: `"{project_name|pascal}AmqpProducer"`, `"{project_name}KafkaConsumer"`

#### `data_project_name` (string template, optional)

Specifies the name of the data/schema project to be generated. This is used for organizing generated data classes separately from the main application code. Supports template syntax with placeholders and filters.

Example: `"{project_name|pascal}Data"`, `"{project_name}Schemas"`

#### `data_project_dir` (string template, optional)

Specifies the directory name for the data project. If not specified, defaults to the value of `data_project_name`. Supports template syntax with placeholders and filters.

Example: `"{project_name|snake}_data"`, `"schemas/{project_name}"`

#### `src_layout` (boolean, optional)

When `true`, indicates that the template uses a source layout convention (e.g., putting code under a `src/` directory). This affects how the generator organizes the output directory structure.

Example: `true` or `false`

### Template String Syntax

String properties like `main_project_name` and `data_project_name` support a template syntax for dynamic value resolution:

**Placeholders:**

- `{variable_name}` - replaced with the value of the variable

**Filters:**

- `{variable|filter}` - apply a filter to transform the value
- `{variable|filter1|filter2}` - chain multiple filters

**Path Suffixes:**

- `{variable~path~segment}` - append path segments with `/` separators

**Available Variables:**

The following variables are available depending on the context where `resolve_string` is used:

**For `_templateinfo.json` properties** (`main_project_name`, `data_project_name`, `data_project_dir`):

- `project_name` - the project name provided via `--projectname` argument

**Available Filters:**

- `lower` - converts to lowercase
- `upper` - converts to uppercase
- `pascal` - converts to PascalCase
- `camel` - converts to camelCase
- `snake` - converts to snake_case
- `dotdash` - replaces `.` with `-`
- `dashdot` - replaces `-` with `.`
- `dotunderscore` - replaces `.` with `_`
- `underscoredot` - replaces `_` with `.`

**Examples:**

```json
{
  "main_project_name": "{project_name|pascal}Producer",
  "data_project_name": "{project_name|snake}_data",
  "data_project_dir": "{project_name~schemas}"
}
```

### Complete Example

```json
{
  "description": "C# Azure Event Hubs Consumer",
  "priority": 5,
  "src_layout": true,
  "main_project_name": "{project_name|pascal}EventHubsConsumer",
  "data_project_name": "{project_name|pascal}Data",
  "data_project_dir": "{project_name|pascal}Data"
}
```

## Template styles

All code templates live grouped in style directories, each set typically reflecting a full code project, including project files and other assets.

### Code generation approach

The general code generation philosophy is that the code generator should yield code and assets that can be compiled and packaged without any further changes and that the code contains extensibility hooks to integrate it into application projects.

For instance, the code for C# consumers that is generated by the embedded templates always includes a "dispatch interface" that can be implemented by the application to handle messages. The dispatch interface shape is identical across all transports and hosts but differs by message definition format. Shows here is the dispatch interface for C# consumers that use the CloudEvents format:

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

The implementation of the interface is then passed to the generated consumer class, for instance in the factory methods that create the consumer instance for a declared endpoint.

```csharp
var consumer = new EventsEventConsumer(endpoint, eventsDispatcher);
```

In scenarios like Azure Functions, the dispatcher is added by dependency injection.

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

All files you want to emit must be suffixed with `.jinja` and are run through the Jinja template engine. If you don't put any Jinja template syntax in your file, it will be copied verbatim to the output directory, with the ".jinja" suffix stripped.

If you prefix a file with an underscore, it will be processed after all regular files and also after all schema files have been generated. This is useful for generating files that must know about all the generated classes or files, like a project file. The underscore prefix is stripped from the output file name.

## Template File Names

Template file names determine the output file names and can include special macros for dynamic naming and multi-file generation.

### Basic File Naming

The simplest approach is to use a static file name. The template engine will use the name as-is (minus the `.jinja` extension).

**Example:** A template file named `README.md.jinja` generates an output file named `README.md`.

### File Name Expansion Macros

Expansion macros in file names enable generating multiple files from a single template or dynamically naming files based on project or class information.

#### `{projectname}` Macro

Expands to the name provided with the `--projectname` argument.

**Example:** `{projectname}.csproj.jinja` → `MyProject.csproj` (when `--projectname MyProject`)

#### `{classname}` Macro

Expands to the name of the generated class, inferred from the schema or definition document. When this macro is used:

- The generator calls the template once for each type/class
- The input document is scoped down to the specific definition or schema type
- Only the class name (without namespace/package) is used

**Example:** `{classname}.cs.jinja` → `Order.cs`, `Customer.cs`, etc. (one file per class)

#### `{classdir}` Macro

Works like `{classname}` but also creates subdirectories reflecting the package/namespace structure. This is particularly useful for Java conventions where package structure maps to directory structure.

**Example:** `{classdir}.java.jinja` with class `com.example.Order`:

- Creates directory: `com/example/`
- Generates file: `com/example/Order.java`

### Advanced File Name Templates

File names support the same template variable syntax as `_templateinfo.json` properties, with access to a richer set of variables:

**Available Variables:**

- `projectname` - the code project name
- `mainprojectname` - the main project name
- `dataprojectname` - the data project name
- `mainprojectdir` - main project as path (dots→slashes)
- `dataprojectdir` - data project as path (dots→slashes)
- `projectdir` - project as path (dots→slashes)
- `projectsrc` - project source path (prefixed with `src/`)
- `testdir` - test directory (`tests/` or `../tests/`)
- `rootdir` - root directory marker
- `classname` - class name only
- `classfull` - fully qualified class name
- `classpackage` - package/namespace name
- `classdir` - class formatted for directories

**Available Filters:**

Same filters as in `_templateinfo.json` templates: `lower`, `upper`, `pascal`, `camel`, `snake`, `dotdash`, `dashdot`, `dotunderscore`, `underscoredot`

**Examples:**

```text
{mainprojectdir}Program.cs.jinja → MyProject/Program.cs
{dataprojectdir}Models/BaseModel.cs.jinja → MyProjectData/Models/BaseModel.cs
{testdir}{projectname}Tests.cs.jinja → tests/MyProjectTests.cs
{rootdir}README.md.jinja → README.md (at output root)
```

### Scoped Document Context

When using `{classname}` or `{classdir}` macros, the template receives a modified `root` variable that contains only the relevant message group or schema:

- The template is invoked once per class/type
- `root.messagegroups` contains only the single message group being processed
- `root.schemagroups` and `root.endpoints` remain available for reference

## Template variables

The input document, which is either a CloudEvents Discovery document or a schema document, is passed to the template as a variable named `root`. The `root` variable's structure reflects the respective input document.

- For code generators for message payload schemas, the `root` variable is the root of the CloudEvents Discovery document, corresponding to the CloudEvent Discovery schema type `document`. Underneath `root` are three collections:
  - `messagegroups` - a dictionary of message definition groups, keyed by the message group's ID.
  - `schemagroups` - a dictionary of schema definition groups, keyed by the message group's ID.
  - `endpoints` - a dictionary of endpoints, keyed by the endpoint's ID.

As discussed above, the `{classdir}` and `{classfile}` filename expansion macros will modify the input document given to the template and scope it to the current object that shall be emitted.

Otherwise, the template always gets the full input document.

If the `--definitions` argument points to a URL or file name that returns/contains a fragment of a CloudEvents discovery document, such as a single `schemagroup` or `messagegroup`, the generator will synthesize a full discovery document around the fragment and pass it to the template.

### Filters

In addition to the many filters [built into Jinja](https://jinja.palletsprojects.com/en/3.0.x/templates/#filters), the following extra filters are available for use in templates:

#### Case Conversion Filters

##### `pascal`

Converts a string (including those in camelCase and snake_case) to PascalCase. Handles namespace separators (`.` and `::`).

Example:

```jinja
{{ "foo_bar" | pascal }} -> FooBar
{{ "com.example.foo" | pascal }} -> Com.Example.Foo
```

##### `camel`

Converts a string (including those in snake_case and PascalCase) to camelCase. Handles namespace separators (`.` and `::`).

Example:

```jinja
{{ "foo_bar" | camel }} -> fooBar
{{ "FooBar" | camel }} -> fooBar
```

##### `snake`

Converts a string (including those in camelCase and PascalCase) to snake_case. Handles namespace separators (`.` and `::`).

Example:

```jinja
{{ "fooBar" | snake }} -> foo_bar
{{ "FooBar" | snake }} -> foo_bar
```

#### String Manipulation Filters

##### `dotdash`

Replaces dots with dashes in a string.

Example:

```jinja
{{ "com.example.Foo" | dotdash }} -> com-example-Foo
```

##### `dashdot`

Replaces dashes with dots in a string.

Example:

```jinja
{{ "com-example-Foo" | dashdot }} -> com.example.Foo
```

##### `dotunderscore`

Replaces dots with underscores in a string.

Example:

```jinja
{{ "com.example.Foo" | dotunderscore }} -> com_example_Foo
```

##### `underscoredot`

Replaces underscores with dots in a string.

Example:

```jinja
{{ "com_example_Foo" | underscoredot }} -> com.example.Foo
```

##### `lstrip(prefix)`

Strips a prefix from a string.

Example:

```jinja
{{ "prefix_value" | lstrip("prefix_") }} -> value
```

##### `pad(len)`

Left-justifies a string with spaces to the specified length. This is useful for aligning version strings in templates.

Example:

```jinja
{{ "1.0" | pad(5) }} -> "1.0  "
{{ "11.0" | pad(5) }} -> "11.0 "
```

##### `strip_invalid_identifier_characters`

Strips invalid characters from an identifier. This is useful for converting strings to identifiers in languages that have stricter rules for identifiers. All unsupported characters are replaced with an underscore.

Example:

```jinja
{{ "foo-bar" | strip_invalid_identifier_characters }} -> foo_bar
{{ "@foobar" | strip_invalid_identifier_characters }} -> _foobar
```

#### Namespace Manipulation Filters

##### `strip_namespace`

Strips the namespace/package portion off an expression, leaving only the class name.

Example:

```jinja
{{ "com.example.Foo" | strip_namespace }} -> Foo
```

##### `namespace(namespace_prefix="")`

Gets the namespace/package portion of an expression, optionally prepending a prefix.

Example:

```jinja
{{ "com.example.Foo" | namespace }} -> com.example
{{ "Foo" | namespace("com.example") }} -> com.example
```

##### `namespace_dot(namespace_prefix="")`

Gets the namespace portion of an expression followed by a dot, or an empty string if no namespace exists.

Example:

```jinja
{{ "com.example.Foo" | namespace_dot }} -> com.example.
{{ "Foo" | namespace_dot }} -> ""
```

##### `concat_namespace(namespace_prefix="")`

Concatenates the namespace/package portions of an expression with an optional prefix.

Example:

```jinja
{{ "com.example.Foo" | concat_namespace }} -> com.example.Foo
```

##### `strip_dots`

Removes all dots from a string, concatenating namespace portions.

Example:

```jinja
{{ "com.example.Foo" | strip_dots }} -> comexampleFoo
```

#### Format Conversion Filters

##### `toyaml(indent=4)`

Formats the given object as YAML with specified indentation. This is useful for emitting parts of the input document, for instance JSON Schema elements, into YAML documents. `tojson` is already built into Jinja.

Example:

```jinja
{{ root | toyaml }}
{{ root | toyaml(2) }}
```

##### `proto`

Formats a proto text string with proper indentation and spacing.

Example:

```jinja
{{ proto_text | proto }}
```

#### Search and Pattern Matching Filters

##### `exists(prop, value)`

Recursively checks whether the given property exists anywhere in the given object scope with the value prefixed with the given string (case-insensitive).

Example:

```jinja
{% if root | exists("format", "amqp") %}
    // do something
{% endif %}
```

##### `existswithout(prop, value, propother, valueother)`

Checks whether a property exists with a value prefix, but only if another property does not exist with another value. Useful for conditional checks in templates.

Example:

```jinja
{% if root | existswithout("format", "amqp", "encoding", "binary") %}
    // do something
{% endif %}
```

##### `regex_search(pattern)`

Performs a regex search. Returns a list of matches.

Example:

```jinja
{% if "foo" | regex_search("f") %}
    // do something
{% endif %}
```

##### `regex_replace(pattern, replacement)`

Does a regex-based replacement. Returns the result.

Example:

```jinja
{{ "foo_bar" | regex_replace("[^A-Za-z_]", "-") }} -> "foo-bar"
```

#### Schema Processing Filters

##### `schema_type(project_name, root, schema_format)`

Returns the type name for a schema reference, considering the schema format and project context.

Example:

```jinja
{{ schema_ref | schema_type(projectname, root, "avro") }}
```

#### Stack and State Management Filters

##### `push(stack_name)`

Pushes a value onto a named stack. This works across template files. Returns an empty string.

Example:

```jinja
{{ "value1" | push("mystack") }}
{{ "value2" | push("mystack") }}
```

##### `pushfile(name)`

Pushes a file path and value onto the 'files' stack for later processing. Returns an empty string.

Example:

```jinja
{{ content | pushfile("output.txt") }}
```

##### `save(prop_name)`

Saves a value in the context dictionary for later retrieval. Returns the value for chaining.

Example:

```jinja
{{ "important_value" | save("myvar") }}
```

#### Resource Tracking Filters

##### `mark_handled`

Marks a resource reference as handled by templates. Used for template-driven resource management.

Example:

```jinja
{{ "#/schemas/myschema" | mark_handled }}
```

##### `is_handled`

Checks if a resource reference has been marked as handled.

Example:

```jinja
{% if "#/schemas/myschema" | is_handled %}
    // skip this resource
{% endif %}
```

### Functions

You can use all expressions and functions defined by the Jinja2 standard library. In addition, the following functions are available as global functions in templates:

#### `pop(stack_name)`

Pops a value from a named stack collected with `push`. This works across template files. If the stack is empty, an empty string is returned.

Example:

```jinja
{{ "foo" | push("name") }}
{{ "bar" | push("name") }}
{{ "baz" | push("name") }}
{{ pop("name") }} -> "baz"
{{ pop("name") }} -> "bar"
{{ pop("name") }} -> "foo"
```

#### `stack(stack_name)` _(Note: Currently only available via ctx.stacks.stack() in code)_

Gets the full contents of a named stack collected with `push`. This works across template files. Returns a list.

**Important:** This function is currently not exposed as a global in templates but exists in the ContextStacksManager. To iterate over a stack, use `pop()` in a loop or access via internal context.

Example (conceptual):

```jinja
{{ "foo" | push("name") }}
{{ "bar" | push("name") }}
{{ "baz" | push("name") }}
{% for x in stack("name") %}{{ x }} {% endfor %} -> foo bar baz
```

#### `get(prop_name)` _(Note: Currently only available via ctx.stacks.get() in code)_

Gets the value of a named property collected with `save`. This works across template files.

**Important:** This function is currently not exposed as a global in templates but exists in the ContextStacksManager. Values saved with `save` filter can be retrieved in code but not directly in templates.

Example (conceptual):

```jinja
{{ "foo" | save("name") }}
{{ get("name") }} -> "foo"
```

#### `latest_dict_entry(dict)`

Gets the "latest" entry from a dictionary, which is specifically designed to work for the `versions` property of a schema object. The latest entry is the one with the highest version number.

Example:

```jinja
{%- set schemaObj = schema_object(root, event.schemaurl) -%}
{%- if schemaObj.versions is defined -%}
   {%- set schemaVersion = latest_dict_entry(schemaObj.versions) %}
{%- endif -%}
```

#### `schema_object(root, schemaurl)`

Gets an object by resolving a given relative URL within the root document. This is useful for getting the schema object for a given event or command.

Example:

```jinja
{%- set schemaObj = schema_object(root, event.schemaurl) -%}
{%- if schemaObj.format is defined -%}
    // work with schemaObj
{%- endif -%}
```

#### URL Utility Functions

##### `geturlhost(url)`

Extracts the hostname from a URL.

Example:

```jinja
{{ geturlhost("https://example.com:8080/path") }} -> example.com
```

##### `geturlpath(url)`

Extracts the path from a URL.

Example:

```jinja
{{ geturlpath("https://example.com:8080/path/to/resource") }} -> /path/to/resource
```

##### `geturlscheme(url)`

Extracts the scheme (protocol) from a URL.

Example:

```jinja
{{ geturlscheme("https://example.com/path") }} -> https
```

##### `geturlport(url)`

Extracts the port from a URL.

Example:

```jinja
{{ geturlport("https://example.com:8080/path") }} -> 8080
```

#### `dependency(language, dependency_name, runtime_version)`

Retrieves dependency information for a specific language runtime. Returns the dependency configuration as a string (e.g., XML for Maven dependencies).

Example:

```jinja
{{ dependency("java", "azure-messaging-eventhubs", "1.11.0") }}
```

### Tags

You can use all tags defined by the Jinja2 standard library. In addition, the following custom tags are available:

#### `{% exit %}`

Exits the template without producing any output. This is useful for skipping the file if the input document doesn't contain the required information or if the template creates output files using `pushfile` and you don't want a file to be emitted for the template itself.

Example:

```jinja
{% if root.type is not defined %}{% exit %}{% endif %}
```

#### `{% time %}`

Generates a timestamp and emits it into the output. The timestamp is in ISO 8601 format with microseconds.

Example:

```jinja
{% time %} -> 2025-11-11T10:30:45.123456Z
```

#### `{% error "message" %}`

Raises a template error with a custom message. This stops template rendering and reports the error to the user. Useful for validation and enforcing template preconditions.

Example:

```jinja
{% if not projectname %}
    {% error "projectname is required but not provided" %}
{% endif %}
```

