# CloudEvents Registry CLI

[![Python Test](https://github.com/clemensv/cedisco-codegen/actions/workflows/test.yml/badge.svg)](https://github.com/clemensv/cedisco-codegen/actions/workflows/test.yml)
[![Python Release](https://github.com/clemensv/cedisco-codegen/actions/workflows/build.yml/badge.svg)](https://github.com/clemensv/cedisco-codegen/actions/workflows/build.yml)


> **NOTE**: However finished this project might look, this is currently just a prototype.
> **Do not use any of its output for any serious purpose at the moment.**

This project is a command line client for the *CloudEvents Registry*.

* [Introduction](#introduction)
* [Installation](#installation)
* [Usage](#usage)


## Introduction

The CloudEvents Registry is an API and a file format for describing messaging
and eventing endpoints, groups of message definitions, and payload schemas. The
formal specification is available at
[https://github.com/cloudevents/spec/blob/main/registry/spec.md](https://github.com/cloudevents/spec/blob/main/registry/spec.md).

While the CloudEvents Registry emerged from the CNCF CloudEvents project and has
been designed for enabling robust development of CloudEvents-based flows, the
registry is not limited to CloudEvents. It can be used to describe any
asynchronous messaging or eventing endpoint, including such that do not use
CloudEvents at all. This repository even contains a few examples of such
definitions for AMQP and MQTT based flows.

The file format has the extension `.disco` (from "discovery") and is a JSON
file. The tooling can also handle YAML files with an equivalent structure with a
`.disco.yaml` extension. This CLI tool can be used to generate code from a
`.disco` file, or to validate a `.disco` file against the formal specification.

### A .disco file

A `.disco` file is a JSON or YAML file that describes a set of messaging
constructs. We will briefly describe the structure of a `.disco` file here for
context, but the formal specification is the authoritative source for the
structure.

The top-level of a `.disco` file declares the schema and version of the specification:

```json
{
    "$schema": "https://cloudevents.io/schemas/registry",
    "specversion": "0.3-wip",
```

The endpoints section describes *producer*, *consumer*, and/or *subscriber*
endpoints, named for the communication path they realize. The example shows a
producer endpoint that uses HTTP for publishing CloudEvents. The endpoint is
configured to use the `Contoso.ERP.Events` group of message definitions, and the
`CloudEvents/1.0` format.

Any endpoint can be seen from different perspectives: For a *producer* endpoint, there
is the application from which events originate and the destination to which
events are sent. For a *consumer* endpoint, there is the application which
handles events and the source from which events are retrieved. For a
*subscriber* endpoint, there is the application which handles arriving events
and the source which sends them. There might also be further perspectives such
as pipeline stages for pre-/post-processing, etc.

The endpoint configuration describes the communication channel to which these
perspectives apply. A code generator can use this information to generate code
for a specific perspective using different templates.

```json
    "endpoints" : {
        "myendpoint" : {
            "type": "endpoint",
            "id" : "myendpoint",
            "usage": "producer",
            "config": {
                "protocol": "HTTP",
                "strict": false,
                "endpoints": [
                    "https://cediscoveryinterop.azurewebsites.net/registry/subscriptions"
                ]
            },
            "groups": [
                "#/groups/Contoso.ERP.Events"
            ],
            "format" : "CloudEvents/1.0"
        }
    },
```

The groups section describes groups of message definitions. The example shows a group of
CloudEvents message definitions with just one entry. The message definition
describes the CloudEvent message type `Contoso.ERP.Events.ReservationPlaced`,
which is a CloudEvent with a `time` attribute, a `source` attribute, and a
`data` attribute that refers to the `orderData` schema. The schema is defined in
the `schemagroups` section below.

```json

    "groups": {
        "Contoso.ERP.Events": {
            "type": "group",
            "id": "Contoso.ERP.Events",
            "definitions": {
                "Contoso.ERP.Events.ReservationPlaced": {
                    "type": "cloudevent",
                    "id": "Contoso.ERP.Events.ReservationPlaced",
                    "description": "A reservation has been placed",
                    "format": "CloudEvents/1.0",
                    "metadata": {
                        "attributes": {
                            "id": {
                                "type": "string",
                                "required": true
                            },
                            "type": {
                                "type": "string",
                                "value": "Contoso.ERP.Events.ReservationPlaced",
                                "required": true
                            },
                            "time": {
                                "type": "datetime",
                                "required": true
                            },
                            "source": {
                                "type": "uritemplate",
                                "value": "/erp/orders",
                                "required": true
                            }
                        }
                    },
                    "schemaurl": "#/schemagroups/Contoso.ERP.Events/schemas/orderData"
                }
            }
        }
    },
```

The *schemagroups* section describes groups of schemas. The example shows a
group of JSON schemas with just one entry having a single version. The schema is
used by the message definition above. Note that the schema is defined in the
same file in this example, but it could also be defined in a separate file and
referenced by URL, with a "schemaurl" property replacing the "schema" property.

```json
    "schemagroups": {
        "Contoso.ERP.Events": {
            "type": "schemagroup",
            "id": "Contoso.ERP.Events",
            "schemas": {
                "orderData": {
                    "type": "schema",
                    "id": "orderData",
                    "format": "JsonSchema/draft-07",
                    "versions": {
                        "1": {
                            "type": "schemaversion",
                            "id": "1",
                            "format": "JsonSchema/draft-07",
                            "schema": {
                                "$schema": "http://json-schema.org/draft-07/schema",
                                "type": "object",
                                "properties": {
                                    "orderId": {
                                        "type": "string"
                                    },
                                    "customerId": {
                                        "type": "string"
                                    },
                                    "total": {
                                        "type": "number"
                                    },
                                    "items": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "productId": {
                                                    "type": "string"
                                                },
                                                "quantity": {
                                                    "type": "number"
                                                },
                                                "price": {
                                                    "type": "number"
                                                }
}   }   }   }   }   }   }   }   }   }   }   }
```

## Installation

The tool requires Python 3.10 or later. Until the tool is published in an official package source (*this is a prototype, remember?*), you can install the tool with pip directly from the repo:

```
pip install git+https://github.com/clemensv/cedisco-codegen.git
```

If you want to develop locally and/or run the included tests follow the instructions in [DEVELOP.md](DEVELOP.md).

## Usage

The tool is invoked as `ceregistry` and supports the following subcommands:
- `ceregistry generate`:  Generate code
- `ceregistry validate`:  Validate a definition
- `ceregistry list`: List available templates

### Generate

The `generate` subcommand generates code from a definition file. The tool includes a set of built-in language/style template sets that can be enumerated with the [List](#list) command.

The `generate` command takes the following options:	

| Option | Description |
| --- | --- |
| `--projectname` | **Required** The project name (namespace name) for the generated code. |
| `--language` | **Required**  The shorthand code of the language to use for the generated code, for instance "cs" for C# or "ts" for TypeScript/JavaScript. See [Languages](#languages-and-styles). |
| `--style` | The code style. This selects one of the template sets available for the given language, for instance "producer". See [Styles](#languages-and-styles)|
| `--output` | The directory where the generated code will be saved. The generator will overwrite existing files in this directory. |
| `--definitions` | The path to a local file or a URL to a file containing CloudEvents Registry definitions. |
| `--requestheaders` | Extra HTTP headers for HTTP requests to the given URL in the format `key=value`. |
| `--templates` | Paths of extra directories containing custom templates See [Custom Templates]. |
| `--template-args` | Extra template arguments to pass to the code generator in the form `key=value`. |

#### Languages and Styles

The tool supports the following languages and styles (as emitted by the `list` command):

```
├── asaql: Azure Stream Analytics
│   ├── dispatch: Azure Stream Analytics: Dispatch to outputs by CloudEvent type
│   └── dispatchpayload: Azure Stream Analytics: Dispatch to outputs by CloudEvent type
├── asyncapi: Async API 2.0
│   └── producer: Async API 2.0 Producer/Publisher
├── cs: C# / .NET 6.0+
│   ├── azfunctioneventgrid: C# Azure Function with Azure Event Grid trigger
│   ├── azfunctioneventhubs: C# Azure Function with Azure Event Hubs trigger
│   ├── azfunctionhttp: C# Azure Function with HTTP trigger
│   ├── azfunctionservicebus: C# Azure Function with Azure Service Bus trigger
│   ├── consumer: C# CloudEvents SDK endpoint consumer class
│   └── producer: C# CloudEvents SDK endpoint producer class
├── java: Java 13+
│   ├── consumer: Java CloudEvents SDK endpoint consumer class
│   └── producer: Java CloudEvents SDK endpoint producer class
├── openapi: Open API 3.0
│   ├── producer: Open API 3.0 Producer
│   └── subscriber: Open API 3.0 Subscriber
├── py: Python 3.9+
│   └── <DirEntry 'producer'>
└── ts: JavaScript/TypeScript
    └── producerhttp: JavaScript/TypeScript HTTP Producer
```

#### Custom Templates

The tool supports custom templates. Custom templates reside in a directory and are organized in subdirectories for each language and style. The directory structure is the same as the built-in templates. The tool will look for custom templates in the directories specified with the `--templates` option. Custom templates take precedence over built-in templates.

For more information on how to write custom templates, see [authoring templates](docs/authoring_templates.md).

If you are building a custom template that might be generally useful, submit a PR for includion into the built-in template set.

### Validate

The `validate` subcommand validates a definition file. The tool will report any errors in the definition file.

The `validate` command takes the following options:

| Option | Description |
| --- | --- |
| `--definitions` | The path to a local file or a URL to a file containing CloudEvents Registry definitions. |
| `--requestheaders` | Extra HTTP headers for HTTP requests to the given URL in the format `key=value`. |

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