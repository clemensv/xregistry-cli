# xRegistry Code Generation CLI

[![Python Test](https://github.com/xregistry/codegen/actions/workflows/test.yml/badge.svg)](https://github.com/xregistry/codegen/actions/workflows/test.yml)
[![Python Release](https://github.com/xregistry/codegen/actions/workflows/build.yml/badge.svg)](https://github.com/xregistry/codegen/actions/workflows/build.yml)

A command-line tool for working with xRegistry documents and APIs, with powerful code generation capabilities for building messaging and eventing applications.

## Why xRegistry Code Generation CLI?

### Production-Ready Code, Not Just Snippets

Unlike typical code generators that dump a single file and leave you to figure out the rest, xRegistry Code Generation CLI generates complete, **SDK-like projects** with:

- ✅ **Working integration tests** out of the box (using Docker/Testcontainers)
- ✅ **Type-safe producer and consumer clients** for multiple platforms
- ✅ **Compile-ready projects** with proper dependency management
- ✅ **Best-practice code structure** following language conventions
- ✅ **Robust schema handling** via [Avrotize](https://github.com/clemensv/avrotize)

### Broad Platform Support

Generate type-safe clients for Java, C#, Python, and TypeScript across multiple messaging systems:

- Generic clients: MQTT, AMQP, Apache Kafka
- Azure-specific: Event Hubs, Service Bus, Event Grid
- Protocol conversions: AsyncAPI and OpenAPI documents

### Flexible Workflows

Work with xRegistry definitions using:

- **Local files** (manifest mode) for offline development
- **Remote registries** (catalog mode) for team collaboration
- **Custom templates** for organization-specific code generation

## Table of Contents

- [What is xRegistry?](#what-is-xregistry)
- [xRegistry Message Catalogs](#xregistry-message-catalogs)

## What is xRegistry?

The [xRegistry project](https://xregistry.io/) run by the CNCF Serverless WG
defines a generic, extensible, and interoperable registry for metadata and
metadata documents. In particular, it is designed to support registries that aid
with the discovery and description of messaging and eventing endpoints and
therefore has three built-in registries for (payload-)schemas, message
definitions, and endpoints.

xRegistry defines both an API and a document format for managing metadata and
one of its key characteristics is that the REST API and the document model are
symmetrical. An HTTP endpoint path in the API corresponds to a JSON pointer path
in the document model.

All metadata resources are organized in groups, and each group can contain
multiple resources. Some resources allow for maintaining multiple versions, as
it is the case for schemas.

The xRegistry API and document model is defined in the
[xRegistry API specification](https://github.com/xregistry/spec).

## License and Governance rules

This project is part of the CNCF xRegistry project and subject to the
governance rules laid out in the [project governance document](https://github.com/xregistry/spec/blob/main/docs/GOVERNANCE.md)

## xRegistry Message Catalogs

xRegistry Message Catalogs are a set of registries that are built on top of
xRegistry and are designed to support the discovery and description of messaging
and eventing endpoints. The following catalogs are defined:

- **Schema Catalog**: A registry for schemas that can be used to validate
    messages.
- **Message Catalog**: A registry for message definitions that describe the
    structure of messages. Messages can be defined as abstract, transport
    neutral envelopes based on [CloudEvents](https://cloudevents.io) or as concrete
    messages that are bound to a specific transport protocol, whereby AMQP, HTTP, MQTT,
    and Apache Kafka are directly supported. Each message definition can associated
    with a schema from the schema catalog for describing the message payload.
- **Endpoint Catalog**: A registry for endpoints that can be used to send or
    receive messages. Each endpoint can be associated with one or more groups of
    message definitions from the message catalog.

The three catalogs are designed to be used together, with the endpoint catalog
referring to message definition groups and message definitions referring to schemas.

You can study some examples of xRegistry Message Catalog documents in the
samples directory of this repository:

- [**Contoso ERP**](samples/message-definitions/contoso-erp.xreg.json): A
    simple example of a message catalog for a fictional ERP system.
- [**Inkjet Printer**](samples/message-definitions/inkjet.xreg.json): A
    fictitious group of events as they may be raised by an inkhet printer.
- [**Fabrikam Motorsports**](samples/message-definitions/fabrikam-motorsports.xreg.json):
    An example for an event stream as it may be used in a motorsports telemetry
    scenario.
- [**Vacuum Cleaner**](samples/message-definitions/vacuumcleaner.xreg.json):
    A fictitious group of events as they may be raised by a vacuum cleaner.

## Installation

The tool requires Python 3.10 or later. Install directly from GitHub:

```bash
pip install git+https://github.com/xregistry/codegen.git
```

This installs the `xregistry` package with two command-line aliases:

- `xregistry` - Full command name
- `xcg` - Short alias for convenience

Both commands are functionally identical. Use whichever you prefer.

For local development and testing, see [Development Environment](docs/development_environment.md).

## Usage

The tool is invoked as `xcg` (or `xregistry`) and supports the following subcommands:

- `xcg generate`: Generate code from xRegistry definitions
- `xcg validate`: Validate xRegistry definition files
- `xcg list`: List available code generation templates
- `xcg config`: Manage tool configuration (defaults, registry URLs, auth)
- `xcg manifest`: Work with local xRegistry files (offline mode)
- `xcg catalog`: Interact with remote xRegistry services (online mode)

### Working with xRegistry Data: Manifest vs Catalog

xRegistry CLI supports two modes for managing registry data:

#### Manifest Mode (Local Files)

Use `xcg manifest` commands to work with **local JSON files** containing xRegistry definitions:

```bash
# Create/update local manifest file
xcg manifest messagegroup add --manifest=./my-registry.json --id=orders ...

# Add messages to the local file
xcg manifest message add --manifest=./my-registry.json --messagegroupid=orders ...
```

**When to use manifest mode:**

- Offline development and testing
- Version-controlled registry definitions (Git)
- Local-first workflows
- No network dependency

#### Catalog Mode (Remote Service)

Use `xcg catalog` commands to interact with a **remote xRegistry HTTP API**:

```bash
# Set up registry connection
xcg config set registry.base_url https://registry.example.com
xcg config set registry.auth_token <token>

# Work with remote registry
xcg catalog messagegroup add --id=orders ...
xcg catalog message add --messagegroupid=orders ...
```

**When to use catalog mode:**

- Team collaboration with shared registry
- Central governance and discovery
- Integration with CI/CD pipelines
- Live registry queries

**Note:** Currently supports [xreg-github](https://github.com/duglin/xreg-github/) registry implementation.

Run `xcg manifest --help` or `xcg catalog --help` to see all available operations (add, get, update, delete, list) for endpoints, message groups, messages, and schemas.

### Config Command

Manage persistent configuration to avoid repeating common arguments:

```bash
# View all configuration
xcg config list

# Set default values
xcg config set defaults.project_name MyProject
xcg config set defaults.language cs
xcg config set defaults.style producer
xcg config set defaults.output_dir ./generated

# Set registry connection
xcg config set registry.base_url https://registry.example.com
xcg config set registry.auth_token <your-token>

# Set custom model URL
xcg config set model.url https://example.com/custom-model.json

# Get specific value
xcg config get defaults.language

# Clear a value
xcg config unset defaults.language

# Reset all to defaults
xcg config reset

# Export as JSON
xcg config list --format json
```

Configuration is stored in a platform-specific location:

- **Windows:** `%APPDATA%\xregistry\config.json`
- **macOS:** `~/Library/Application Support/xregistry/config.json`
- **Linux:** `~/.config/xregistry/config.json`

**Available configuration keys:**

| Key | Description |
|-----|-------------|
| `defaults.project_name` | Default project name for code generation |
| `defaults.language` | Default language (cs, java, py, ts, etc.) |
| `defaults.style` | Default style (producer, consumer, etc.) |
| `defaults.output_dir` | Default output directory |
| `registry.base_url` | Base URL for remote xRegistry catalog |
| `registry.auth_token` | Authentication token for catalog access |
| `registry.timeout` | HTTP timeout for catalog requests (seconds) |
| `model.url` | Custom model.json URL (overrides built-in) |
| `model.cache_timeout` | Cache duration for model downloads (seconds) |

### Generate

The `generate` subcommand generates code from a definition file. The tool
includes a set of built-in language/style template sets that can be enumerated
with the [List](#list) command.

The `generate` command takes the following options:

| Option             | Description                                                                                                                                                                        |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--projectname`    | **Required** The project name (namespace name) for the generated code.                                                                                                             |
| `--language`       | **Required** The shorthand code of the language to use for the generated code, for instance "cs" for C# or "ts" for TypeScript/JavaScript. See [Languages](#languages-and-styles). |
| `--style`          | The code style. This selects one of the template sets available for the given language, for instance "producer". See [Styles](#languages-and-styles)                               |
| `--output`         | The directory where the generated code will be saved. The generator will overwrite existing files in this directory.                                                               |
| `--definitions`    | The path to a local file or a URL to a file containing CloudEvents Registry definitions.                                                                                           |
| `--requestheaders` | Extra HTTP headers for HTTP requests to the given URL in the format `key=value`.                                                                                                   |
| `--templates`      | Paths of extra directories containing custom templates See [Custom Templates].                                                                                                     |
| `--template-args`  | Extra template arguments to pass to the code generator in the form `key=value`.                                                                                                    |

#### Languages and Styles

The tool supports the following languages and styles (as emitted by the `list` command):

```text
--languages options:
styles: 
├── asaql: Azure Stream Analytics
│   ├── dispatch: Azure Stream Analytics Query Dispatch
│   └── dispatchpayload: Azure Stream Analytics Query Dispatch with Payload
├── py: Python 3.9+
│   ├── mqttclient:
│   ├── ehconsumer: Python Azure Event Hubs Consumer
│   ├── ehproducer: Python Azure Event Hubs Producer
│   ├── kafkaconsumer: Python Apache Kafka Consumer
│   ├── kafkaproducer: Python Apache Kafka Producer
│   └── producer: Python Generic Producer
├── ts: JavaScript/TypeScript
│   ├── amqpconsumer: TypeScript AMQP 1.0 Consumer
│   ├── amqpproducer: TypeScript AMQP 1.0 Producer
│   ├── egproducer: TypeScript Azure Event Grid Producer
│   ├── ehproducer: TypeScript Azure Event Hubs Producer
│   ├── mqttclient: TypeScript MQTT 5.0 Client
│   ├── producerhttp: TypeScript HTTP Producer
│   ├── sbconsumer: TypeScript Azure Service Bus Consumer
│   ├── sbproducer: TypeScript Azure Service Bus Producer
│   ├── dashboard: TypeScript Dashboard
│   ├── ehconsumer: TypeScript Azure Event Hubs Consumer
│   ├── kafkaconsumer: TypeScript Apache Kafka Consumer
│   └── kafkaproducer: TypeScript Apache Kafka Producer
├── asyncapi: Async API 3.0
│   ├── consumer: AsyncAPI Consumer Definition
│   └── producer: AsyncAPI Producer Definition
├── openapi: Open API 3.0
│   ├── producer: OpenAPI Producer Definition
│   └── subscriber: OpenAPI Subscriber Definition
├── java: Java 21+
│   ├── amqpconsumer: Java AMQP 1.0 Consumer
│   ├── amqpjmsproducer: Java AMQP JMS Producer
│   ├── amqpproducer: Java AMQP 1.0 Producer
│   ├── ehconsumer: Java Azure Event Hubs Consumer
│   ├── ehproducer: Java Azure Event Hubs Producer
│   ├── kafkaconsumer: Java Apache Kafka Consumer
│   ├── kafkaproducer: Java Apache Kafka Producer
│   ├── mqttclient: Java MQTT 5.0 Client
│   ├── sbconsumer: Java Azure Service Bus Consumer
│   ├── sbproducer: Java Azure Service Bus Producer
│   ├── consumer: Java Generic Consumer
│   ├── producer: Java Generic Producer
│   ├── xconsumer: Java Generic Consumer (Extended)
│   └── xproducer: Java Generic Producer (Extended)
└── cs: C# / .NET 6.0+
    ├── egazfn: C# Azure Event Grid Azure Function
    ├── ehazfn: C# Azure Event Hubs Azure Function
    ├── sbazfn: C# Azure Service Bus Azure Function
    ├── amqpconsumer: C# AMQP 1.0 Consumer
    ├── amqpproducer: C# AMQP 1.0 Producer
    ├── egproducer: C# Azure Event Grid Producer
    ├── ehconsumer: C# Azure Event Hubs Consumer
    ├── ehproducer: C# Azure Event Hubs Producer
    ├── kafkaconsumer: C# Apache Kafka Consumer
    ├── kafkaproducer: C# Apache Kafka Producer
    ├── mqttclient: C# MQTT 5.0 Client
    ├── sbconsumer: C# Azure Service Bus Consumer
    └── sbproducer: C# Azure Service Bus Producer
```

There is a test suite that validates all templates.

##### OpenAPI

The tool can generate OpenAPI definitions for producer endpoints with:

```shell
xcg generate --language=openapi --style=producer --projectname=MyProjectProducer --definitions=definitions.json --output=MyProjectProducer
```

This will yield a `MyProjectProducer/MyProjectProducer.yml' file that can be used to generate a
producer client for the given endpoint.

Similarly, the tool can generate OpenAPI definitions for subscriber endpoints with:

```shell
xcg generate --language=openapi --style=subscriber --projectname=MyProjectSubscriber --definitions=definitions.json --output=MyProjectSubscriber
```

This will yield a `MyProjectSubscriber/MyProjectSubcriber.yml' file that can be
used to generate a subscriber server for the given endpoint, which is compatible
with the CloudEvents Subscription API.

##### AsyncAPI

The tool can generate AsyncAPI definitions with:

```shell
xcg generate --language=asyncapi --style=producer --projectname=MyProjectProducer --definitions=definitions.json --output=MyProjectProducer
```

For AsyncAPI, the tool support an extension parameter ce_content_mode that can be used to control the CloudEvents content mode of the generated AsyncAPI definition. The default is "structured" and the other supported value is "binary". The AsyncAPI template supports HTTP, MQTT, and AMQP 1.0 endpoints and injects the appropriate headers for the selected content mode for each protocol.

Use it like this:

```shell
xcg generate --language=asyncapi --style=producer --projectname=MyProjectProducer --definitions=definitions.json --output=MyProjectProducer --template-args ce_content_mode=binary
```

##### AMQP 1.0

The tool can generate AMQP 1.0 producer and consumer code for multiple languages (Java, C#, Python, TypeScript). The generated code works with any AMQP 1.0 compliant broker:

**Supported Brokers:**
- Apache ActiveMQ Artemis (native AMQP 1.0)
- Apache Qpid (native AMQP 1.0)
- Azure Service Bus (native AMQP 1.0)
- **RabbitMQ 4.0+** (native AMQP 1.0)
- **RabbitMQ 3.x** (via AMQP 1.0 plugin - requires plugin enablement)

**Using RabbitMQ:**

- **RabbitMQ 4.0+**: Native AMQP 1.0 support (no plugin required)
- **RabbitMQ 3.x**: Requires the AMQP 1.0 plugin to be enabled

For detailed setup instructions, including Docker deployment, connection configuration, and production best practices, see:

📖 **[RabbitMQ AMQP 1.0 Setup Guide](docs/rabbitmq_amqp_setup.md)**

Quick start with Docker:

**RabbitMQ 4.0+ (Recommended)**:
```bash
docker run -d --name rabbitmq-amqp \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:4-management
```

**RabbitMQ 3.x** (requires plugin):
```bash
docker run -d --name rabbitmq-amqp \
  -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_PLUGINS=rabbitmq_amqp1_0 \
  rabbitmq:3-management
```

Generate AMQP 1.0 clients:
```bash
# Java AMQP producer
xregistry generate --language=java --style=amqpproducer --projectname=MyProducer --definitions=definitions.json --output=./output

# C# AMQP consumer
xregistry generate --language=cs --style=amqpconsumer --projectname=MyConsumer --definitions=definitions.json --output=./output

# Python AMQP producer
xregistry generate --language=py --style=amqpproducer --projectname=MyProducer --definitions=definitions.json --output=./output

# TypeScript AMQP consumer
xregistry generate --language=ts --style=amqpconsumer --projectname=MyConsumer --definitions=definitions.json --output=./output
```

The generated code includes integration tests that work with ActiveMQ Artemis and both RabbitMQ 3.x (with plugin) and RabbitMQ 4.0+ (native support).

#### Custom Templates

The tool supports custom templates. Custom templates reside in a directory and are organized in subdirectories for each language and style. The directory structure is the same as the built-in templates. The tool will look for custom templates in the directories specified with the `--templates` option. Custom templates take precedence over built-in templates.

For more information on how to write custom templates, see [authoring templates](docs/authoring_templates.md).

If you are building a custom template that might be generally useful, submit a PR for includion into the built-in template set.

### Validate

The `validate` subcommand validates a definition file. The tool will report any errors in the definition file.

The `validate` command takes the following options:

| Option             | Description                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------- |
| `--definitions`    | The path to a local file or a URL to a file containing xRegistry definitions. |
| `--requestheaders` | Extra HTTP headers for HTTP requests to the given URL in the format `key=value`.         |

### List

The `list` subcommand lists the available language/style template sets.

## Community and Docs

Learn more about the people and organizations who are creating a dynamic cloud
native ecosystem by making our systems interoperable with CloudEvents.

- Our [Governance](https://github.com/xregistry/spec/docs/GOVERNANCE.md) documentation.
- [Contributing](https://github.com/xregistry/spec/docs/CONTRIBUTING.md) guidance.
- [Code of Conduct](https://github.com/cncf/foundation/blob/master/code-of-conduct.md)

### Communications

The main mailing list for e-mail communications:

- Send emails to: [cncf-cloudevents](mailto:cncf-cloudevents@lists.cncf.io)
- To subscribe see: <https://lists.cncf.io/g/cncf-cloudevents>
- Archives are at: <https://lists.cncf.io/g/cncf-cloudevents/topics>

And a #cloudevents Slack channel under
[CNCF's Slack workspace](http://slack.cncf.io/).

## License

[Apache 2.0](LICENSE)
