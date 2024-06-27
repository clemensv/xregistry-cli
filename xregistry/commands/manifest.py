import json
import argparse
from pathlib import Path
from typing import List, Optional, Any

class ManifestSubcommands:
    def __init__(self, filename: str):
        """
        Initialize the ManifestSubcommands class.

        Args:
            filename (str): The name of the manifest file.
        """
        self.filename = filename
        self.load_manifest()

    def load_manifest(self):
        """
        Load the manifest file. If the file does not exist, initialize an empty manifest.
        """
        if Path(self.filename).exists():
            with open(self.filename, 'r', encoding='utf-8') as file:
                self.manifest = json.load(file)
        else:
            self.manifest = {
                "$schema": "https://cloudevents.io/schemas/registry",
                "specversion": "0.5-wip",
                "endpoints": {},
                "messagegroups": {},
                "schemagroups": {}
            }

    def save_manifest(self):
        """
        Save the current state of the manifest to the file.
        """
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump(self.manifest, file, indent=4)

    def init_manifest(self):
        """
        Initialize a new manifest with empty collections for endpoints, messagegroups, and schemagroups.
        """
        self.manifest = {
            "$schema": "https://cloudevents.io/schemas/registry",
            "specversion": "0.5-wip",
            "endpoints": {},
            "messagegroups": {},
            "schemagroups": {}
        }
        self.save_manifest()

    def add_endpoint(self, endpoint_id: str, usage: str, protocol: Optional[str], deployed: Optional[bool], 
                     endpoints: List[str], options: Optional[List[str]], 
                     messagegroups: Optional[List[str]], documentation: Optional[str], 
                     description: Optional[str], labels: Optional[List[str]], name: Optional[str]):
        """
        Add an endpoint to the manifest.

        Args:
            endpoint_id (str): The unique identifier for the endpoint.
            usage (str): The usage type of the endpoint (subscriber, producer, or consumer).
            protocol (Optional[str]): The protocol used by the endpoint (HTTP, AMQP, MQTT, Kafka, or NATS).
            deployed (Optional[bool]): Whether the endpoint is deployed.
            endpoints (List[str]): A list of endpoint URIs.
            options (Optional[List[str]]): A list of key=value pairs for endpoint options.
            messagegroups (Optional[List[str]]): A list of message group identifiers.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the endpoint.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the endpoint.
        """
        if endpoint_id in self.manifest['endpoints']:
            raise ValueError(f"Endpoint with id {endpoint_id} already exists.")
        endpoint = {
            "id": endpoint_id,
            "usage": usage.capitalize(),
            "config": {
                "endpoints": [{"uri": uri} for uri in endpoints]
            }
        }
        if protocol:
            endpoint['config']['protocol'] = protocol.upper()
        if deployed is not None:
            endpoint['config']['deployed'] = deployed
        if options:
            endpoint['config']['options'] = dict(kv.split('=') for kv in options)
        if messagegroups:
            endpoint['messagegroups'] = messagegroups
        if documentation:
            endpoint['documentation'] = documentation
        if description:
            endpoint['description'] = description
        if labels:
            endpoint['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            endpoint['name'] = name
        self.manifest['endpoints'][endpoint_id] = endpoint
        self.save_manifest()

    def remove_endpoint(self, endpoint_id: str):
        """
        Remove an endpoint from the manifest.

        Args:
            endpoint_id (str): The unique identifier for the endpoint to be removed.
        """
        if endpoint_id not in self.manifest['endpoints']:
            raise ValueError(f"Endpoint with id {endpoint_id} does not exist.")
        del self.manifest['endpoints'][endpoint_id]
        self.save_manifest()

    def edit_endpoint(self, endpoint_id: str, usage: Optional[str], protocol: Optional[str], deployed: Optional[bool], 
                      endpoints: Optional[List[str]], options: Optional[List[str]], 
                      messagegroups: Optional[List[str]], documentation: Optional[str], 
                      description: Optional[str], labels: Optional[List[str]], name: Optional[str]):
        """
        Edit an existing endpoint in the manifest.

        Args:
            endpoint_id (str): The unique identifier for the endpoint.
            usage (Optional[str]): The usage type of the endpoint (subscriber, producer, or consumer).
            protocol (Optional[str]): The protocol used by the endpoint (HTTP, AMQP, MQTT, Kafka, or NATS).
            deployed (Optional[bool]): Whether the endpoint is deployed.
            endpoints (Optional[List[str]]): A list of endpoint URIs.
            options (Optional[List[str]]): A list of key=value pairs for endpoint options.
            messagegroups (Optional[List[str]]): A list of message group identifiers.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the endpoint.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the endpoint.
        """
        if endpoint_id not in self.manifest['endpoints']:
            raise ValueError(f"Endpoint with id {endpoint_id} does not exist.")
        endpoint = self.manifest['endpoints'][endpoint_id]
        if usage:
            endpoint['usage'] = usage.capitalize()
        if protocol:
            endpoint['config']['protocol'] = protocol.upper()
        if deployed is not None:
            endpoint['config']['deployed'] = deployed
        if endpoints:
            endpoint['config']['endpoints'] = [{"uri": uri} for uri in endpoints]
        if options:
            endpoint['config']['options'] = dict(kv.split('=') for kv in options)
        if messagegroups:
            endpoint['messagegroups'] = messagegroups
        if documentation:
            endpoint['documentation'] = documentation
        if description:
            endpoint['description'] = description
        if labels:
            endpoint['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            endpoint['name'] = name
        self.save_manifest()

    def add_messagegroup(self, group_id: str, format: Optional[str], documentation: Optional[str], 
                         description: Optional[str], labels: Optional[List[str]], name: Optional[str]):
        """
        Add a message group to the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            format (Optional[str]): The format of the message group (CloudEvents or None).
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the message group.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the message group.
        """
        if group_id not in self.manifest['messagegroups']:
            messagegroup = {
                "id": group_id,
                "messages": {}
            }
            if format:
                messagegroup['format'] = format.capitalize()
            if documentation:
                messagegroup['documentation'] = documentation
            if description:
                messagegroup['description'] = description
            if labels:
                messagegroup['labels'] = dict(kv.split('=') for kv in labels)
            if name:
                messagegroup['name'] = name
            self.manifest['messagegroups'][group_id] = messagegroup
            self.save_manifest()
        else:
            raise ValueError(f"Message group with id {group_id} already exists.")

    def remove_messagegroup(self, group_id: str):
        """
        Remove a message group from the manifest.

        Args:
            group_id (str): The unique identifier for the message group to be removed.
        """
        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        del self.manifest['messagegroups'][group_id]
        self.save_manifest()

    def edit_messagegroup(self, group_id: str, format: Optional[str], documentation: Optional[str], 
                          description: Optional[str], labels: Optional[List[str]], name: Optional[str]):
        """
        Edit an existing message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            format (Optional[str]): The format of the message group (CloudEvents or None).
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the message group.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the message group.
        """
        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if format:
            messagegroup['format'] = format.capitalize()
        if documentation:
            messagegroup['documentation'] = documentation
        if description:
            messagegroup['description'] = description
        if labels:
            messagegroup['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            messagegroup['name'] = name
        self.save_manifest()

    def add_message(self, group_id: str, message_id: str, format: Optional[str], binding: Optional[str], 
                    schemaformat: Optional[str], schemagroup: Optional[str], schemaid: Optional[str], 
                    schemaurl: Optional[str], documentation: Optional[str], 
                    description: Optional[str], labels: Optional[List[str]], name: Optional[str]):
        """
        Add a message to a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            format (Optional[str]): The format of the message (CloudEvents or None).
            binding (Optional[str]): The binding of the message (AMQP, MQTT, NATS, HTTP, Kafka, or None).
            schemaformat (Optional[str]): The schema format of the message.
            schemagroup (Optional[str]): The schema group identifier.
            schemaid (Optional[str]): The schema identifier.
            schemaurl (Optional[str]): The URL of the schema.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the message.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the message.
        """
        if group_id not in self.manifest['messagegroups']:
            self.add_messagegroup(group_id, None, None, None, None, None)
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} already exists in group {group_id}.")
        message = {
            "id": message_id
        }
        if format:
            message['format'] = format.capitalize()
            if format.lower() != 'none':
                message['metadata'] = {}
        if binding:
            message['binding'] = binding.capitalize()
            if binding.lower() != 'none':
                message['message'] = {}
        if schemaformat:
            message['schemaformat'] = schemaformat
        if schemagroup and schemaid:
            message['schemaurl'] = f"#/schemagroups/{schemagroup}/schemas/{schemaid}"
        elif schemaurl:
            message['schemaurl'] = schemaurl
        if documentation:
            message['documentation'] = documentation
        if description:
            message['description'] = description
        if labels:
            message['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            message['name'] = name
        messagegroup['messages'][message_id] = message
        self.save_manifest()

    def remove_message(self, group_id: str, message_id: str):
        """
        Remove a message from a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message to be removed.
        """
        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        del messagegroup['messages'][message_id]
        self.save_manifest()

    def edit_message(self, group_id: str, message_id: str, format: Optional[str], binding: Optional[str], 
                     schemaformat: Optional[str], schemagroup: Optional[str], schemaid: Optional[str], 
                     schemaurl: Optional[str], documentation: Optional[str], 
                     description: Optional[str], labels: Optional[List[str]], name: Optional[str]):
        """
        Edit an existing message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            format (Optional[str]): The format of the message (CloudEvents or None).
            binding (Optional[str]): The binding of the message (AMQP, MQTT, NATS, HTTP, Kafka, or None).
            schemaformat (Optional[str]): The schema format of the message.
            schemagroup (Optional[str]): The schema group identifier.
            schemaid (Optional[str]): The schema identifier.
            schemaurl (Optional[str]): The URL of the schema.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the message.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the message.
        """
        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if format:
            message['format'] = format.capitalize()
            if format.lower() != 'none' and 'metadata' not in message:
                message['metadata'] = {}
        if binding:
            message['binding'] = binding.capitalize()
            if binding.lower() != 'none' and 'message' not in message:
                message['message'] = {}
        if schemaformat:
            message['schemaformat'] = schemaformat
        if schemagroup and schemaid:
            message['schemaurl'] = f"#/schemagroups/{schemagroup}/schemas/{schemaid}"
        elif schemaurl:
            message['schemaurl'] = schemaurl
        if documentation:
            message['documentation'] = documentation
        if description:
            message['description'] = description
        if labels:
            message['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            message['name'] = name
        self.save_manifest()

    def add_schemagroup(self, group_id: str, documentation: Optional[str], description: Optional[str], 
                        labels: Optional[List[str]], name: Optional[str]):
        """
        Add a schema group to the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the schema group.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the schema group.
        """
        if group_id in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} already exists.")
        schemagroup = {
            "id": group_id,
            "schemas": {}
        }
        if documentation:
            schemagroup['documentation'] = documentation
        if description:
            schemagroup['description'] = description
        if labels:
            schemagroup['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            schemagroup['name'] = name
        self.manifest['schemagroups'][group_id] = schemagroup
        self.save_manifest()

    def remove_schemagroup(self, group_id: str):
        """
        Remove a schema group from the manifest.

        Args:
            group_id (str): The unique identifier for the schema group to be removed.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        del self.manifest['schemagroups'][group_id]
        self.save_manifest()

    def edit_schemagroup(self, group_id: str, documentation: Optional[str], description: Optional[str], 
                         labels: Optional[List[str]], name: Optional[str]):
        """
        Edit an existing schema group in the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the schema group.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the schema group.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        schemagroup = self.manifest['schemagroups'][group_id]
        if documentation:
            schemagroup['documentation'] = documentation
        if description:
            schemagroup['description'] = description
        if labels:
            schemagroup['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            schemagroup['name'] = name
        self.save_manifest()

    def add_schema(self, group_id: str, schema_id: str, format: str, version_id: Optional[str], schema: Optional[str], 
                   schemaimport: Optional[str], schemaurl: Optional[str], documentation: Optional[str], 
                   description: Optional[str], labels: Optional[List[str]], name: Optional[str]):
        """
        Add a schema to a schema group in the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            schema_id (str): The unique identifier for the schema.
            format (str): The format of the schema (JSONSchema, XSD, Avro, Protobuf).
            version_id (Optional[str]): The version identifier for the schema.
            schema (Optional[str]): The literal schema string.
            schemaimport (Optional[str]): The file location or URL to import the schema from.
            schemaurl (Optional[str]): The URL of the schema.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the schema.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the schema.
        """
        if group_id not in self.manifest['schemagroups']:
            self.add_schemagroup(group_id, None, None, None, None)
        schemagroup = self.manifest['schemagroups'][group_id]
        if schema_id not in schemagroup['schemas']:
            schemagroup['schemas'][schema_id] = {"versions": {}}
        schema_entry = schemagroup['schemas'][schema_id]
        if version_id in schema_entry['versions']:
            raise ValueError(f"Schema version {version_id} already exists in group {group_id} schema {schema_id}.")
        version_entry = {
            "id": version_id if version_id else "1",
            "format": format
        }
        if schema:
            try:
                version_entry['schema'] = json.loads(schema)
            except json.JSONDecodeError:
                version_entry['schemabase64'] = schema
        elif schemaimport:
            # Placeholder for importing schema from file or URL
            version_entry['schemaimport'] = schemaimport
        elif schemaurl:
            version_entry['schemaurl'] = schemaurl
        if documentation:
            version_entry['documentation'] = documentation
        if description:
            version_entry['description'] = description
        if labels:
            version_entry['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            version_entry['name'] = name
        schema_entry['versions'][version_entry['id']] = version_entry
        self.save_manifest()

    def remove_schema(self, group_id: str, schema_id: str, version_id: Optional[str] = None):
        """
        Remove a schema from a schema group in the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            schema_id (str): The unique identifier for the schema.
            version_id (Optional[str]): The version identifier for the schema to be removed.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        schemagroup = self.manifest['schemagroups'][group_id]
        if schema_id not in schemagroup['schemas']:
            raise ValueError(f"Schema {schema_id} does not exist in group {group_id}.")
        if version_id:
            if version_id not in schemagroup['schemas'][schema_id]['versions']:
                raise ValueError(f"Schema version {version_id} does not exist in group {group_id} schema {schema_id}.")
            del schemagroup['schemas'][schema_id]['versions'][version_id]
            if not schemagroup['schemas'][schema_id]['versions']:
                del schemagroup['schemas'][schema_id]
        else:
            del schemagroup['schemas'][schema_id]
        self.save_manifest()

    def edit_schema(self, group_id: str, schema_id: str, version_id: str, format: Optional[str], schema: Optional[str], 
                    schemaimport: Optional[str], schemaurl: Optional[str], documentation: Optional[str], 
                    description: Optional[str], labels: Optional[List[str]], name: Optional[str], y: Optional[bool]):
        """
        Edit an existing schema in a schema group in the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            schema_id (str): The unique identifier for the schema.
            version_id (str): The version identifier for the schema.
            format (Optional[str]): The format of the schema (JSONSchema, XSD, Avro, Protobuf).
            schema (Optional[str]): The literal schema string.
            schemaimport (Optional[str]): The file location or URL to import the schema from.
            schemaurl (Optional[str]): The URL of the schema.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the schema.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the schema.
            y (Optional[bool]): Suppress confirmation prompt if True.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        schemagroup = self.manifest['schemagroups'][group_id]
        if schema_id not in schemagroup['schemas']:
            raise ValueError(f"Schema {schema_id} does not exist in group {group_id}.")
        schema_entry = schemagroup['schemas'][schema_id]
        if version_id not in schema_entry['versions']:
            raise ValueError(f"Schema version {version_id} does not exist in group {group_id} schema {schema_id}.")
        if not y:
            confirm = input("It is not recommended to edit schema versions, but rather add revisions of schemas to the version history. Do you want to proceed? (y/N): ")
            if confirm.lower() != 'y':
                return
        version_entry = schema_entry['versions'][version_id]
        if format:
            version_entry['format'] = format
        if schema:
            try:
                version_entry['schema'] = json.loads(schema)
            except json.JSONDecodeError:
                version_entry['schemabase64'] = schema
        elif schemaimport:
            # Placeholder for importing schema from file or URL
            version_entry['schemaimport'] = schemaimport
        elif schemaurl:
            version_entry['schemaurl'] = schemaurl
        if documentation:
            version_entry['documentation'] = documentation
        if description:
            version_entry['description'] = description
        if labels:
            version_entry['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            version_entry['name'] = name
        self.save_manifest()

    def set_default_version(self, group_id: str, schema_id: str, version_id: str):
        """
        Set the default version for a schema in a schema group.

        Args:
            group_id (str): The unique identifier for the schema group.
            schema_id (str): The unique identifier for the schema.
            version_id (str): The version identifier to set as default.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        schemagroup = self.manifest['schemagroups'][group_id]
        if schema_id not in schemagroup['schemas']:
            raise ValueError(f"Schema {schema_id} does not exist in group {group_id}.")
        schema_entry = schemagroup['schemas'][schema_id]
        if version_id not in schema_entry['versions']:
            raise ValueError(f"Schema version {version_id} does not exist in group {group_id} schema {schema_id}.")
        schema_entry['defaultversionid'] = version_id
        self.save_manifest()

    def add_parsers(self, manifest_subparsers: Any):
        """
        Add subparsers for the manifest commands.

        Args:
            manifest_subparsers (Any): The subparsers object to add parsers to.
        """
        init_parser = manifest_subparsers.add_parser("init", help="Initialize a new manifest file")
        init_parser.add_argument("filename", help="Manifest file name")
        init_parser.set_defaults(func=lambda args: ManifestSubcommands(args.filename).init_manifest())

        endpoint_parser = manifest_subparsers.add_parser("endpoint", help="Manage endpoints")
        endpoint_subparsers = endpoint_parser.add_subparsers(dest="endpoint_command", help="Endpoint commands")

        endpoint_add = endpoint_subparsers.add_parser("add", help="Add an endpoint")
        endpoint_add.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_add.add_argument("--usage", required=True, choices=["subscriber", "producer", "consumer"], help="Endpoint usage")
        endpoint_add.add_argument("--protocol", choices=["HTTP", "AMQP", "MQTT", "Kafka", "NATS"], help="Endpoint protocol")
        endpoint_add.add_argument("--deployed", action='store_true', help="Is the endpoint deployed")
        endpoint_add.add_argument("--endpoints", nargs='+', required=True, help="Endpoint URIs")
        endpoint_add.add_argument("--options", nargs='*', help="Endpoint options as key=value pairs")
        endpoint_add.add_argument("--messagegroups", nargs='+', help="Message group IDs")
        endpoint_add.add_argument("--documentation", help="Documentation URL")
        endpoint_add.add_argument("--description", help="Description string")
        endpoint_add.add_argument("--labels", nargs='*', help="Labels as key=value pairs")
        endpoint_add.add_argument("--name", help="Human-readable name")
        endpoint_add.add_argument("filename", help="Manifest file name")
        endpoint_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_endpoint(
            args.id, args.usage, args.protocol, args.deployed, args.endpoints, args.options,
            args.messagegroups, args.documentation, args.description, args.labels, args.name
        ))

        endpoint_remove = endpoint_subparsers.add_parser("remove", help="Remove an endpoint")
        endpoint_remove.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_remove.add_argument("filename", help="Manifest file name")
        endpoint_remove.set_defaults(func=lambda args: ManifestSubcommands(args.filename).remove_endpoint(args.id))

        endpoint_edit = endpoint_subparsers.add_parser("edit", help="Edit an endpoint")
        endpoint_edit.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_edit.add_argument("--usage", choices=["subscriber", "producer", "consumer"], help="Endpoint usage")
        endpoint_edit.add_argument("--protocol", choices=["HTTP", "AMQP", "MQTT", "Kafka", "NATS"], help="Endpoint protocol")
        endpoint_edit.add_argument("--deployed", action='store_true', help="Is the endpoint deployed")
        endpoint_edit.add_argument("--endpoints", nargs='+', help="Endpoint URIs")
        endpoint_edit.add_argument("--options", nargs='*', help="Endpoint options as key=value pairs")
        endpoint_edit.add_argument("--messagegroups", nargs='+', help="Message group IDs")
        endpoint_edit.add_argument("--documentation", help="Documentation URL")
        endpoint_edit.add.argument("--description", help="Description string")
        endpoint_edit.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        endpoint_edit.add.argument("--name", help="Human-readable name")
        endpoint_edit.add.argument("filename", help="Manifest file name")
        endpoint_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_endpoint(
            args.id, args.usage, args.protocol, args.deployed, args.endpoints, args.options,
            args.messagegroups, args.documentation, args.description, args.labels, args.name
        ))

        messagegroup_parser = manifest_subparsers.add_parser("messagegroup", help="Manage message groups")
        messagegroup_subparsers = messagegroup_parser.add_subparsers(dest="messagegroup_command", help="Message group commands")

        messagegroup_add = messagegroup_subparsers.add_parser("add", help="Add a message group")
        messagegroup_add.add.argument("--id", required=True, help="Message group ID")
        messagegroup_add.add.argument("--format", choices=["CloudEvents", "None"], help="Message group format")
        messagegroup_add.add.argument("--documentation", help="Documentation URL")
        messagegroup_add.add.argument("--description", help="Description string")
        messagegroup_add.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        messagegroup_add.add.argument("--name", help="Human-readable name")
        messagegroup_add.add.argument("filename", help="Manifest file name")
        messagegroup_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_messagegroup(
            args.id, args.format, args.documentation, args.description, args.labels, args.name
        ))

        messagegroup_remove = messagegroup_subparsers.add_parser("remove", help="Remove a message group")
        messagegroup_remove.add.argument("--id", required=True, help="Message group ID")
        messagegroup_remove.add.argument("filename", help="Manifest file name")
        messagegroup_remove.set_defaults(func=lambda args: ManifestSubcommands(args.filename).remove_messagegroup(args.id))

        messagegroup_edit = messagegroup_subparsers.add_parser("edit", help="Edit a message group")
        messagegroup_edit.add.argument("--id", required=True, help="Message group ID")
        messagegroup_edit.add.argument("--format", choices=["CloudEvents", "None"], help="Message group format")
        messagegroup_edit.add.argument("--documentation", help="Documentation URL")
        messagegroup_edit.add.argument("--description", help="Description string")
        messagegroup_edit.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        messagegroup_edit.add.argument("--name", help="Human-readable name")
        messagegroup_edit.add.argument("filename", help="Manifest file name")
        messagegroup_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_messagegroup(
            args.id, args.format, args.documentation, args.description, args.labels, args.name
        ))

        message_add = messagegroup_subparsers.add_parser("message", help="Manage messages in a message group")
        message_subparsers = message_add.add_subparsers(dest="message_command", help="Message commands")

        message_add_sub = message_subparsers.add_parser("add", help="Add a message to a message group")
        message_add_sub.add.argument("--groupid", required=True, help="Message group ID")
        message_add_sub.add.argument("--id", required=True, help="Message ID")
        message_add_sub.add.argument("--format", choices=["CloudEvents", "None"], help="Message format")
        message_add_sub.add.argument("--binding", choices=["AMQP", "MQTT", "NATS", "HTTP", "Kafka", "None"], help="Message binding")
        message_add_sub.add.argument("--schemaformat", help="Schema format")
        message_add_sub.add.argument("--schemagroup", help="Schema group ID")
        message_add_sub.add.argument("--schemaid", help="Schema ID")
        message_add_sub.add.argument("--schemaurl", help="Schema URL")
        message_add_sub.add.argument("--documentation", help="Documentation URL")
        message_add_sub.add.argument("--description", help="Description string")
        message_add_sub.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        message_add_sub.add.argument("--name", help="Human-readable name")
        message_add_sub.add.argument("filename", help="Manifest file name")
        message_add_sub.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_message(
            args.groupid, args.id, args.format, args.binding, args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name
        ))

        message_remove = message_subparsers.add_parser("remove", help="Remove a message from a message group")
        message_remove.add.argument("--groupid", required=True, help="Message group ID")
        message_remove.add.argument("--id", required=True, help="Message ID")
        message_remove.add.argument("filename", help="Manifest file name")
        message_remove.set_defaults(func=lambda args: ManifestSubcommands(args.filename).remove_message(args.groupid, args.id))

        message_edit = message_subparsers.add_parser("edit", help="Edit a message in a message group")
        message_edit.add.argument("--groupid", required=True, help="Message group ID")
        message_edit.add.argument("--id", required=True, help="Message ID")
        message_edit.add.argument("--format", choices=["CloudEvents", "None"], help="Message format")
        message_edit.add.argument("--binding", choices=["AMQP", "MQTT", "NATS", "HTTP", "Kafka", "None"], help="Message binding")
        message_edit.add.argument("--schemaformat", help="Schema format")
        message_edit.add.argument("--schemagroup", help="Schema group ID")
        message_edit.add.argument("--schemaid", help="Schema ID")
        message_edit.add.argument("--schemaurl", help="Schema URL")
        message_edit.add.argument("--documentation", help="Documentation URL")
        message_edit.add.argument("--description", help="Description string")
        message_edit.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        message_edit.add.argument("--name", help="Human-readable name")
        message_edit.add.argument("filename", help="Manifest file name")
        message_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_message(
            args.groupid, args.id, args.format, args.binding, args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name
        ))

        schemagroup_parser = manifest_subparsers.add_parser("schemagroup", help="Manage schema groups")
        schemagroup_subparsers = schemagroup_parser.add_subparsers(dest="schemagroup_command", help="Schema group commands")

        schemagroup_add = schemagroup_subparsers.add_parser("add", help="Add a schema group")
        schemagroup_add.add.argument("--id", required=True, help="Schema group ID")
        schemagroup_add.add.argument("--documentation", help="Documentation URL")
        schemagroup_add.add.argument("--description", help="Description string")
        schemagroup_add.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        schemagroup_add.add.argument("--name", help="Human-readable name")
        schemagroup_add.add.argument("filename", help="Manifest file name")
        schemagroup_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_schemagroup(
            args.id, args.documentation, args.description, args.labels, args.name
        ))

        schemagroup_remove = schemagroup_subparsers.add.parser("remove", help="Remove a schema group")
        schemagroup_remove.add.argument("--id", required=True, help="Schema group ID")
        schemagroup_remove.add.argument("filename", help="Manifest file name")
        schemagroup_remove.set_defaults(func=lambda args: ManifestSubcommands(args.filename).remove_schemagroup(args.id))

        schemagroup_edit = schemagroup_subparsers.add_parser("edit", help="Edit a schema group")
        schemagroup_edit.add.argument("--id", required=True, help="Schema group ID")
        schemagroup_edit.add.argument("--documentation", help="Documentation URL")
        schemagroup_edit.add.argument("--description", help="Description string")
        schemagroup_edit.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        schemagroup_edit.add.argument("--name", help="Human-readable name")
        schemagroup_edit.add.argument("filename", help="Manifest file name")
        schemagroup_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_schemagroup(
            args.id, args.documentation, args.description, args.labels, args.name
        ))

        schema_parser = schemagroup_subparsers.add_parser("schema", help="Manage schemas in a schema group")
        schema_subparsers = schema_parser.add_subparsers(dest="schema_command", help="Schema commands")

        schema_add = schema_subparsers.add.parser("add", help="Add a schema to a schema group")
        schema_add.add.argument("--groupid", required=True, help="Schema group ID")
        schema_add.add.argument("--id", required=True, help="Schema ID")
        schema_add.add.argument("--format", required=True, choices=["JSONSchema", "XSD", "Avro", "Protobuf"], help="Schema format")
        schema_add.add.argument("--versionid", help="Schema version ID")
        schema_add.add.argument("--schema", help="Literal schema string")
        schema_add.add.argument("--schemaimport", help="Schema import file or URL")
        schema_add.add.argument("--schemaurl", help="Schema URL")
        schema_add.add.argument("--documentation", help="Documentation URL")
        schema_add.add.argument("--description", help="Description string")
        schema_add.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        schema_add.add.argument("--name", help="Human-readable name")
        schema_add.add.argument("filename", help="Manifest file name")
        schema_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_schema(
            args.groupid, args.id, args.format, args.versionid, args.schema, args.schemaimport, args.schemaurl,
            args.documentation, args.description, args.labels, args.name
        ))

        schema_remove = schema_subparsers.add_parser("remove", help="Remove a schema from a schema group")
        schema_remove.add.argument("--groupid", required=True, help="Schema group ID")
        schema_remove.add.argument("--id", required=True, help="Schema ID")
        schema_remove.add.argument("--versionid", help="Schema version ID")
        schema_remove.add.argument("filename", help="Manifest file name")
        schema_remove.set_defaults(func=lambda args: ManifestSubcommands(args.filename).remove_schema(
            args.groupid, args.id, args.versionid
        ))

        schema_edit = schema_subparsers.add.parser("edit", help="Edit a schema in a schema group")
        schema_edit.add.argument("--groupid", required=True, help="Schema group ID")
        schema_edit.add.argument("--id", required=True, help="Schema ID")
        schema_edit.add.argument("--versionid", required=True, help="Schema version ID")
        schema_edit.add.argument("--format", choices=["JSONSchema", "XSD", "Avro", "Protobuf"], help="Schema format")
        schema_edit.add.argument("--schema", help="Literal schema string")
        schema_edit.add.argument("--schemaimport", help="Schema import file or URL")
        schema_edit.add.argument("--schemaurl", help="Schema URL")
        schema_edit.add.argument("--documentation", help="Documentation URL")
        schema_edit.add.argument("--description", help="Description string")
        schema_edit.add.argument("--labels", nargs='*', help="Labels as key=value pairs")
        schema_edit.add.argument("--name", help="Human-readable name")
        schema_edit.add.argument("--y", action='store_true', help="Suppress confirmation prompt")
        schema_edit.add.argument("filename", help="Manifest file name")
        schema_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_schema(
            args.groupid, args.id, args.versionid, args.format, args.schema, args.schemaimport, args.schemaurl,
            args.documentation, args.description, args.labels, args.name, args.y
        ))

        schema_default_version = schema_subparsers.add.parser("setdefaultversion", help="Set default version for a schema")
        schema_default_version.add.argument("--groupid", required=True, help="Schema group ID")
        schema_default_version.add.argument("--id", required=True, help="Schema ID")
        schema_default_version.add.argument("--versionid", required=True, help="Schema version ID")
        schema_default_version.add.argument("filename", help="Manifest file name")
        schema_default_version.set_defaults(func=lambda args: ManifestSubcommands(args.filename).set_default_version(
            args.groupid, args.id, args.versionid
        ))

    def process_command(self, args: Any):
        """
        Process the specified manifest command.

        Args:
            args (Any): The arguments parsed from the command line.
        """
        if hasattr(args, 'func'):
            args.func(args)
        else:
            print("No command specified. Use --help for more information.")

# def main():
#     """
#     The main function to parse arguments and execute the corresponding commands.
#     """
#     parser = argparse.ArgumentParser(description="xRegistry CLI")
#     subparsers = parser.add_subparsers(dest="command", help="The command to execute: generate, validate or list")
#     subparsers.default = "generate"
#     generate = subparsers.add_parser("generate", help="Generate code.")
#     generate.set_defaults(func=generate_code)
#     validate = subparsers.add_parser("validate", help="Validate a definition")
#     validate.set_defaults(func=validate_definition)
#     list1 = subparsers.add_parser("list", help="List available templates")
#     list1.set_defaults(func=list_templates)
#     subparsers.required = True

#     manifest_parser = subparsers.add_parser("manifest", help="Manage manifest files")
#     manifest_subparsers = manifest_parser.add_subparsers(dest="subcommand", help="Manifest subcommands")

#     subcommand_instance = ManifestSubcommands("")
#     subcommand_instance.add_parsers(manifest_subparsers)

#     args = parser.parse_args()
#     if args.command == "manifest":
#         subcommand_instance.filename = args.filename
#         subcommand_instance.process_command(args)
#     else:
#         args.func(args)

# if __name__ == "__main__":
#     main()
