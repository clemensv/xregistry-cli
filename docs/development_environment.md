# Development environment

This project requires Python 3.10+ and several runtimes for testing generated
code.

For running the Python code you will need a working Python 3.10+ installation.
The prerequisites for the Python code are listed in the `requirements.txt` file.
You can install them with `pip`:

```shell
pip install -r requirements.txt
```

You need to install the following runtimes/SDKs separately:

* .NET SDK 6.0 or later
* OpenJDK 17 or later
* Node.js 14 or later

For running the (PyTest) tests you will need a working Docker installation for
hosting the Eclipse Mosquitto and ActiveMQ Artemis brokers during test runs, and
a set further tools for validating code generation ouptut:

- Azure Functions Core tools
- Async API CLI
- OpenAPI Generator CLI

```shell
npm install -g azure-functions-core-tools@4 --unsafe-perm true
npm install -g @asyncapi/cli
npm install -g @openapitools/openapi-generator-cli
```

## Running the tests

The tests are written using PyTest. You can run them with:

```shell    
pytest
```

## C# code generation dependencies

The generated code depends on the [.NET 6.0 SDK](https://dotnet.microsoft.com/en-us/download)

The generated C# code depends on an experimental extension to the C# CloudEvents SDK.

The extension is not yet available from NuGet, so you will need to build it yourself.

1. Create a new, local directory for the extension packages somewhere on
your local machine, then create an environment variable in your user profile
named `CEDISCO_NUGET_LOCAL_FEED` that points to this directory. 

1. Clone the repository: [https://github.com/clemensv/CloudNative.CloudEvents.Endpoints/](https://github.com/clemensv/CloudNative.CloudEvents.Endpoints/)

2. Build the project in the `source` directory with `dotnet build` and copy the resulting
packages from the `source/packages` directory into the directory you created in step 1.

## Java code generation dependencies

The generated code depends on [OpenJDK 17](https://learn.microsoft.com/en-us/java/openjdk/download)

The generated Java code depends on an experimental extension to the Java
CloudEvents SDK. Mind that the extension is not yet available from Maven
Central, so you will need to build it yourself. The implementation is also not
yet complete and several protocols are stubbed out, in part due to lack of
coverage by the CloudEvents Java SDK.

1. Clone the repository: [https://github.com/clemensv/io.cloudevents.experimental.endpoints](https://github.com/clemensv/io.cloudevents.experimental.endpoints)

2. Build the project with `mvn install` which will install the packages into your local Maven repository.

## TypeScript code generation dependencies

The generated code depends on [Node.js 14](https://nodejs.org/en/download/)
