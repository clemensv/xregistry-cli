# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring, line-too-long

import json
import argparse
from pathlib import Path
from sys import version
from typing import Dict, List, Literal, Optional, Any, Union
from datetime import datetime

PROPERTY_TYPES = ["string", "int", "timestamp", "uritemplate"]


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
                "$schema": "http://xregistry.io/schemas/manifest.json",
                "specversion": "0.5-wip",
                "endpoints": {},
                "messagegroups": {},
                "schemagroups": {}
            }

    def save_manifest(self):
        """
        Save the current state of the manifest to the file.
        """
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump(self.manifest, file, indent=4)

    def init_manifest(self):
        """
        Initialize a new manifest with empty collections for endpoints, messagegroups, and schemagroups.
        """
        self.save_manifest()

    def _set_common_fields(self, data: dict, description: Optional[str] = None, documentation: Optional[str] = None,
                           labels: Optional[List[str]] = None, name: Optional[str] = None, initial: bool = False):
        """
        Set common fields for manifest entries.

        Args:
            data (dict): The data dictionary to update.
            description (Optional[str]): Description of the entry.
            documentation (Optional[str]): URL to the documentation.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the entry.
            initial (bool): Whether this is the initial creation of the entry.
        """
        if description:
            data['description'] = description
        if documentation:
            data['documentation'] = documentation
        if labels:
            data['labels'] = dict(kv.split('=') for kv in labels)
        if name:
            data['name'] = name
        now_iso = datetime.utcnow().isoformat()
        if initial:
            data['createdat'] = now_iso
            data['epoch'] = 0
        data['modifiedat'] = now_iso

    def add_endpoint(self, endpoint_id: str, usage: str, protocol: Optional[str] = None, deployed: Optional[bool] = None,
                     endpoints: Optional[List[str]] = None, options: Optional[List[str]] = None,
                     messagegroups: Optional[List[str]] = None, documentation: Optional[str] = None,
                     description: Optional[str] = None, labels: Optional[List[str]] = None, name: Optional[str] = None,
                     channel: Optional[str] = None, deprecated: Optional[str] = None):
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
            channel (Optional[str]): Channel identifier.
            deprecated (Optional[str]): Deprecation information.
        """
        if endpoint_id in self.manifest['endpoints']:
            raise ValueError(f"Endpoint with id {endpoint_id} already exists.")
        endpoint: Dict[str, Union[str, Dict[str, str], List[str]]] = {
            "endpointid": endpoint_id,
            "usage": usage.capitalize(),
        }
        endpoint_config = {}
        if endpoints:
            endpoint_config['endpoints'] = [{"uri": uri} for uri in endpoints]
        if protocol:
            endpoint_config['protocol'] = protocol.upper()
        if deployed is not None:
            endpoint_config['deployed'] = deployed
        if options:
            endpoint_config['options'] = dict(kv.split('=') for kv in options)
        if len(endpoint_config) > 0:
            endpoint['config'] = endpoint_config
        if messagegroups:
            endpoint['messagegroups'] = messagegroups
        self._set_common_fields(endpoint, description,
                                documentation, labels, name, initial=True)
        if channel:
            endpoint['channel'] = channel
        if deprecated:
            endpoint['deprecated'] = deprecated
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

    def edit_endpoint(self, endpoint_id: str, usage: Optional[str] = None, protocol: Optional[str] = None, deployed: Optional[bool] = None,
                      endpoints: Optional[List[str]] = None, options: Optional[List[str]] = None,
                      messagegroups: Optional[List[str]] = None, documentation: Optional[str] = None,
                      description: Optional[str] = None, labels: Optional[List[str]] = None, name: Optional[str] = None,
                      channel: Optional[str] = None, deprecated: Optional[str] = None):
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
            channel (Optional[str]): Channel identifier.
            deprecated (Optional[str]): Deprecation information.
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
            endpoint['config']['endpoints'] = [
                {"uri": uri} for uri in endpoints]
        if options:
            endpoint['config']['options'] = dict(kv.split('=') for kv in options)
        if messagegroups:
            endpoint['messagegroups'] = messagegroups
        self._set_common_fields(endpoint, description,
                                documentation, labels, name)
        if 'epoch' not in endpoint:
            endpoint['epoch'] = 0
        endpoint['epoch'] += 1
        if channel:
            endpoint['channel'] = channel
        if deprecated:
            endpoint['deprecated'] = deprecated
        self.save_manifest()

    def show_endpoint(self, endpoint_id: str):
        """
        Show an endpoint from the manifest.

        Args:
            endpoint_id (str): The unique identifier for the endpoint to be shown.
        """
        if endpoint_id not in self.manifest['endpoints']:
            raise ValueError(f"Endpoint with id {endpoint_id} does not exist.")
        print(json.dumps(self.manifest['endpoints'][endpoint_id], indent=4))

    def apply_endpoint(self, endpoint_json: str):
        """
        Apply an endpoint JSON to the manifest.

        Args:
            endpoint_json (str): The JSON file containing the endpoint data.
        """
        with open(endpoint_json, 'r', encoding='utf-8') as file:
            endpoint_data = json.load(file)
        endpoint_id = endpoint_data.get('id')
        if not endpoint_id:
            raise ValueError("Endpoint ID is required in the JSON data.")
        self.manifest['endpoints'][endpoint_id] = endpoint_data
        self.save_manifest()

    def add_messagegroup(self, group_id: str, format_: Optional[str] = None, documentation: Optional[str] = None,
                         description: Optional[str] = None, labels: Optional[List[str]] = None, name: Optional[str] = None,
                         binding: Optional[str] = None):
        """
        Add a message group to the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            format (Optional[str]): The format of the message group (CloudEvents or None).
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the message group.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the message group.
            binding (Optional[str]): Binding identifier for the message group.
        """
        if group_id in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} already exists.")
        messagegroup = {
            "messagegroupid": group_id,
            "messages": {}
        }
        if format_ and format_.lower() != 'none':
            messagegroup['format'] = format_
        if binding:
            messagegroup['binding'] = binding
        self._set_common_fields(messagegroup, description,
                                documentation, labels, name, initial=True)
        self.manifest['messagegroups'][group_id] = messagegroup
        self.save_manifest()

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

    def edit_messagegroup(self, group_id: str, format_: Optional[str] = None, documentation: Optional[str] = None,
                          description: Optional[str] = None, labels: Optional[List[str]] = None, name: Optional[str] = None,
                          binding: Optional[str] = None):
        """
        Edit an existing message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            format (Optional[str]): The format of the message group (CloudEvents or None).
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the message group.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the message group.
            binding (Optional[str]): Binding identifier for the message group.
        """
        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if format_ and format_.lower() != 'none':
            messagegroup['format'] = format_
        if binding:
            messagegroup['binding'] = binding
        self._set_common_fields(messagegroup, description,
                                documentation, labels, name)
        if 'epoch' not in messagegroup:
            messagegroup['epoch'] = 0
        messagegroup['epoch'] += 1
        self.save_manifest()

    def show_messagegroup(self, group_id: str):
        """
        Show a message group from the manifest.

        Args:
            group_id (str): The unique identifier for the message group to be shown.
        """
        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        print(json.dumps(self.manifest['messagegroups'][group_id], indent=4))

    def apply_messagegroup(self, messagegroup_json: str):
        """
        Apply a message group JSON to the manifest.

        Args:
            messagegroup_json (str): The JSON file containing the message group data.
        """
        with open(messagegroup_json, 'r', encoding='utf-8') as file:
            messagegroup_data = json.load(file)
        group_id = messagegroup_data.get('id')
        if not group_id:
            raise ValueError("Message group ID is required in the JSON data.")
        self.manifest['messagegroups'][group_id] = messagegroup_data
        self.save_manifest()

    def add_message(self, group_id: str, message_id: str, format_: Optional[str] = None, binding: Optional[str] = None,
                    schemaformat: Optional[str] = None, schemagroup: Optional[str] = None, schemaid: Optional[str] = None,
                    schemaurl: Optional[str] = None, documentation: Optional[str] = None,
                    description: Optional[str] = None, labels: Optional[List[str]] = None, name: Optional[str] = None):
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
            metadata (Optional[dict]): Metadata of the message.
        """
        if group_id not in self.manifest['messagegroups']:
            self.add_messagegroup(group_id)
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} already exists in group {group_id}.")
        message: Dict[str, Union[Dict[str, str], Dict[str, Dict[str, str]], str]] = {
            "messageid": message_id
        }
        if format_:
            if format_.lower() == 'cloudevents':
                format_ = 'CloudEvents/1.0'
            if format_ not in ['CloudEvents/1.0', 'None']:
                raise ValueError(f"Invalid format {format_}. Must be 'CloudEvents/1.0' or 'None'")
            message['format'] = format_
            if format_.lower() == 'CloudEvents/1.0':
                metadata: Dict[str, Any] = {
                    "type": {
                        "value": message_id
                    }
                }
                message['metadata'] = metadata

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
        self._set_common_fields(message, description,
                                documentation, labels, name, initial=True)
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

    def edit_message(self, group_id: str, message_id: str, format_: Optional[str] = None, binding: Optional[str] = None,
                     schemaformat: Optional[str] = None, schemagroup: Optional[str] = None, schemaid: Optional[str] = None,
                     schemaurl: Optional[str] = None, documentation: Optional[str] = None,
                     description: Optional[str] = None, labels: Optional[List[str]] = None, name: Optional[str] = None):
        """
        Edit an existing message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            format_ (Optional[str]): The format of the message (CloudEvents or None).
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
        if format_:
            if format_.lower() == 'cloudevents':
                format_ = 'CloudEvents/1.0'
            if format_ not in ['CloudEvents/1.0', 'None']:
                raise ValueError(f"Invalid format {format_}. Must be 'CloudEvents/1.0' or 'None' to clear")
            message['format'] = format_
            if format_.lower() == 'None':
                if 'metadata' in message:
                    del message['metadata']
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
        self._set_common_fields(message, description,
                                documentation, labels, name)
        if 'epoch' not in message:
            message['epoch'] = 0
        message['epoch'] += 1
        messagegroup['messages'][message_id] = message
        self.save_manifest()

    def show_message(self, group_id: str, message_id: str):
        """
        Show a message from a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message to be shown.
        """
        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        print(json.dumps(messagegroup['messages'][message_id], indent=4))

    def apply_message(self, message_json: str):
        """
        Apply a message JSON to the manifest.

        Args:
            message_json (str): The JSON file containing the message data.
        """
        with open(message_json, 'r', encoding='utf-8') as file:
            message_data = json.load(file)
        group_id = message_data.get('group_id')
        if not group_id:
            raise ValueError("Message group ID is required in the JSON data.")
        message_id = message_data.get('id')
        if not message_id:
            raise ValueError("Message ID is required in the JSON data.")
        if group_id not in self.manifest['messagegroups']:
            self.add_messagegroup(group_id, None, None, None, None, None)
        self.manifest['messagegroups'][group_id]['messages'][message_id] = message_data
        self.save_manifest()

    def add_cloudevents_message_metadata(self, group_id: str, message_id: str, name: str, type_: Literal['string', 'int', 'timestamp', 'uritemplate'], description: Optional[str] = None, value: Optional[str] = None, required: bool = False):
        """
        Add metadata to a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            name (str): Human-readable name for the metadata.
            type_ (Literal['string', 'int', 'timestamp', 'uritemplate']): The type of the metadata.
            description (Optional[str]): Description of the metadata.
            value (Optional[str]): The value of the metadata.
            required (bool): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'format' in message and message['format'].lower() != 'cloudevents/1.0':
            raise ValueError(
                f"Message with id {message_id} is not a CloudEvents message, but has format {message['format']}.")
        if not 'format' in message:
            message['format'] = 'CloudEvents/1.0'
        if 'metadata' not in message:
            message['metadata'] = {}
        if name in message['metadata']:
            raise ValueError(f"Metadata with key {name} already exists in message {message_id}.")
        metadata: Dict[str, Any] = {
            "name": name,
            "type": type_,
        }
        if required:
            metadata['required'] = bool(required)
        if value:
            metadata['value'] = value
        if description:
            metadata['description'] = description
        message['metadata'][name] = metadata
        self.save_manifest()

    def remove_cloudevents_message_metadata(self, group_id: str, message_id: str, name: str):
        """
        Remove metadata from a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            name (str): The name of the metadata to be removed.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'metadata' not in message:
            raise ValueError(f"Message with id {message_id} does not have any metadata.")
        if name not in message['metadata']:
            raise ValueError(f"Metadata with key {name} does not exist in message {message_id}.")
        del message['metadata'][name]
        self.save_manifest()

    def edit_cloudevents_message_metadata(self, group_id: str, message_id: str, name: Optional[str] = None, type_: Optional[Literal['string', 'int', 'timestamp', 'uritemplate']] = None, description: Optional[str] = None, value: Optional[str] = None, required: Optional[bool] = None):
        """
        Edit metadata of a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            name (Optional[str]): Human-readable name for the metadata.
            type_ (Optional[Literal['string', 'int', 'timestamp', 'uritemplate']]): The type of the metadata.
            description (Optional[str]): Description of the metadata.
            required (Optional[bool]): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if not 'format' in message or message['format'].lower() != 'cloudevents/1.0':
            raise ValueError(f"Message with id {message_id} is not a CloudEvents message.")
        if 'metadata' not in message:
            raise ValueError(f"Message with id {message_id} does not have any metadata.")
        if name not in message['metadata']:
            raise ValueError(f"Metadata with key {name} does not exist in message {message_id}.")
        metadata = message['metadata'][name]
        metadata['name'] = name
        if type_:
            metadata['type'] = type_
        if description:
            metadata['description'] = description
        if required is not None:
            metadata['required'] = bool(required)
        if value:
            metadata['value'] = value
        self.save_manifest()

    def apply_message_metadata(self, message_cloudevents_metadata_json: str):
        """
        Apply message metadata JSON to the manifest.

        Args:
            message_cloudevents_metadata_json (str): The JSON file containing the message metadata data.
        """
        with open(message_cloudevents_metadata_json, 'r', encoding='utf-8') as file:
            message_cloudevents_metadata_data = json.load(file)
        group_id = message_cloudevents_metadata_data.get('group_id')
        if not group_id:
            raise ValueError("Message group ID is required in the JSON data.")
        message_id = message_cloudevents_metadata_data.get('message_id')
        if not message_id:
            raise ValueError("Message ID is required in the JSON data.")
        if group_id not in self.manifest['messagegroups']:
            self.add_messagegroup(group_id, None, None, None, None, None)
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            self.add_message(group_id, message_id)
        message = messagegroup['messages'][message_id]
        if 'metadata' not in message:
            message['metadata'] = {}
        for key, metadata in message_cloudevents_metadata_data['metadata'].items():
            if key in message['metadata']:
                raise ValueError(f"Metadata with key {key} already exists in message {message_id}.")
            message['metadata'][key] = metadata
        self.save_manifest()

    def add_schemagroup(self, group_id: str, documentation: Optional[str] = None, description: Optional[str] = None,
                        labels: Optional[List[str]] = None, name: Optional[str] = None):
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
            "schemagroupid": group_id,
            "schemas": {}
        }
        self._set_common_fields(schemagroup, description,
                                documentation, labels, name, initial=True)
        self.manifest['schemagroups'][group_id] = schemagroup
        self.save_manifest()

    def add_amqp_message_metadata(self, group_id: str, message_id: str,
                                  section: Literal['properties', 'application-properties'],
                                  name: str,
                                  type_: Literal['string', 'int',
                                                 'timestamp', 'uritemplate'] = 'string',
                                  value: Optional[str] = None,
                                  description: Optional[str] = None,
                                  required: bool = False):
        """
        Add AMQP metadata to a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            section (Literal['properties', 'application-properties']): The section of the metadata.
            name (str): Human-readable name for the metadata.
            type_ (Literal['string', 'int', 'timestamp', 'uritemplate']): The type of the metadata.
            value (Optional[str]): The value of the metadata.
            description (Optional[str]): Description of the metadata.
            required (bool): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'amqp/1.0':
            raise ValueError(
                f"Message with id {message_id} is not bound to AMQP 1.0, but has binding {message['binding']}.")
        if not 'binding' in message:
            message['binding'] = 'AMQP/1.0'
        if 'message' not in message:
            message['message'] = {}
        if section not in ['properties', 'application-properties']:
            raise ValueError(f"Invalid section {section}. Must be 'properties' or 'application-properties'.")
        if section not in message['message']:
            message['message'][section] = {}
        if name in message['message'][section]:
            raise ValueError(f"AMQP message metadata with key {name} already exists in message {message_id}.{section}")
        metadata: Dict[str, Any] = {
            "name": name,
            "type": type_
        }
        if required:
            metadata['required'] = bool(required)
        if description:
            metadata['description'] = description
        if value:
            metadata['value'] = value
        message['message'][section][name] = metadata
        self.save_manifest()

    def remove_amqp_message_metadata(self, group_id: str, message_id: str, section: Literal['properties', 'application-properties'], name: str):
        """
        Remove AMQP metadata from a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            key (str): The key of the metadata to be removed.
            section (Literal['properties', 'application-properties']): The section of the metadata.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'amqp/1.0':
            raise ValueError(
                f"Message with id {message_id} is not bound to AMQP 1.0, but has binding {message['binding']}.")
        if 'message' not in message:
            raise ValueError(f"Message with id {message_id} does not have any AMQP metadata.")
        if section not in message['message']:
            raise ValueError(f"Message with id {message_id} does not have any {section} metadata.")
        if name not in message['message'][section]:
            raise ValueError(f"AMQP metadata with key {name} does not exist in message {message_id}.{section}.")
        del message['message'][section][name]
        self.save_manifest()

    def edit_amqp_message_metadata(self, group_id: str, message_id: str, section: Literal['properties', 'application-properties'],
                                   name: Optional[str] = None, type_: Optional[Literal['string', 'int', 'timestamp', 'uritemplate']] = None,
                                   value: Optional[str] = None, description: Optional[str] = None, required: Optional[bool] = None):
        """
        Edit AMQP metadata of a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            key (str): The key of the metadata.
            section (Literal['properties', 'application-properties']): The section of the metadata.
            name (Optional[str]): Human-readable name for the metadata.
            type_ (Optional[Literal['string', 'int', 'timestamp', 'uritemplate']]): The type of the metadata.
            value (Optional[str]): The value of the metadata.
            description (Optional[str]): Description of the metadata.
            required (Optional[bool]): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'amqp/1.0':
            raise ValueError(
                f"Message with id {message_id} is not bound to AMQP 1.0, but has binding {message['binding']}.")
        if 'message' not in message:
            raise ValueError(f"Message with id {message_id} does not have any AMQP metadata.")
        if section not in message['message']:
            raise ValueError(f"Message with id {message_id} does not have any {section} metadata.")
        if name not in message['message'][section]:
            raise ValueError(f"AMQP metadata with key {name} does not exist in message {message_id}.{section}.")
        metadata = message['message'][section][name]
        if name:
            metadata['name'] = name
        if type_:
            metadata['type'] = type_
        if value:
            metadata['value'] = value
        if description:
            metadata['description'] = description
        if required:
            metadata['required'] = bool(required)
        self.save_manifest()

    def apply_amqp_message_metadata(self, message_amqp_metadata_json: str):
        """
        Apply AMQP message metadata JSON to the manifest.

        Args:
            message_amqp_metadata_json (str): The JSON file containing the AMQP message metadata data.
        """
        with open(message_amqp_metadata_json, 'r', encoding='utf-8') as file:
            message_amqp_metadata_data = json.load(file)
        group_id = message_amqp_metadata_data.get('group_id')
        if not group_id:
            raise ValueError("Message group ID is required in the JSON data.")
        message_id = message_amqp_metadata_data.get('message_id')
        if not message_id:
            raise ValueError("Message ID is required in the JSON data.")
        if group_id not in self.manifest['messagegroups']:
            self.add_messagegroup(group_id, None, None, None, None, None)
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            self.add_message(group_id, message_id)
        message = messagegroup['messages'][message_id]
        if 'message' not in message:
            message['message'] = {}
        for section, metadata in message_amqp_metadata_data['message'].items():
            if section not in message['message']:
                message['message'][section] = {}
            for key, metadata in metadata.items():
                if key in message['message'][section]:
                    raise ValueError(f"AMQP metadata with key {key} already exists in message {message_id}.{section}")
                message['message'][section][key] = metadata
        self.save_manifest()

    def add_http_message_metadata(self, group_id: str, message_id: str, section: Optional[Literal['headers', 'query']], name: str, type_: Literal['string', 'int', 'timestamp', 'uritemplate'] = 'string', value: Optional[str] = None, description: Optional[str] = None, required: bool = False):
        """
        Add HTTP metadata to a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            key (str): The key of the metadata.
            section (Literal['headers', 'query']): The section of the metadata.
            name (str): Human-readable name for the metadata.
            type_ (Literal['string', 'int', 'timestamp', 'uritemplate']): The type of the metadata.
            value (Optional[str]): The value of the metadata.
            description (Optional[str]): Description of the metadata.
            required (bool): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'http':
            raise ValueError(
                f"Message with id {message_id} is not bound to HTTP, but has binding {message['binding']}.")
        if not 'binding' in message:
            message['binding'] = 'HTTP'
        if 'message' not in message:
            message['message'] = {}
        if section:
            if section not in ['headers', 'query']:
                raise ValueError(f"Invalid section {section}. Must be 'headers' or 'query'.")
            if section not in message['message']:
                message['message'][section] = {}
            if name in message['message'][section]:
                raise ValueError(
                    f"HTTP message metadata with key {name} already exists in message {message_id}.{section}")
            metadata: Dict[str, Any] = {
                "name": name,
                "type": type_,
            }
            if required:
                metadata['required'] = bool(required)
            if description:
                metadata['description'] = description
            message['message'][section][name] = metadata
            self.save_manifest()
        else:
            if name not in ['path', 'method']:
                raise ValueError(f"Invalid key {name}. Must be 'path' or 'method'.")
            if name in message['message']:
                raise ValueError(f"HTTP message metadata with key {name} already exists in message {message_id}")
            metadata: Dict[str, Any] = {
                "name": name,
                "type": type_,
            }
            if required:
                metadata['required'] = "true" if required else "false"
            if description:
                metadata['description'] = description
            message['message'][name] = metadata
            self.save_manifest()

    def remove_http_message_metadata(self, group_id: str, message_id: str, section: Optional[Literal['headers', 'query']], name: str):
        """
        Remove HTTP metadata from a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            name (str): The name of the metadata to be removed.
            section (Optional[Literal['headers', 'query']]): The section of the metadata.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'http':
            raise ValueError(
                f"Message with id {message_id} is not bound to HTTP, but has binding {message['binding']}.")
        if 'message' not in message:
            raise ValueError(f"Message with id {message_id} does not have any HTTP metadata.")
        if section:
            if section not in message['message']:
                raise ValueError(f"Message with id {message_id} does not have any {section} metadata.")
            if name not in message['message'][section]:
                raise ValueError(f"HTTP metadata with name {name} does not exist in message {message_id}.{section}.")
            del message['message'][section][name]
            self.save_manifest()
        else:
            if name not in ['path', 'method']:
                raise ValueError(f"Invalid name {name}. Must be 'path' or 'method'.")
            if name not in message['message']:
                raise ValueError(f"HTTP metadata with name {name} does not exist in message {message_id}")
            del message['message'][name]
            self.save_manifest()

    def edit_http_message_metadata(self, group_id: str, message_id: str, section: Optional[Literal['headers', 'query']],
                                   name: Optional[str] = None, type_: Optional[Literal['string', 'int', 'timestamp', 'uritemplate']] = None,
                                   value: Optional[str] = None, description: Optional[str] = None, required: Optional[bool] = None):
        """
        Edit HTTP metadata of a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            name (str): The name of the metadata.
            section (Optional[Literal['headers', 'query']]): The section of the metadata.
            name (Optional[str]): Human-readable name for the metadata.
            type_ (Optional[Literal['string', 'int', 'timestamp', 'uritemplate']]): The type of the metadata.
            value (Optional[str]): The value of the metadata.
            description (Optional[str]): Description of the metadata.
            required (Optional[bool]): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'http':
            raise ValueError(
                f"Message with id {message_id} is not bound to HTTP, but has binding {message['binding']}.")
        if 'message' not in message:
            raise ValueError(f"Message with id {message_id} does not have any HTTP metadata.")
        if section:
            if section not in message['message']:
                raise ValueError(f"Message with id {message_id} does not have any {section} metadata.")
            if name not in message['message'][section]:
                raise ValueError(f"HTTP metadata with name {name} does not exist in message {message_id}.{section}.")
            metadata = message['message'][section][name]
            if name:
                metadata['name'] = name
            if type_:
                metadata['type'] = type_
            if value:
                metadata['value'] = value
            if description:
                metadata['description'] = description
            if required is not None:
                metadata['required'] = bool(required)
            self.save_manifest()
        else:
            if name not in ['path', 'method']:
                raise ValueError(f"Invalid name {name}. Must be 'path' or 'method'.")
            if name not in message['message']:
                raise ValueError(f"HTTP metadata with name {name} does not exist in message {message_id}")
            metadata = message['message'][name]
            if name:
                metadata['name'] = name
            if type_:
                metadata['type'] = type_
            if value:
                metadata['value'] = value
            if description:
                metadata['description'] = description
            if required is not None:
                metadata['required'] = bool(required)
            self.save_manifest()

    def apply_http_message_metadata(self, message_http_metadata_json: str):
        """
        Apply HTTP message metadata JSON to the manifest.

        Args:
            message_http_metadata_json (str): The JSON file containing the HTTP message metadata data.
        """
        with open(message_http_metadata_json, 'r', encoding='utf-8') as file:
            message_http_metadata_data = json.load(file)
        group_id = message_http_metadata_data.get('group_id')
        if not group_id:
            raise ValueError("Message group ID is required in the JSON data.")
        message_id = message_http_metadata_data.get('message_id')
        if not message_id:
            raise ValueError("Message ID is required in the JSON data.")
        if group_id not in self.manifest['messagegroups']:
            self.add_messagegroup(group_id, None, None, None, None, None)
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            self.add_message(group_id, message_id)
        message = messagegroup['messages'][message_id]
        if 'message' not in message:
            message['message'] = {}
        for section, metadata in message_http_metadata_data['message'].items():
            if section not in message['message']:
                message['message'][section] = {}
            for key, metadata in metadata.items():
                if key in message['message'][section]:
                    raise ValueError(f"HTTP metadata with key {key} already exists in message {message_id}.{section}")
                message['message'][section][key] = metadata
        self.save_manifest()

    def add_kafka_message_metadata(self, group_id: str, message_id: str, section: Optional[Literal['headers']], name: str, type_: Literal['string', 'int', 'timestamp', 'uritemplate'] = 'string', value: Optional[str] = None, description: Optional[str] = None, required: bool = False):
        """
        Add Kafka metadata to a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            section (Literal['headers']): The section of the metadata.
            name (str): Human-readable name for the metadata.
            type_ (Literal['string', 'int', 'timestamp', 'uritemplate']): The type of the metadata.
            value (Optional[str]): The value of the metadata.
            description (Optional[str]): Description of the metadata.
            required (bool): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'kafka':
            raise ValueError(
                f"Message with id {message_id} is not bound to Kafka, but has binding {message['binding']}.")
        if not 'binding' in message:
            message['binding'] = 'Kafka'
        if 'message' not in message:
            message['message'] = {}
        if section:
            if section not in ['headers']:
                raise ValueError(f"Invalid section {section}. Must be 'headers'.")
            if section not in message['message']:
                message['message'][section] = {}
            if name in message['message'][section]:
                raise ValueError(
                    f"Kafka message metadata with key {name} already exists in message {message_id}.{section}")
            metadata: Dict[str, Any] = {
                "name": name,
                "type": type_,
                "required": bool(required)
            }
            if description:
                metadata['description'] = description
            message['message'][section][name] = metadata
            self.save_manifest()
        else:
            if key not in ['topic', 'partition', 'key']:
                raise ValueError(f"Invalid key {name}. Must be 'topic', 'partition', or 'key'.")
            if key in message['message']:
                raise ValueError(f"Kafka message metadata with key {name} already exists in message {message_id}")
            metadata: Dict[str, Any] = {
                "name": name,
                "type": type_
            }
            if required:
                metadata['required'] = bool(required)
            if description:
                metadata['description'] = description
            message['message'][name] = metadata
            self.save_manifest()

    def remove_kafka_message_metadata(self, group_id: str, message_id: str, section: Optional[Literal['headers']], name: str):
        """
        Remove Kafka metadata from a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            key (str): The key of the metadata to be removed.
            section (Optional[Literal['headers']]): The section of the metadata.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'kafka':
            raise ValueError(
                f"Message with id {message_id} is not bound to Kafka, but has binding {message['binding']}.")
        if 'message' not in message:
            raise ValueError(f"Message with id {message_id} does not have any Kafka metadata.")
        if section:
            if section not in message['message']:
                raise ValueError(f"Message with id {message_id} does not have any {section} metadata.")
            if name not in message['message'][section]:
                raise ValueError(f"Kafka metadata with name {name} does not exist in message {message_id}.{section}.")
            del message['message'][section][name]
            self.save_manifest()
        else:
            if name not in ['topic', 'partition', 'name']:
                raise ValueError(f"Invalid name {name}. Must be 'topic', 'partition', or 'name'.")
            if name not in message['message']:
                raise ValueError(f"Kafka metadata with name {name} does not exist in message {message_id}")
            del message['message'][name]
            self.save_manifest()

    def edit_kafka_message_metadata(self, group_id: str, message_id: str, section: Optional[Literal['headers']],
                                    name: Optional[str] = None, type_: Optional[Literal['string', 'int', 'timestamp', 'uritemplate']] = None,
                                    value: Optional[str] = None, description: Optional[str] = None, required: Optional[bool] = None):
        """
        Edit Kafka metadata of a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            key (str): The key of the metadata.
            section (Optional[Literal['headers']]): The section of the metadata.
            name (Optional[str]): Human-readable name for the metadata.
            type_ (Optional[Literal['string', 'int', 'timestamp', 'uritemplate']]): The type of the metadata.
            value (Optional[str]): The value of the metadata.
            description (Optional[str]): Description of the metadata.
            required (Optional[bool]): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message and message['binding'].lower() != 'kafka':
            raise ValueError(
                f"Message with id {message_id} is not bound to Kafka, but has binding {message['binding']}.")
        if 'message' not in message:
            raise ValueError(f"Message with id {message_id} does not have any Kafka metadata.")
        if section:
            if section not in message['message']:
                raise ValueError(f"Message with id {message_id} does not have any {section} metadata.")
            if name not in message['message'][section]:
                raise ValueError(f"Kafka metadata with name {name} does not exist in message {message_id}.{section}.")
            metadata = message['message'][section][name]
            if name:
                metadata['name'] = name
            if type_:
                metadata['type'] = type_
            if value:
                metadata['value'] = value
            if description:
                metadata['description'] = description
            if required is not None:
                metadata['required'] = bool(required)
            self.save_manifest()
        else:
            if name not in ['topic', 'partition', 'name']:
                raise ValueError(f"Invalid name {name}. Must be 'topic', 'partition', or 'name'.")
            if name not in message['message']:
                raise ValueError(f"Kafka metadata with name {name} does not exist in message {message_id}")
            metadata = message['message'][name]
            if name:
                metadata['name'] = name
            if type_:
                metadata['type'] = type_
            if value:
                metadata['value'] = value
            if description:
                metadata['description'] = description
            if required is not None:
                metadata['required'] = bool(required)
            self.save_manifest()

    def apply_kafka_message_metadata(self, message_kafka_metadata_json: str):
        """
        Apply Kafka message metadata JSON to the manifest.

        Args:
            message_kafka_metadata_json (str): The JSON file containing the Kafka message metadata data.
        """

        with open(message_kafka_metadata_json, 'r', encoding='utf-8') as file:
            message_kafka_metadata_data = json.load(file)
        group_id = message_kafka_metadata_data.get('group_id')
        if not group_id:
            raise ValueError("Message group ID is required in the JSON data.")
        message_id = message_kafka_metadata_data.get('message_id')
        if not message_id:
            raise ValueError("Message ID is required in the JSON data.")
        if group_id not in self.manifest['messagegroups']:
            self.add_messagegroup(group_id, None, None, None, None, None)
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            self.add_message(group_id, message_id)
        message = messagegroup['messages'][message_id]
        if 'message' not in message:
            message['message'] = {}
        for section, metadata in message_kafka_metadata_data['message'].items():
            if section not in message['message']:
                message['message'][section] = {}
            for key, metadata in metadata.items():
                if key in message['message'][section]:
                    raise ValueError(f"Kafka metadata with key {key} already exists in message {message_id}.{section}")
                message['message'][section][key] = metadata
        self.save_manifest()

    def add_mqtt_message_metadata(self, group_id: str, message_id: str, mqtt_version: Literal['3', '5', '3.1.1', '5.0'], name: str, type_: Literal['string', 'int', 'timestamp', 'uritemplate'] = 'string', value: Optional[str] = None, description: Optional[str] = None, required: bool = False):
        """
        Add MQTT metadata to a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            mqtt_version (Literal['3', '5', '3.1.1', '5.0']): The MQTT version of the metadata.
            name (str): Human-readable name for the metadata.
            type_ (Literal['string', 'int', 'timestamp', 'uritemplate']): The type of the metadata.
            value (Optional[str]): The value of the metadata.
            description (Optional[str]): Description of the metadata.
            required (bool): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if mqtt_version not in ['3', '5', '3.1.1', '5.0']:
            raise ValueError(f"Invalid MQTT version {mqtt_version}. Must be '3', '5', '3.1.1', or '5.0'.")
        if mqtt_version == '3':
            mqtt_version = '3.1.1'
        if mqtt_version == '5':
            mqtt_version = '5.0'
        if 'binding' in message:
            message_binding = message['binding'].lower()
            if not message_binding.startswith('mqtt'):
                raise ValueError(
                    f"Message with id {message_id} is not bound to MQTT, but has binding {message['binding']}.")
            if message_binding != f"mqtt/{mqtt_version}":
                raise ValueError(
                    f"Message with id {message_id} is not bound to MQTT, but has binding {message['binding']}.")
        else:
            message['binding'] = f"MQTT/{mqtt_version}"
        if 'message' not in message:
            message['message'] = {}
        if name in message['message']:
            raise ValueError(f"MQTT message metadata with name {name} already exists in message {message_id}")
        if mqtt_version == '3.1.1' and name not in ['topic', 'qos', 'retain']:
            raise ValueError(f"Invalid name {name}. Must be 'topic', 'qos', or 'retain'.")
        if mqtt_version == '5.0' and name not in ['topic', 'qos', 'retain', 'message-expiry-interval', 'response_topic', 'correlation_data', 'content_type', 'payload_format_indicator', 'user-properties']:
            raise ValueError(
                f"Invalid name {name}. Must be 'topic', 'qos', 'retain', 'message-expiry-interval', 'response_topic', 'correlation_data', 'content_type', 'payload_format_indicator', or 'user-properties'.")
        metadata: Dict[str, Any] = {
            "name": name,
            "type": type_
        }
        if required:
            metadata['required'] = bool(required)
        if description:
            metadata['description'] = description
        message['message'][name] = metadata
        self.save_manifest()

    def remove_mqtt_message_metadata(self, group_id: str, message_id: str, name: str):
        """
        Remove MQTT metadata from a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            mqtt_version (Literal['3', '5', '3.1.1', '5.0']): The MQTT version of the metadata.
            name (str): The name of the metadata to be removed.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message:
            message_binding = message['binding'].lower()
            if not message_binding.startswith('mqtt'):
                raise ValueError(
                    f"Message with id {message_id} is not bound to MQTT, but has binding {message['binding']}.")
        else:
            raise ValueError(f"Message with id {message_id} is not bound to MQTT.")
        if 'message' not in message:
            raise ValueError(f"Message with id {message_id} does not have any MQTT metadata.")
        if name not in message['message']:
            raise ValueError(f"MQTT metadata with name {name} does not exist in message {message_id}")
        del message['message'][name]
        self.save_manifest()

    def edit_mqtt_message_metadata(self, group_id: str, message_id: str, name: str, type_: Optional[Literal['string', 'int', 'timestamp', 'uritemplate']] = None, value: Optional[str] = None, description: Optional[str] = None, required: Optional[bool] = None):
        """
        Edit MQTT metadata of a message in a message group in the manifest.

        Args:
            group_id (str): The unique identifier for the message group.
            message_id (str): The unique identifier for the message.
            mqtt_version (Literal['3', '5', '3.1.1', '5.0']): The MQTT version of the metadata.
            name (str): Human-readable name for the metadata.
            type_ (Optional[Literal['string', 'int', 'timestamp', 'uritemplate']]): The type of the metadata.
            value (Optional[str]): The value of the metadata.
            description (Optional[str]): Description of the metadata.
            required (Optional[bool]): Whether the metadata is required.
        """

        if group_id not in self.manifest['messagegroups']:
            raise ValueError(f"Message group with id {group_id} does not exist.")
        messagegroup = self.manifest['messagegroups'][group_id]
        if message_id not in messagegroup['messages']:
            raise ValueError(f"Message with id {message_id} does not exist in group {group_id}.")
        message = messagegroup['messages'][message_id]
        if 'binding' in message:
            message_binding = message['binding'].lower()
            if not message_binding.startswith('mqtt'):
                raise ValueError(
                    f"Message with id {message_id} is not bound to MQTT, but has binding {message['binding']}.")
        else:
            raise ValueError(f"Message with id {message_id} is not bound to MQTT.")
        if 'message' not in message:
            raise ValueError(f"Message with id {message_id} does not have any MQTT metadata.")
        if name not in message['message']:
            raise ValueError(f"MQTT metadata with name {name} does not exist in message {message_id}")
        metadata = message['message'][name]
        if name:
            metadata['name'] = name
        if type_:
            metadata['type'] = type_
        if value:
            metadata['value'] = value
        if description:
            metadata['description'] = description
        if required is not None:
            metadata['required'] = bool(required)
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

    def edit_schemagroup(self, group_id: str, documentation: Optional[str] = None, description: Optional[str] = None,
                         labels: Optional[List[str]] = None, name: Optional[str] = None):
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
        self._set_common_fields(schemagroup, description,
                                documentation, labels, name)
        if 'epoch' not in schemagroup:
            schemagroup['epoch'] = 0
        schemagroup['epoch'] += 1
        self.save_manifest()

    def show_schemagroup(self, group_id: str):
        """
        Show a schema group from the manifest.

        Args:
            group_id (str): The unique identifier for the schema group to be shown.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        print(json.dumps(self.manifest['schemagroups'][group_id], indent=4))

    def apply_schemagroup(self, schemagroup_json: str):
        """
        Apply a schema group JSON to the manifest.

        Args:
            schemagroup_json (str): The JSON file containing the schema group data.
        """
        with open(schemagroup_json, 'r', encoding='utf-8') as file:
            schemagroup_data = json.load(file)
        group_id = schemagroup_data.get('id')
        if not group_id:
            raise ValueError("Schema group ID is required in the JSON data.")
        self.manifest['schemagroups'][group_id] = schemagroup_data
        self.save_manifest()

    def add_schemaversion(self, group_id: str, schema_id: str, format_: str, version_id: Optional[str] = None, schema: Optional[str] = None,
                   schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, documentation: Optional[str] = None,
                   description: Optional[str] = None, labels: Optional[List[str]] = None, name: Optional[str] = None):
        """
        Add a schema to a schema group in the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            schema_id (str): The unique identifier for the schema.
            format (str): The format of the schema.
            version_id (Optional[str]): The version identifier of the schema.
            schema (Optional[str]): The inline schema.
            schemaimport (Optional[str]): The file location or URL to import the schema.
            schemaurl (Optional[str]): The URL of the schema.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the schema.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the schema.
        """
        if group_id not in self.manifest['schemagroups']:
            self.add_schemagroup(group_id, None, None, None, None)
        schemagroup = self.manifest['schemagroups'][group_id]
        if 'schemas' in schemagroup and schema_id in schemagroup['schemas']:
            schema_data = schemagroup['schemas'][schema_id]
        else:
            schema_data = {
                "schemaid": schema_id,
                "format": format_,
                "versions": {}
            }
        if version_id and version_id in schema_data['versions']:
            raise ValueError(f"Version {version_id} of schema {schema_id} already exists.")
        if not version_id:
            if 'versions' not in schema_data or not schema_data['versions']:
                version_id = '1'
            else:
                version_id = str(max([int(v) for v in schema_data['versions']]) + 1)
        version_data = {
            "schemaid": schema_id,
            "versionid": version_id,
            "format": format_
        }
        if schema:
            try:
                version_data['schema'] = json.loads(schema)
            except json.JSONDecodeError:
                version_data['schemabase64'] = schema.encode('utf-8').hex()
        elif schemaimport:
            if Path(schemaimport).exists():
                with open(schemaimport, 'r', encoding='utf-8') as file:
                    version_data['schema'] = json.load(file)
            else:
                raise ValueError(f"Schema import file {schemaimport} does not exist.")
        elif schemaurl:
            version_data['schemaurl'] = schemaurl
        self._set_common_fields(version_data, description, documentation, labels, name, initial=True)
        schema_data['versions'][version_id] = version_data
        schemagroup['schemas'][schema_id] = schema_data
        self.save_manifest()

    def remove_schemaversion(self, group_id: str, schema_id: str, version_id: Optional[str] = None):
        """
        Remove a schema or schema version from a schema group in the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            schema_id (str): The unique identifier for the schema.
            version_id (Optional[str]): The version identifier of the schema to be removed.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        schemagroup = self.manifest['schemagroups'][group_id]
        if schema_id not in schemagroup['schemas']:
            raise ValueError(f"Schema with id {schema_id} does not exist in group {group_id}.")
        if version_id:
            if version_id in schemagroup['schemas'][schema_id]['versions']:
                del schemagroup['schemas'][schema_id]['versions'][version_id]
                if not schemagroup['schemas'][schema_id]['versions']:
                    del schemagroup['schemas'][schema_id]
            else:
                raise ValueError(f"Version {version_id} of schema {schema_id} does not exist.")
        else:
            del schemagroup['schemas'][schema_id]
        self.save_manifest()

    def edit_schemaversion(self, group_id: str, schema_id: str, version_id: str, format_: Optional[str] = None,
                    schema: Optional[str] = None, schemaimport: Optional[str] = None, schemaurl: Optional[str] = None,
                    documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[List[str]] = None,
                    name: Optional[str] = None, confirm_edit: bool = False):
        """
        Edit an existing schema or schema version in a schema group in the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            schema_id (str): The unique identifier for the schema.
            version_id (str): The version identifier of the schema.
            format (Optional[str]): The format of the schema.
            schema (Optional[str]): The inline schema.
            schemaimport (Optional[str]): The file location or URL to import the schema.
            schemaurl (Optional[str]): The URL of the schema.
            documentation (Optional[str]): URL to the documentation.
            description (Optional[str]): Description of the schema.
            labels (Optional[List[str]]): A list of key=value pairs for labels.
            name (Optional[str]): Human-readable name for the schema.
            confirm_edit (bool): Confirmation to proceed with editing schema version.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        schemagroup = self.manifest['schemagroups'][group_id]
        if schema_id not in schemagroup['schemas']:
            raise ValueError(f"Schema with id {schema_id} does not exist in group {group_id}.")
        if not version_id or version_id not in schemagroup['schemas'][schema_id]['versions']:
            raise ValueError(f"Version {version_id} of schema {schema_id} does not exist.")
        if not confirm_edit:
            response = input(
                "It is not recommended to edit schema versions, but rather add revisions of schemas to the version history. Do you want to proceed? (y/N): ")
            if response.lower() != 'y':
                return
        version_data = schemagroup['schemas'][schema_id]
        if format_:
            version_data['format'] = format_
        if version_id:
            version_data['version'] = version_id
        if schema:
            try:
                version_data['schema'] = json.loads(schema)
            except json.JSONDecodeError:
                version_data['schemabase64'] = schema.encode('utf-8').hex()
        elif schemaimport:
            if Path(schemaimport).exists():
                with open(schemaimport, 'r', encoding='utf-8') as file:
                    version_data['schema'] = json.load(file)
            else:
                raise ValueError(f"Schema import file {schemaimport} does not exist.")
        elif schemaurl:
            version_data['schemaurl'] = schemaurl
        self._set_common_fields(version_data, description,
                                documentation, labels, name)
        if 'epoch' not in version_data:
            version_data['epoch'] = 0
        version_data['epoch'] += 1
        schemagroup['schemas'][schema_id] = version_data
        self.save_manifest()

    def show_schema(self, group_id: str, schema_id: str):
        """
        Show a schema from a schema group in the manifest.

        Args:
            group_id (str): The unique identifier for the schema group.
            schema_id (str): The unique identifier for the schema to be shown.
        """
        if group_id not in self.manifest['schemagroups']:
            raise ValueError(f"Schema group with id {group_id} does not exist.")
        schemagroup = self.manifest['schemagroups'][group_id]
        if schema_id not in schemagroup['schemas']:
            raise ValueError(f"Schema with id {schema_id} does not exist in group {group_id}.")
        print(json.dumps(schemagroup['schemas'][schema_id], indent=4))

    def apply_schema(self, schema_json: str):
        """
        Apply a schema JSON to the manifest.

        Args:
            schema_json (str): The JSON file containing the schema data.
        """
        with open(schema_json, 'r', encoding='utf-8') as file:
            schema_data = json.load(file)
        group_id = schema_data.get('group_id')
        if not group_id:
            raise ValueError("Schema group ID is required in the JSON data.")
        schema_id = schema_data.get('id')
        if not schema_id:
            raise ValueError("Schema ID is required in the JSON data.")
        if group_id not in self.manifest['schemagroups']:
            self.add_schemagroup(group_id, None, None, None, None)
        self.manifest['schemagroups'][group_id]['schemas'][schema_id] = schema_data
        self.save_manifest()

    @classmethod
    def add_parsers(cls, manifest_parser: argparse.ArgumentParser):
        """
        Add subparsers for the manifest commands.

        Args:
            subparsers (Any): The subparsers object to add the subcommands to.
        """

        manifest_subparsers = manifest_parser.add_subparsers(help="Manifest commands")
        manifest_init = manifest_subparsers.add_parser("init", help="Initialize a new manifest file")
        manifest_init.set_defaults(func=lambda args: ManifestSubcommands(args.filename).init_manifest())

        def add_common_arguments(parser):
            """
            Add common arguments to the parser.

            Args:
                parser (ArgumentParser): The parser to add arguments to.
            """
            parser.add_argument("--description", help="Description string")
            parser.add_argument("--documentation", help="Documentation URL")
            parser.add_argument("--labels", nargs='*',
                                help="Labels as key=value pairs")
            parser.add_argument("--name", help="Human-readable name")

        endpoint_subparsers = manifest_subparsers.add_parser("endpoint", help="Manage endpoints").add_subparsers(
            dest="endpoint_command", help="Endpoint commands")

        endpoint_add = endpoint_subparsers.add_parser("add", help="Add a new endpoint")
        endpoint_add.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_add.add_argument("--usage", required=True,
                                  choices=["subscriber", "producer", "consumer"], help="Usage type")
        endpoint_add.add_argument("--protocol", choices=["HTTP", "AMQP", "MQTT", "Kafka", "NATS"], help="Protocol")
        endpoint_add.add_argument("--deployed", type=bool, help="Deployed status")
        endpoint_add.add_argument("--endpoints", nargs='+', help="Endpoint URIs")
        endpoint_add.add_argument("--options", nargs='*', help="Endpoint options")
        endpoint_add.add_argument("--messagegroups", nargs='*', help="Message group IDs")
        endpoint_add.add_argument("--channel", help="Channel identifier")
        endpoint_add.add_argument("--deprecated", help="Deprecation information")
        add_common_arguments(endpoint_add)
        endpoint_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_endpoint(args.id, args.usage, args.protocol, args.deployed, args.endpoints, args.options,
                                                                                                    args.messagegroups, args.documentation, args.description, args.labels, args.name,
                                                                                                    args.channel, args.deprecated
                                                                                                    ))

        endpoint_remove = endpoint_subparsers.add_parser("remove", help="Remove an endpoint")
        endpoint_remove.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_remove.set_defaults(func=lambda args: ManifestSubcommands(args.filename).remove_endpoint(args.id))

        endpoint_edit = endpoint_subparsers.add_parser("edit", help="Edit an endpoint")
        endpoint_edit.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_edit.add_argument("--usage", choices=["subscriber", "producer", "consumer"], help="Usage type")
        endpoint_edit.add_argument("--protocol", choices=["HTTP", "AMQP", "MQTT", "Kafka", "NATS"], help="Protocol")
        endpoint_edit.add_argument("--deployed", type=bool, help="Deployed status")
        endpoint_edit.add_argument("--endpoints", nargs='+', help="Endpoint URIs")
        endpoint_edit.add_argument("--options", nargs='*', help="Endpoint options")
        endpoint_edit.add_argument("--messagegroups", nargs='*', help="Message group IDs")
        endpoint_edit.add_argument("--channel", help="Channel identifier")
        endpoint_edit.add_argument("--deprecated", help="Deprecation information")
        add_common_arguments(endpoint_edit)
        endpoint_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_endpoint(args.id, args.usage, args.protocol, args.deployed, args.endpoints, args.options,
                                                                                                      args.messagegroups, args.documentation, args.description, args.labels, args.name,
                                                                                                      args.channel, args.deprecated
                                                                                                      ))

        endpoint_show = endpoint_subparsers.add_parser("show", help="Show an endpoint")
        endpoint_show.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_show.set_defaults(func=lambda args: ManifestSubcommands(args.filename).show_endpoint(args.id))

        endpoint_apply = endpoint_subparsers.add_parser("apply", help="Apply an endpoint JSON")
        endpoint_apply.add_argument("-f", "--file", required=True, help="JSON file containing endpoint data")
        endpoint_apply.set_defaults(func=lambda args: ManifestSubcommands(args.filename).apply_endpoint(args.file))

        messagegroup_subparsers = manifest_subparsers.add_parser("messagegroup", help="Manage message groups").add_subparsers(
            dest="messagegroup_command", help="Message group commands")

        messagegroup_add = messagegroup_subparsers.add_parser("add", help="Add a new message group")
        messagegroup_add.add_argument("--id", required=True, help="Message group ID")
        messagegroup_add.add_argument("--format", choices=["CloudEvents", "None"], help="Message group format")
        messagegroup_add.add_argument("--binding", help="Binding identifier")
        add_common_arguments(messagegroup_add)
        messagegroup_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_messagegroup(args.id, args.format, args.documentation, args.description, args.labels, args.name,
                                                                                                            args.binding
                                                                                                            ))

        messagegroup_remove = messagegroup_subparsers.add_parser("remove", help="Remove a message group")
        messagegroup_remove.add_argument("--id", required=True, help="Message group ID")
        messagegroup_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_messagegroup(args.id))

        messagegroup_edit = messagegroup_subparsers.add_parser("edit", help="Edit a message group")
        messagegroup_edit.add_argument("--id", required=True, help="Message group ID")
        messagegroup_edit.add_argument("--format", choices=["CloudEvents", "None"], help="Message group format")
        messagegroup_edit.add_argument("--binding", help="Binding identifier")
        add_common_arguments(messagegroup_edit)
        messagegroup_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_messagegroup(args.id, args.format, args.documentation, args.description, args.labels, args.name,
                                                                                                              args.binding
                                                                                                              ))

        messagegroup_show = messagegroup_subparsers.add_parser("show", help="Show a message group")
        messagegroup_show.add_argument("--id", required=True, help="Message group ID")
        messagegroup_show.set_defaults(func=lambda args: ManifestSubcommands(args.filename).show_messagegroup(args.id))

        messagegroup_apply = messagegroup_subparsers.add_parser("apply", help="Apply a message group JSON")
        messagegroup_apply.add_argument("-f", "--file", required=True, help="JSON file containing message group data")
        messagegroup_apply.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).apply_messagegroup(args.file))

        message_subparsers = manifest_subparsers.add_parser(
            "message", help="Manage messages").add_subparsers(dest="message_command", help="Message commands")

        message_add = message_subparsers.add_parser("add", help="Add a new message")
        message_add.add_argument("--groupid", required=True, help="Message group ID")
        message_add.add_argument("--id", required=True, help="Message ID")
        message_add.add_argument("--format", choices=["CloudEvents", "None"],
                                 help="Message format", default="CloudEvents")
        message_add.add_argument("--binding", choices=["AMQP", "MQTT", "NATS",
                                 "HTTP", "Kafka", "None"], help="Message binding", default="None")
        message_add.add_argument("--schemaformat", help="Schema format")
        message_add.add_argument("--schemagroup", help="Schema group ID")
        message_add.add_argument("--schemaid", help="Schema ID")
        message_add.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_add)
        message_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_message(args.groupid, args.id, args.format, args.binding, args.schemaformat, args.schemagroup, args.schemaid,
                                                                                                  args.schemaurl, args.documentation, args.description, args.labels, args.name
                                                                                                  ))

        message_remove = message_subparsers.add_parser("remove", help="Remove a message")
        message_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_remove.add_argument("--id", required=True, help="Message ID")
        message_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_message(args.groupid, args.id))

        message_edit = message_subparsers.add_parser("edit", help="Edit a message")
        message_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_edit.add_argument("--id", required=True, help="Message ID")
        message_edit.add_argument("--format", choices=["CloudEvents", "None"], help="Message format")
        message_edit.add_argument("--binding", choices=["AMQP", "MQTT",
                                  "NATS", "HTTP", "Kafka", "None"], help="Message binding")
        message_edit.add_argument("--schemaformat", help="Schema format")
        message_edit.add_argument("--schemagroup", help="Schema group ID")
        message_edit.add_argument("--schemaid", help="Schema ID")
        message_edit.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_edit)
        message_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_message(args.groupid, args.id, args.format, args.binding, args.schemaformat, args.schemagroup, args.schemaid,
                                                                                                    args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_cloudevent_subparsers = manifest_subparsers.add_parser(
            "cloudevent", help="Manage CloudEvents").add_subparsers(dest="cloudevents_command", help="CloudEvents commands")
        message_cloudevent_add = message_cloudevent_subparsers.add_parser("add", help="Add a new CloudEvent")
        message_cloudevent_add.add_argument("--groupid", required=True, help="Message group ID")
        message_cloudevent_add.add_argument("--id", required=True, help="Message ID and CloudEvents type")
        message_cloudevent_add.add_argument("--schemaformat", help="Schema format")
        message_cloudevent_add.add_argument("--schemagroup", help="Schema group ID")
        message_cloudevent_add.add_argument("--schemaid", help="Schema ID")
        message_cloudevent_add.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_cloudevent_add)

        def _add_cloudevent(args):
            sc = ManifestSubcommands(args.filename)
            sc.add_message(
                args.groupid, args.id, "CloudEvents/1.0", "None", args.schemaformat, args.schemagroup, args.schemaid,
                args.schemaurl, args.documentation, args.description, args.labels, args.name)
            sc.add_cloudevents_message_metadata(args.groupid, args.id, "specversion",
                                                "string", "CloudEvents version", "1.0", True)
            sc.add_cloudevents_message_metadata(args.groupid, args.id, "type", "string", "Event type", args.id, True)
            sc.add_cloudevents_message_metadata(args.groupid, args.id, "source",
                                                "string", "Event source", "{source}", True)
            return
        message_cloudevent_add.set_defaults(func=_add_cloudevent)

        message_cloudevent_edit = message_cloudevent_subparsers.add_parser("edit", help="Edit a CloudEvent")
        message_cloudevent_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_cloudevent_edit.add_argument("--id", required=True, help="Message ID and CloudEvents type")
        message_cloudevent_edit.add_argument("--schemaformat", help="Schema format")
        message_cloudevent_edit.add_argument("--schemagroup", help="Schema group ID")
        message_cloudevent_edit.add_argument("--schemaid", help="Schema ID")
        message_cloudevent_edit.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_cloudevent_edit)
        message_cloudevent_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_message(
            args.groupid, args.id, "CloudEvents/1.0", "None", args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_cloudevent_remove = message_cloudevent_subparsers.add_parser("remove", help="Remove a CloudEvent")
        message_cloudevent_remove.add_argument("--groupid", required=True, help="Message group ID", type=str)
        message_cloudevent_remove.add_argument("--id", required=True, help="Message ID and CloudEvents type", type=str)
        message_cloudevent_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_message(args.groupid, args.id))

        message_cloudevent_metadata_subparsers = message_cloudevent_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")
        message_cloudevent_metadata_add = message_cloudevent_metadata_subparsers.add_parser(
            "add", help="Add a new metadata field")
        message_cloudevent_metadata_add.add_argument("--groupid", required=True, help="Message group ID")
        message_cloudevent_metadata_add.add_argument("--id", required=True, help="Message ID")
        message_cloudevent_metadata_add.add_argument("--attribute", required=True, help="Attribute name")
        message_cloudevent_metadata_add.add_argument(
            "--type", choices=PROPERTY_TYPES, help="Metadata type", default="string")
        message_cloudevent_metadata_add.add_argument("--description", help="Metadata description")
        message_cloudevent_metadata_add.add_argument(
            "--value", help="Attribute value, may contain template expressions if the type is 'uritemplate'")
        message_cloudevent_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        message_cloudevent_metadata_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_cloudevents_message_metadata(
            args.groupid, args.id, args.attribute, args.type, args.description, args.value, args.required))

        message_cloudevent_metadata_edit = message_cloudevent_metadata_subparsers.add_parser(
            "edit", help="Edit a metadata field")
        message_cloudevent_metadata_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_cloudevent_metadata_edit.add_argument("--id", required=True, help="Message ID")
        message_cloudevent_metadata_edit.add_argument("--attribute", required=True, help="Attribute name")
        message_cloudevent_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Attribute type")
        message_cloudevent_metadata_edit.add_argument("--description", help="Attribute description")
        message_cloudevent_metadata_edit.add_argument(
            "--value", help="Attribute value, may contain template expressions if the type is 'uritemplate'")
        message_cloudevent_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        message_cloudevent_metadata_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_cloudevents_message_metadata(
            args.groupid, args.id, args.attribute, args.type, args.description, args.value, args.required))

        message_cloudevent_metadata_remove = message_cloudevent_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_cloudevent_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_cloudevent_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_cloudevent_metadata_remove.add_argument("--attribute", required=True, help="CloudEvents attribute")
        message_cloudevent_metadata_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_cloudevents_message_metadata(args.groupid, args.id, args.key))

        message_amqp_subparsers = manifest_subparsers.add_parser(
            "amqp", help="Manage AMQP").add_subparsers(dest="amqp_command", help="AMQP commands")
        message_amqp_metadata_subparsers = message_amqp_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_amqp_message(args):
            sc = ManifestSubcommands(args.filename)
            sc.add_message(args.groupid, args.id, "None", "AMQP/1.0", args.schemaformat, args.schemagroup,
                           args.schemaid, args.schemaurl, args.documentation, args.description, args.labels, args.name)
            sc.add_amqp_message_metadata(args.groupid, args.id, "properties",
                                         "subject", "string", args.id, "Subject", True)

        message_amqp_add = message_amqp_subparsers.add_parser("add", help="Add a new message")
        message_amqp_add.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_add.add_argument("--id", required=True, help="Message ID")
        message_amqp_add.add_argument("--schemaformat", help="Schema format")
        message_amqp_add.add_argument("--schemagroup", help="Schema group ID")
        message_amqp_add.add_argument("--schemaid", help="Schema ID")
        message_amqp_add.add_argument("--schemaurl", help="Schema URL")
        message_amqp_add.set_defaults(func=_add_amqp_message)

        message_amqp_edit = message_amqp_subparsers.add_parser("edit", help="Edit a message")
        message_amqp_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_edit.add_argument("--id", required=True, help="Message ID")
        message_amqp_edit.add_argument("--schemaformat", help="Schema format")
        message_amqp_edit.add_argument("--schemagroup", help="Schema group ID")
        message_amqp_edit.add_argument("--schemaid", help="Schema ID")
        message_amqp_edit.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_amqp_edit)
        message_amqp_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_message(
            args.groupid, args.id, "None", "AMQP/1.0", args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_amqp_remove = message_amqp_subparsers.add_parser("remove", help="Remove a message")
        message_amqp_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_remove.add_argument("--id", required=True, help="Message ID")
        message_amqp_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_message(args.groupid, args.id))

        message_amqp_metadata_add = message_amqp_metadata_subparsers.add_parser("add", help="Add a new metadata field")
        message_amqp_metadata_add.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_metadata_add.add_argument("--id", required=True, help="Message ID")
        message_amqp_metadata_add.add_argument("--section", required=True, choices=[
                                               "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_amqp_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_amqp_metadata_add.add_argument("--description", help="Metadata description")
        message_amqp_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        message_amqp_metadata_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_amqp_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.description, args.required))

        message_amqp_metadata_edit = message_amqp_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_amqp_metadata_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_metadata_edit.add_argument("--id", required=True, help="Message ID")
        message_amqp_metadata_edit.add_argument("--section", required=True, choices=[
                                                "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_edit.add_argument("--name", help="Metadata name")
        message_amqp_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_amqp_metadata_edit.add_argument("--description", help="Metadata description")
        message_amqp_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        message_amqp_metadata_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_amqp_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.description, args.required))

        message_amqp_metadata_remove = message_amqp_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_amqp_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_amqp_metadata_remove.add_argument("--section", required=True, choices=[
                                                  "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        message_amqp_metadata_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_amqp_message_metadata(args.groupid, args.id, args.name, args.section))

        message_mqtt_subparsers = manifest_subparsers.add_parser(
            "mqtt", help="Manage MQTT").add_subparsers(dest="mqtt_command", help="MQTT commands")
        message_mqtt_metadata_subparsers = message_mqtt_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_mqtt_message(args):
            sc = ManifestSubcommands(args.filename)
            sc.add_message(
                args.groupid, args.id, "None", "MQTT/" + args.mqtt_version, args.schemaformat, args.schemagroup, args.schemaid,
                args.schemaurl, args.documentation, args.description, args.labels, args.name)
            sc.add_mqtt_message_metadata(args.groupid, args.id, args.mqtt_version, "topic",
                                         "string", "{topic}/"+args.id,  "MQTT topic", True)

        message_mqtt_add = message_mqtt_subparsers.add_parser("add", help="Add a new message")
        message_mqtt_add.add_argument("--groupid", required=True, help="Message group ID")
        message_mqtt_add.add_argument("--id", required=True, help="Message ID")
        message_mqtt_add.add_argument("--mqtt_version", required=True,
                                      choices=["3", "5", "3.1.1", "5.0"], help="MQTT version")
        message_mqtt_add.add_argument("--schemaformat", help="Schema format")
        message_mqtt_add.add_argument("--schemagroup", help="Schema group ID")
        message_mqtt_add.add_argument("--schemaid", help="Schema ID")
        message_mqtt_add.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_mqtt_add)
        message_mqtt_add.set_defaults(func=_add_amqp_message)

        message_mqtt_edit = message_mqtt_subparsers.add_parser("edit", help="Edit a message")
        message_mqtt_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_mqtt_edit.add_argument("--id", required=True, help="Message ID")
        message_mqtt_edit.add_argument("--schemaformat", help="Schema format")
        message_mqtt_edit.add_argument("--schemagroup", help="Schema group ID")
        message_mqtt_edit.add_argument("--schemaid", help="Schema ID")
        message_mqtt_edit.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_mqtt_edit)
        message_mqtt_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_message(
            args.groupid, args.id, "None", "MQTT/" + args.mqtt_version, args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_mqtt_remove = message_mqtt_subparsers.add_parser("remove", help="Remove a message")
        message_mqtt_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_mqtt_remove.add_argument("--id", required=True, help="Message ID")
        message_mqtt_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_message(args.groupid, args.id))

        message_mqtt_metadata_add = message_mqtt_metadata_subparsers.add_parser("add", help="Add a new metadata field")
        message_mqtt_metadata_add.add_argument("--groupid", required=True, help="Message group ID")
        message_mqtt_metadata_add.add_argument("--id", required=True, help="Message ID")
        message_mqtt_metadata_add.add_argument("--mqtt_version", required=True,
                                               choices=["3", "5", "3.1.1", "5.0"], help="MQTT version")
        message_mqtt_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_mqtt_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_mqtt_metadata_add.add_argument("--value", required=True, help="Metadata value")
        message_mqtt_metadata_add.add_argument("--description", help="Metadata description")
        message_mqtt_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        message_mqtt_metadata_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_mqtt_message_metadata(
            args.groupid, args.id, args.mqtt_version, args.name, args.type, args.value, args.description, args.required))

        message_mqtt_metadata_edit = message_mqtt_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_mqtt_metadata_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_mqtt_metadata_edit.add_argument("--id", required=True, help="Message ID")
        message_mqtt_metadata_edit.add_argument("--mqtt_version", required=True,
                                                choices=["3", "5", "3.1.1", "5.0"], help="MQTT version")
        message_mqtt_metadata_edit.add_argument("--name", help="Metadata name")
        message_mqtt_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_mqtt_metadata_edit.add_argument("--value", help="Metadata value")
        message_mqtt_metadata_edit.add_argument("--description", help="Metadata description")
        message_mqtt_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        message_mqtt_metadata_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_mqtt_message_metadata(
            args.groupid, args.id, args.name, args.type, args.value, args.description, args.required))

        message_mqtt_metadata_remove = message_mqtt_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_mqtt_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_mqtt_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_mqtt_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        message_mqtt_metadata_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_mqtt_message_metadata(args.groupid, args.id, args.name))

        message_kafka_subparsers = manifest_subparsers.add_parser(
            "kafka", help="Manage Kafka").add_subparsers(dest="kafka_command", help="Kafka commands")
        message_kafka_metadata_subparsers = message_kafka_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_kafka_message(args):
            sc = ManifestSubcommands(args.filename)
            sc.add_message(args.groupid, args.id, "None", "Kafka", args.schemaformat, args.schemagroup, args.schemaid,
                           args.schemaurl, args.documentation, args.description, args.labels, args.name)
            sc.add_kafka_message_metadata(args.groupid, args.id, "headers", "message_type",
                                          "string", args.id, "Message ID", True)
            sc.add_kafka_message_metadata(args.groupid, args.id, None, "key", "string", "{key}", "Message key", False)

        message_kafka_add = message_kafka_subparsers.add_parser("add", help="Add a new message")
        message_kafka_add.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_add.add_argument("--id", required=True, help="Message ID")
        message_kafka_add.add_argument("--schemaformat", help="Schema format")
        message_kafka_add.add_argument("--schemagroup", help="Schema group ID")
        message_kafka_add.add_argument("--schemaid", help="Schema ID")
        message_kafka_add.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_kafka_add)
        message_kafka_add.set_defaults(func=_add_kafka_message)

        message_kafka_edit = message_kafka_subparsers.add_parser("edit", help="Edit a message")
        message_kafka_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_edit.add_argument("--id", required=True, help="Message ID")
        message_kafka_edit.add_argument("--schemaformat", help="Schema format")
        message_kafka_edit.add_argument("--schemagroup", help="Schema group ID")
        message_kafka_edit.add_argument("--schemaid", help="Schema ID")
        message_kafka_edit.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_kafka_edit)
        message_kafka_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_message(
            args.groupid, args.id, "None", "Kafka", args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_kafka_remove = message_kafka_subparsers.add_parser("remove", help="Remove a message")
        message_kafka_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_remove.add_argument("--id", required=True, help="Message ID")
        message_kafka_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_message(args.groupid, args.id))

        message_kafka_metadata_add = message_kafka_metadata_subparsers.add_parser(
            "add", help="Add a new metadata field")
        message_kafka_metadata_add.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_metadata_add.add_argument("--id", required=True, help="Message ID")
        message_kafka_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_kafka_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_kafka_metadata_add.add_argument("--description", help="Metadata description")
        message_kafka_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        message_kafka_metadata_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_kafka_message_metadata(
            args.groupid, args.id, args.name, args.type, args.description, args.required))

        message_kafka_metadata_edit = message_kafka_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_kafka_metadata_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_metadata_edit.add_argument("--id", required=True, help="Message ID")
        message_kafka_metadata_edit.add_argument("--name", help="Metadata name")
        message_kafka_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_kafka_metadata_edit.add_argument("--description", help="Metadata description")
        message_kafka_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        message_kafka_metadata_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_kafka_message_metadata(
            args.groupid, args.id, args.name, args.type, args.description, args.required))

        message_kafka_metadata_remove = message_kafka_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_kafka_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_kafka_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        message_kafka_metadata_remove.add_argument(
            "--section", required=True, choices=["headers"], help="Metadata section")
        message_kafka_metadata_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_kafka_message_metadata(args.groupid, args.id, args.section, args.name))

        message_http_subparsers = manifest_subparsers.add_parser(
            "http", help="Manage HTTP").add_subparsers(dest="http_command", help="HTTP commands")
        message_http_metadata_subparsers = message_http_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_http_message(args):
            sc = ManifestSubcommands(args.filename)
            sc.add_message(args.groupid, args.id, "None", "HTTP", args.schemaformat, args.schemagroup, args.schemaid,
                           args.schemaurl, args.documentation, args.description, args.labels, args.name)
            sc.add_http_message_metadata(args.groupid, args.id, "headers", "content-type",
                                         "string", "application/json", "Content type", True)
            sc.add_http_message_metadata(args.groupid, args.id, None, "method", "string", "POST", "HTTP method", True)

        message_http_add = message_http_subparsers.add_parser("add", help="Add a new message")
        message_http_add.add_argument("--groupid", required=True, help="Message group ID")
        message_http_add.add_argument("--id", required=True, help="Message ID")
        message_http_add.add_argument("--schemaformat", help="Schema format")
        message_http_add.add_argument("--schemagroup", help="Schema group ID")
        message_http_add.add_argument("--schemaid", help="Schema ID")
        message_http_add.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_http_add)
        message_http_add.set_defaults(func=_add_http_message)

        message_http_edit = message_http_subparsers.add_parser("edit", help="Edit a message")
        message_http_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_http_edit.add_argument("--id", required=True, help="Message ID")
        message_http_edit.add_argument("--schemaformat", help="Schema format")
        message_http_edit.add_argument("--schemagroup", help="Schema group ID")
        message_http_edit.add_argument("--schemaid", help="Schema ID")
        message_http_edit.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_http_edit)
        message_http_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_message(
            args.groupid, args.id, "None", "HTTP", args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_http_remove = message_http_subparsers.add_parser("remove", help="Remove a message")
        message_http_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_http_remove.add_argument("--id", required=True, help="Message ID")
        message_http_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_message(args.groupid, args.id))

        message_http_metadata_add = message_http_metadata_subparsers.add_parser("add", help="Add a new metadata field")
        message_http_metadata_add.add_argument("--groupid", required=True, help="Message group ID")
        message_http_metadata_add.add_argument("--id", required=True, help="Message ID")
        message_http_metadata_add.add_argument("--key", required=True, help="Metadata key")
        message_http_metadata_add.add_argument("--section", required=False,
                                               choices=["headers", "query"], help="Metadata section")
        message_http_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_http_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_http_metadata_add.add_argument("--description", help="Metadata description")
        message_http_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        message_http_metadata_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_http_message_metadata(
            args.groupid, args.id, args.name, args.type, args.description, args.required))

        message_http_metadata_edit = message_http_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_http_metadata_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_http_metadata_edit.add_argument("--id", required=True, help="Message ID")
        message_http_metadata_edit.add_argument("--key", required=True, help="Metadata key")
        message_http_metadata_edit.add_argument("--section", required=False,
                                                choices=["headers", "query"], help="Metadata section")
        message_http_metadata_edit.add_argument("--name", help="Metadata name")
        message_http_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_http_metadata_edit.add_argument("--description", help="Metadata description")
        message_http_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        message_http_metadata_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_http_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.description, args.required))

        message_http_metadata_remove = message_http_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_http_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_http_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_http_metadata_remove.add_argument("--name", required=True, help="Metadata key")
        message_http_metadata_remove.add_argument(
            "--section", required=False, choices=["headers", "query"], help="Metadata section")
        message_http_metadata_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_http_message_metadata(args.groupid, args.id, args.section, args.name))

        message_show = message_subparsers.add_parser("show", help="Show a message")
        message_show.add_argument("--groupid", required=True, help="Message group ID")
        message_show.add_argument("--id", required=True, help="Message ID")
        message_show.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).show_message(args.groupid, args.id))

        message_apply = message_subparsers.add_parser("apply", help="Apply a message JSON")
        message_apply.add_argument("-f", "--file", required=True, help="JSON file containing message data")
        message_apply.set_defaults(func=lambda args: ManifestSubcommands(args.filename).apply_message(args.file))

        schemagroup_subparsers = manifest_subparsers.add_parser("schemagroup", help="Manage schema groups").add_subparsers(
            dest="schemagroup_command", help="Schema group commands")

        schemagroup_add = schemagroup_subparsers.add_parser("add", help="Add a new schema group")
        schemagroup_add.add_argument("--id", required=True, help="Schema group ID")
        add_common_arguments(schemagroup_add)
        schemagroup_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_schemagroup(
            args.id, args.documentation, args.description, args.labels, args.name))

        schemagroup_remove = schemagroup_subparsers.add_parser("remove", help="Remove a schema group")
        schemagroup_remove.add_argument("--id", required=True, help="Schema group ID")
        schemagroup_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_schemagroup(args.id))

        schemagroup_edit = schemagroup_subparsers.add_parser("edit", help="Edit a schema group")
        schemagroup_edit.add_argument("--id", required=True, help="Schema group ID")
        add_common_arguments(schemagroup_edit)
        schemagroup_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_schemagroup(args.id, args.documentation, args.description, args.labels, args.name ))

        schemagroup_show = schemagroup_subparsers.add_parser("show", help="Show a schema group")
        schemagroup_show.add_argument("--id", required=True, help="Schema group ID")
        schemagroup_show.set_defaults(func=lambda args: ManifestSubcommands(args.filename).show_schemagroup(args.id))

        schemagroup_apply = schemagroup_subparsers.add_parser("apply", help="Apply a schema group JSON")
        schemagroup_apply.add_argument("-f", "--file", required=True, help="JSON file containing schema group data")
        schemagroup_apply.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).apply_schemagroup(args.file))

        schema_subparsers = manifest_subparsers.add_parser(
            "schemaversion", help="Manage schema versions").add_subparsers(dest="schema_command", help="Schema commands")

        schema_add = schema_subparsers.add_parser("add", help="Add a new schema version")
        schema_add.add_argument("--groupid", required=True, help="Schema group ID")
        schema_add.add_argument("--id", required=True, help="Schema ID")
        schema_add.add_argument("--format", required=True, help="Schema format")
        schema_add.add_argument("--versionid", help="Schema version ID")
        schema_add.add_argument("--schema", help="Inline schema")
        schema_add.add_argument("--schemaimport", help="Schema import file location or URL")
        schema_add.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(schema_add)
        schema_add.set_defaults(func=lambda args: ManifestSubcommands(args.filename).add_schemaversion(args.groupid, args.id, args.format, args.versionid, args.schema, args.schemaimport,
                                                                                                args.schemaurl, args.documentation, args.description, args.labels, args.name
                                                                                                ))

        schema_remove = schema_subparsers.add_parser("remove", help="Remove a schema or schema version")
        schema_remove.add_argument("--groupid", required=True, help="Schema group ID")
        schema_remove.add_argument("--id", required=True, help="Schema ID")
        schema_remove.add_argument("--versionid", required=True, help="Schema version ID")
        schema_remove.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).remove_schemaversion(args.groupid, args.id, args.versionid))

        schema_edit = schema_subparsers.add_parser("edit", help="Edit a schema or schema version")
        schema_edit.add_argument("--groupid", required=True, help="Schema group ID")
        schema_edit.add_argument("--id", required=True, help="Schema ID")
        schema_edit.add_argument("--format", help="Schema format")
        schema_edit.add_argument("--versionid", required=True, help="Schema version ID")
        schema_edit.add_argument("--schema", help="Inline schema")
        schema_edit.add_argument("--schemaimport", help="Schema import file location or URL")
        schema_edit.add_argument("--schemaurl", help="Schema URL")
        schema_edit.add_argument("--confirm_edit", action="store_true", help="Confirm schema edit")
        add_common_arguments(schema_edit)
        schema_edit.set_defaults(func=lambda args: ManifestSubcommands(args.filename).edit_schemaversion(args.groupid, args.id, args.versionid, args.format, args.schema, args.schemaimport,
                                                                                                  args.schemaurl, args.documentation, args.description, args.labels, args.name, args.confirm_edit
                                                                                                  ))

        schema_show = schema_subparsers.add_parser("show", help="Show a schema")
        schema_show.add_argument("--groupid", required=True, help="Schema group ID")
        schema_show.add_argument("--id", required=True, help="Schema ID")
        schema_show.set_defaults(func=lambda args: ManifestSubcommands(
            args.filename).show_schema(args.groupid, args.id))

        schema_apply = schema_subparsers.add_parser("apply", help="Apply a schema JSON")
        schema_apply.add_argument("-f", "--file", required=True, help="JSON file containing schema data")
        schema_apply.set_defaults(func=lambda args: ManifestSubcommands(args.filename).apply_schema(args.file))
