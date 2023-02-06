# Development environment

This project requires Python 3.10+ and Node.js 14+.

## Python

For running the Python code you will need a working Python 3.10+ installation. The prerequisites for the Python code are listed in the `requirements.txt` file. You can install them with `pip`:

```shell
pip install -r requirements.txt
```

For running the (PyTest) tests you will need a working Docker installation for hosting the Eclipse Mosquitto and ActiveMQ Artemis brokers during test runs, and a set further tools for validating code generation ouptut:

- Azure Functions Core tools
- Async API CLI
- OpenAPI Generator CLI

```shell
npm install -g azure-functions-core-tools@4 --unsafe-perm true
npm install -g @asyncapi/cli
npm install -g @openapitools/openapi-generator-cli
```

