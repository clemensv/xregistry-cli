# xRegistry CLI

[![Python Test](https://github.com/clemensv/xregistry-cli/actions/workflows/test.yml/badge.svg)](https://github.com/clemensv/xregistry-cli/actions/workflows/test.yml)
[![Python Release](https://github.com/clemensv/xregistry-cli/actions/workflows/build.yml/badge.svg)](https://github.com/clemensv/xregistry-cli/actions/workflows/build.yml)

> **NOTE**: However finished this project might look, this is currently just a prototype.
> **Do not use any of its output for any serious purpose at the moment.**

This project is a command line client for the xRegistry document format and API, with
a focus on generating code artifacts from xRegistry definitions, especially message catalogs.

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

## xRegistry Message Catalogs

xRegistry Message Catalogs are a set of registries that are built on top of
xRegistry and are designed to support the discovery and description of messaging
and eventing endpoints. The following catalogs are defined:

-   **Schema Catalog**: A registry for schemas that can be used to validate
    messages.
-   **Message Catalog**: A registry for message definitions that describe the
    structure of messages. Messages can be defined as abstract, transport
    neutral envelopes based on [CloudEvents](https://cloudevents.io) or as concrete
    messages that are bound to a specific transport protocol, whereby AMQP, HTTP, MQTT,
    and Apache Kafka are directly supported. Each message definition can associated
    with a schema from the schema catalog for describing the message payload.
-   **Endpoint Catalog**: A registry for endpoints that can be used to send or
    receive messages. Each endpoint can be associated with one or more groups of
    message definitions from the message catalog.

The three catalogs are designed to be used together, with the endpoint catalog
referring to message definition groups and message definitions referring to schemas.

You can study some examples of xRegistry Message Catalog documents in the
samples directory of this repository:

-   [**Contoso ERP**](samples/message-definitions/contoso-erp.xreg.json): A
    simple example of a message catalog for a fictional ERP system.
-   [**Inkjet Printer**](samples/message-definitions/inkjet.xreg.json): A
    fictitious group of events as they may be raised by an inkhet printer.
-   [**Fabrikam Motorsports**](samples/message-definitions/fabrikam-motorsports.xreg.json):
    An example for an event stream as it may be used in a motorsports telemetry
    scenario.
-   [**Vacuum Cleaner**](samples/message-definitions/vacuumcleaner.xreg.json):
    A fictitious group of events as they may be raised by a vacuum cleaner.

## Installation

The tool requires Python 3.10 or later. Until the tool is published in an
official package source (_this is a prototype, remember?_), you can install the
tool with pip directly from the repo:

```
pip install git+https://github.com/clemensv/cloudevents-registry-cli.git
```

If you want to develop locally and/or run the included tests follow the
instructions in [Development Environment](docs/development_environment.md).

## Usage

The tool is invoked as `xregistry` and supports the following subcommands:

- `xregistry generate`: Generate code
- `xregistry validate`: Validate a definition
- `xregistry list`: List available templates

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

```
--languages options:
styles:
├── asaql: Azure Stream Analytics
│   ├── dispatch: Azure Stream Analytics: Dispatch to outputs by CloudEvent type
│   └── dispatchpayload: Azure Stream Analytics: Dispatch to outputs by CloudEvent type
├── py: Python 3.9+
│   ├── ehconsumer: Python Event Hubs consumer class
│   ├── ehproducer: Python Event Hubs producer class
│   ├── kafkaconsumer: Python Apache Kafka consumer class
│   ├── kafkaproducer: Python Event Hubs producer class
│   └── producer: Python generic HTTP producer class
├── ts: JavaScript/TypeScript
│   └── producerhttp: JavaScript/TypeScript HTTP Producer
├── asyncapi: Async API 2.0
│   └── producer: Async API 2.0 Producer/Publisher
├── openapi: Open API 3.0
│   ├── producer: Open API 3.0 Producer
│   └── subscriber: Open API 3.0 Subscriber
├── java: Java 21+
│   ├── consumer: Java Experimental CloudEvents SDK endpoint consumer class
│   └── producer: Java Experimental CloudEvents SDK endpoint producer class
└── cs: C# / .NET 6.0+
    ├── egazfn: C# Azure Function with Azure Event Grid trigger
    ├── ehazfn: C# Azure Function with Azure Event Hubs trigger
    ├── sbazfn: C# Azure Function with Azure Service Bus trigger
    ├── amqpconsumer: C# CloudEvents SDK AMQP endpoint consumer class
    ├── amqpproducer: C# CloudEvents SDK AMQP endpoint producer class
    ├── egproducer: C# Azure Service Bus producer class
    ├── ehconsumer: C# Azure Event Hubs consumer
    ├── ehproducer: Azure Event Hubs producer class
    ├── kafkaconsumer: C# Apache Kafka consumer
    ├── kafkaproducer: Apache Kafka producer class
    ├── mqttclient: C# MQTT Client
    ├── sbconsumer: C# Azure Service Bus consumer
    └── sbproducer: Azure Service Bus producer class
```

Especially noteworthy might be the support for both AsyncAPI and OpenAPI.

##### OpenAPI

The tool can generate AsyncAPI definitions for producer endpoints with:

```shell
xregistry generate --language=openapi --style=producer --projectname=MyProjectProducer --definitions=definitions.json --output=MyProjectProducer
```

This will yield a `MyProjectProducer/MyProjectProducer.yml' file that can be used to generate a
producer client for the given endpoint.

Similarly, the tool can generate OpenAPI definitions for subscriber endpoints with:

```shell
xregistry generate --language=openapi --style=subscriber --projectname=MyProjectSubscriber --definitions=definitions.json --output=MyProjectSubscriber
```

This will yield a `MyProjectSubscriber/MyProjectSubcriber.yml' file that can be
used to generate a subscriber server for the given endpoint, which is compatible
with the CloudEvents Subscription API.

##### AsyncAPI

The tool can generate AsyncAPI definitions with:

```shell
xregistry generate --language=asyncapi --style=producer --projectname=MyProjectProducer --definitions=definitions.json --output=MyProjectProducer
```

For AsyncAPI, the tool support an extension parameter ce_content_mode that can be used to control the CloudEvents content mode of the generated AsyncAPI definition. The default is "structured" and the other supported value is "binary". The AsyncAPI template supports HTTP, MQTT, and AMQP 1.0 endpoints and injects the appropriate headers for the selected content mode for each protocol.

Use it like this:

```shell
xregistry generate --language=asyncapi --style=producer --projectname=MyProjectProducer --definitions=definitions.json --output=MyProjectProducer --template-args ce_content_mode=binary
```

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

- Our [Governance](https://github.com/cloudevents/spec/docs/GOVERNANCE.md) documentation.
- [Contributing](https://github.com/cloudevents/spec/docs/CONTRIBUTING.md) guidance.
- [Code of Conduct](https://github.com/cncf/foundation/blob/master/code-of-conduct.md)

### Communications

The main mailing list for e-mail communications:

- Send emails to: [cncf-cloudevents](mailto:cncf-cloudevents@lists.cncf.io)
- To subscribe see: https://lists.cncf.io/g/cncf-cloudevents
- Archives are at: https://lists.cncf.io/g/cncf-cloudevents/topics

And a #cloudevents Slack channel under
[CNCF's Slack workspace](http://slack.cncf.io/).

## License

[Apache 2.0](LICENSE)
