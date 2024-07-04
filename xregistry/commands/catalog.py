"""This module contains the CatalogSubcommands class, which provides methods to handle catalog subcommands."""

import json
import datetime
import argparse
from typing import List, Dict, Any, Optional
import requests

def current_time_iso() -> str:
    """Returns the current time in ISO format."""
    return datetime.datetime.now().isoformat()

class CatalogSubcommands:
    """Class containing methods to handle catalog subcommands."""

    def __init__(self):
        self.base_url = ""

    def set_base_url(self, uri: str) -> None:
        """Sets the base URL for the API."""
        self.base_url = uri

    def init_catalog(self, uri: str) -> None:
        """Initializes a new catalog by sending a POST request to the API."""
        self.set_base_url(uri)
        data = {
            "endpoints": {},
            "messagegroups": {},
            "schemagroups": {}
        }
        response = requests.post(self.base_url, json=data)
        if response.status_code != 200:
            raise ValueError(f"Failed to initialize catalog: {response.text}")

    def add_endpoint(self, uri: str, id: str, usage: str, protocol: str, endpoints: Optional[List[str]] = None,
                     options: Optional[Dict[str, Any]] = None, messagegroups: Optional[List[str]] = None, deployed: bool = False,
                     documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                     name: Optional[str] = None) -> None:
        """Adds an endpoint to the catalog."""
        self.set_base_url(uri)
        endpoint = {
            "id": id,
            "usage": usage,
            "protocol": protocol,
            "createdon": current_time_iso(),
            "modifiedon": current_time_iso(),
            "epoch": 0
        }
        if endpoints:
            endpoint["endpoints"] = endpoints
        if options:
            endpoint["options"] = options
        if messagegroups:
            endpoint["messagegroups"] = messagegroups
        if deployed:
            endpoint["deployed"] = deployed
        if documentation:
            endpoint["documentation"] = documentation
        if description:
            endpoint["description"] = description
        if labels:
            endpoint["labels"] = labels
        if name:
            endpoint["name"] = name
        response = requests.put(f"{self.base_url}/endpoints/{id}", json=endpoint)
        if response.status_code != 200:
            raise ValueError(f"Failed to add endpoint: {response.text}")

    def remove_endpoint(self, uri: str, id: str, epoch: int) -> None:
        """Removes an endpoint from the catalog."""
        self.set_base_url(uri)
        response = requests.delete(f"{self.base_url}/endpoints/{id}", params={"epoch": epoch})
        if response.status_code != 204:
            raise ValueError(f"Failed to remove endpoint: {response.text}")

    def edit_endpoint(self, uri: str, id: str, usage: Optional[str] = None, protocol: Optional[str] = None, endpoints: Optional[List[str]] = None,
                      options: Optional[Dict[str, Any]] = None, messagegroups: Optional[List[str]] = None, deployed: bool = None,
                      documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                      name: Optional[str] = None) -> None:
        """Edits an existing endpoint in the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/endpoints/{id}")
        if response.status_code != 200:
            raise ValueError(f"Endpoint with id {id} does not exist: {response.text}")
        endpoint = response.json()
        if usage:
            endpoint["usage"] = usage
        if protocol:
            endpoint["protocol"] = protocol
        if endpoints:
            endpoint["endpoints"] = endpoints
        if options:
            endpoint["options"] = options
        if messagegroups:
            endpoint["messagegroups"] = messagegroups
        if deployed is not None:
            endpoint["deployed"] = deployed
        if documentation:
            endpoint["documentation"] = documentation
        if description:
            endpoint["description"] = description
        if labels:
            endpoint["labels"] = labels
        if name:
            endpoint["name"] = name
        endpoint["modifiedon"] = current_time_iso()
        endpoint["epoch"] += 1
        response = requests.put(f"{self.base_url}/endpoints/{id}", json=endpoint)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit endpoint: {response.text}")

    def show_endpoint(self, uri: str, id: str) -> None:
        """Shows an endpoint from the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/endpoints/{id}")
        if response.status_code != 200:
            raise ValueError(f"Endpoint with id {id} does not exist: {response.text}")
        print(json.dumps(response.json(), indent=2))

    def apply_endpoint(self, uri: str, file: str) -> None:
        """Applies an endpoint from a file."""
        self.set_base_url(uri)
        with open(file, 'r', encoding='utf-8') as ef:
            endpoint = json.load(ef)
            id = endpoint["id"]
            response = requests.get(f"{self.base_url}/endpoints/{id}")
            if response.status_code == 200:
                self.edit_endpoint(uri, id, **endpoint)
            else:
                self.add_endpoint(uri, **endpoint)

    def add_messagegroup(self, uri: str, id: str, format: str, binding: str, messages: Optional[Dict[str, Any]] = None,
                         description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                         name: Optional[str] = None) -> None:
        """Adds a messagegroup to the catalog."""
        self.set_base_url(uri)
        messagegroup = {
            "id": id,
            "format": format,
            "binding": binding,
            "createdon": current_time_iso(),
            "modifiedon": current_time_iso(),
            "epoch": 0
        }
        if messages:
            messagegroup["messages"] = messages
        if description:
            messagegroup["description"] = description
        if documentation:
            messagegroup["documentation"] = documentation
        if labels:
            messagegroup["labels"] = labels
        if name:
            messagegroup["name"] = name
        response = requests.put(f"{self.base_url}/messagegroups/{id}", json=messagegroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to add messagegroup: {response.text}")

    def remove_messagegroup(self, uri: str, id: str, epoch: int) -> None:
        """Removes a messagegroup from the catalog."""
        self.set_base_url(uri)
        response = requests.delete(f"{self.base_url}/messagegroups/{id}", params={"epoch": epoch})
        if response.status_code != 204:
            raise ValueError(f"Failed to remove messagegroup: {response.text}")

    def edit_messagegroup(self, uri: str, id: str, format: Optional[str] = None, binding: Optional[str] = None, messages: Optional[Dict[str, Any]] = None,
                          description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                          name: Optional[str] = None) -> None:
        """Edits an existing messagegroup in the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/messagegroups/{id}")
        if response.status_code != 200:
            raise ValueError(f"Messagegroup with id {id} does not exist: {response.text}")
        messagegroup = response.json()
        if format:
            messagegroup["format"] = format
        if binding:
            messagegroup["binding"] = binding
        if messages:
            messagegroup["messages"] = messages
        if description:
            messagegroup["description"] = description
        if documentation:
            messagegroup["documentation"] = documentation
        if labels:
            messagegroup["labels"] = labels
        if name:
            messagegroup["name"] = name
        messagegroup["modifiedon"] = current_time_iso()
        messagegroup["epoch"] += 1
        response = requests.put(f"{self.base_url}/messagegroups/{id}", json=messagegroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit messagegroup: {response.text}")

    def show_messagegroup(self, uri: str, id: str) -> None:
        """Shows a messagegroup from the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/messagegroups/{id}")
        if response.status_code != 200:
            raise ValueError(f"Messagegroup with id {id} does not exist: {response.text}")
        print(json.dumps(response.json(), indent=2))

    def apply_messagegroup(self, uri: str, file: str) -> None:
        """Applies a messagegroup from a file."""
        self.set_base_url(uri)
        with open(file, 'r', encoding='utf-8') as ef:
            messagegroup = json.load(ef)
            id = messagegroup["id"]
            response = requests.get(f"{self.base_url}/messagegroups/{id}")
            if response.status_code == 200:
                self.edit_messagegroup(uri, id, **messagegroup)
            else:
                self.add_messagegroup(uri, **messagegroup)

    def add_schemagroup(self, uri: str, id: str, format: str, schemas: Optional[Dict[str, Any]] = None,
                        description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                        name: Optional[str] = None) -> None:
        """Adds a schemagroup to the catalog."""
        self.set_base_url(uri)
        schemagroup = {
            "id": id,
            "format": format,
            "createdon": current_time_iso(),
            "modifiedon": current_time_iso(),
            "epoch": 0
        }
        if schemas:
            schemagroup["schemas"] = schemas
        if description:
            schemagroup["description"] = description
        if documentation:
            schemagroup["documentation"] = documentation
        if labels:
            schemagroup["labels"] = labels
        if name:
            schemagroup["name"] = name
        response = requests.put(f"{self.base_url}/schemagroups/{id}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to add schemagroup: {response.text}")

    def remove_schemagroup(self, uri: str, id: str, epoch: int) -> None:
        """Removes a schemagroup from the catalog."""
        self.set_base_url(uri)
        response = requests.delete(f"{self.base_url}/schemagroups/{id}", params={"epoch": epoch})
        if response.status_code != 204:
            raise ValueError(f"Failed to remove schemagroup: {response.text}")

    def edit_schemagroup(self, uri: str, id: str, format: Optional[str] = None, schemas: Optional[Dict[str, Any]] = None,
                         description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                         name: Optional[str] = None) -> None:
        """Edits an existing schemagroup in the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/schemagroups/{id}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {id} does not exist: {response.text}")
        schemagroup = response.json()
        if format:
            schemagroup["format"] = format
        if schemas:
            schemagroup["schemas"] = schemas
        if description:
            schemagroup["description"] = description
        if documentation:
            schemagroup["documentation"] = documentation
        if labels:
            schemagroup["labels"] = labels
        if name:
            schemagroup["name"] = name
        schemagroup["modifiedon"] = current_time_iso()
        schemagroup["epoch"] += 1
        response = requests.put(f"{self.base_url}/schemagroups/{id}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit schemagroup: {response.text}")

    def show_schemagroup(self, uri: str, id: str) -> None:
        """Shows a schemagroup from the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/schemagroups/{id}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {id} does not exist: {response.text}")
        print(json.dumps(response.json(), indent=2))

    def apply_schemagroup(self, uri: str, file: str) -> None:
        """Applies a schemagroup from a file."""
        self.set_base_url(uri)
        with open(file, 'r', encoding='utf-8') as ef:
            schemagroup = json.load(ef)
            id = schemagroup["id"]
            response = requests.get(f"{self.base_url}/schemagroups/{id}")
            if response.status_code == 200:
                self.edit_schemagroup(uri, id, **schemagroup)
            else:
                self.add_schemagroup(uri, **schemagroup)

    def add_schema(self, uri: str, groupid: str, id: str, format: str, versionid: str = "1", schema: Optional[str] = None,
                   schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                   labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Adds a schema to a schemagroup in the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        schema_obj = {
            "id": id,
            "format": format,
            "createdon": current_time_iso(),
            "modifiedon": current_time_iso(),
            "epoch": 0
        }
        if schema:
            try:
                json.loads(schema)
                schema_obj["schema"] = schema
            except json.JSONDecodeError:
                schema_obj["schemabase64"] = schema.encode("utf-8").hex()
        elif schemaimport:
            with open(schemaimport, 'r', encoding='utf-8') as sf:
                schema_content = sf.read()
                try:
                    json.loads(schema_content)
                    schema_obj["schema"] = schema_content
                except json.JSONDecodeError:
                    schema_obj["schemabase64"] = schema_content.encode("utf-8").hex()
        elif schemaurl:
            schema_obj["schemaurl"] = schemaurl
        if description:
            schema_obj["description"] = description
        if documentation:
            schema_obj["documentation"] = documentation
        if labels:
            schema_obj["labels"] = labels
        if name:
            schema_obj["name"] = name

        if "schemas" not in schemagroup:
            schemagroup["schemas"] = {}
        schemagroup["schemas"][id] = schema_obj

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to add schema: {response.text}")

    def remove_schema(self, uri: str, groupid: str, id: str, versionid: Optional[str] = None) -> None:
        """Removes a schema from a schemagroup in the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or id not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {id} does not exist in schemagroup {groupid}")

        if versionid:
            if "versions" in schemagroup["schemas"][id]:
                versions = schemagroup["schemas"][id]["versions"]
                if versionid in versions:
                    del versions[versionid]
                    if not versions:
                        del schemagroup["schemas"][id]
                else:
                    raise ValueError(f"Version id {versionid} does not exist in schema {id}")
            else:
                raise ValueError(f"No versions found for schema {id}")
        else:
            del schemagroup["schemas"][id]

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove schema: {response.text}")

    def edit_schema(self, uri: str, groupid: str, id: str, format: Optional[str] = None, versionid: str = "1", schema: Optional[str] = None,
                    schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                    labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Edits an existing schema in a schemagroup in the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or id not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {id} does not exist in schemagroup {groupid}")

        schema_obj = schemagroup["schemas"][id]
        if format:
            schema_obj["format"] = format
        if schema:
            try:
                json.loads(schema)
                schema_obj["schema"] = schema
            except json.JSONDecodeError:
                schema_obj["schemabase64"] = schema.encode("utf-8").hex()
        elif schemaimport:
            with open(schemaimport, 'r', encoding='utf-8') as sf:
                schema_content = sf.read()
                try:
                    json.loads(schema_content)
                    schema_obj["schema"] = schema_content
                except json.JSONDecodeError:
                    schema_obj["schemabase64"] = schema_content.encode("utf-8").hex()
        elif schemaurl:
            schema_obj["schemaurl"] = schemaurl
        if description:
            schema_obj["description"] = description
        if documentation:
            schema_obj["documentation"] = documentation
        if labels:
            schema_obj["labels"] = labels
        if name:
            schema_obj["name"] = name

        schema_obj["modifiedon"] = current_time_iso()
        schema_obj["epoch"] += 1

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit schema: {response.text}")

    def show_schema(self, uri: str, groupid: str, id: str) -> None:
        """Shows a schema from a schemagroup in the catalog."""
        self.set_base_url(uri)
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or id not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {id} does not exist in schemagroup {groupid}")

        print(json.dumps(schemagroup["schemas"][id], indent=2))

    def apply_schema(self, uri: str, file: str) -> None:
        """Applies a schema from a file."""
        self.set_base_url(uri)
        with open(file, 'r', encoding='utf-8') as sf:
            schema = json.load(sf)
            groupid = schema["groupid"]
            id = schema["id"]
            response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
            if response.status_code == 200:
                self.edit_schema(uri, groupid, id, **schema)
            else:
                self.add_schema(uri, groupid, id, **schema)

    def add_catalog_parsers(self, subparsers: _SubParsersAction[argparse.ArgumentParser]):
        catalog_parser = subparsers.add_parser('catalog', help="Operate on catalog via webservice")
        catalog_subparsers = catalog_parser.add_subparsers(dest="catalog_command", help="Catalog command to execute")

        # Endpoint commands
        add_endpoint_parser = catalog_subparsers.add_parser('endpoint_add', help="Add an endpoint")
        add_endpoint_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        add_endpoint_parser.add_argument('id', type=str, help="ID of the endpoint")
        add_endpoint_parser.add_argument('usage', type=str, help="Usage of the endpoint")
        add_endpoint_parser.add_argument('protocol', type=str, choices=["HTTP", "AMQP", "MQTT", "Kafka", "NATS"], help="Protocol of the endpoint")
        add_endpoint_parser.set_defaults(func=CatalogSubcommands().add_endpoint)

        remove_endpoint_parser = catalog_subparsers.add_parser('endpoint_remove', help="Remove an endpoint")
        remove_endpoint_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        remove_endpoint_parser.add_argument('id', type=str, help="ID of the endpoint")
        remove_endpoint_parser.add_argument('epoch', type=int, help="Epoch of the endpoint")
        remove_endpoint_parser.set_defaults(func=CatalogSubcommands().remove_endpoint)

        edit_endpoint_parser = catalog_subparsers.add_parser('endpoint_edit', help="Edit an endpoint")
        edit_endpoint_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        edit_endpoint_parser.add_argument('id', type=str, help="ID of the endpoint")
        edit_endpoint_parser.add_argument('--usage', type=str, help="Usage of the endpoint")
        edit_endpoint_parser.add_argument('--protocol', type=str, choices=["HTTP", "AMQP", "MQTT", "Kafka", "NATS"], help="Protocol of the endpoint")
        edit_endpoint_parser.set_defaults(func=CatalogSubcommands().edit_endpoint)

        show_endpoint_parser = catalog_subparsers.add_parser('endpoint_show', help="Show an endpoint")
        show_endpoint_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        show_endpoint_parser.add_argument('id', type=str, help="ID of the endpoint")
        show_endpoint_parser.set_defaults(func=CatalogSubcommands().show_endpoint)

        apply_endpoint_parser = catalog_subparsers.add_parser('endpoint_apply', help="Apply an endpoint from a file")
        apply_endpoint_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        apply_endpoint_parser.add_argument('file', type=str, help="File containing the endpoint definition")
        apply_endpoint_parser.set_defaults(func=CatalogSubcommands().apply_endpoint)

        # MessageGroup commands
        add_messagegroup_parser = catalog_subparsers.add_parser('messagegroup_add', help="Add a messagegroup")
        add_messagegroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        add_messagegroup_parser.add_argument('id', type=str, help="ID of the messagegroup")
        add_messagegroup_parser.add_argument('--format', type=str, choices=["CloudEvents", "None"], help="Format of the messagegroup")
        add_messagegroup_parser.set_defaults(func=CatalogSubcommands().add_messagegroup)

        remove_messagegroup_parser = catalog_subparsers.add_parser('messagegroup_remove', help="Remove a messagegroup")
        remove_messagegroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        remove_messagegroup_parser.add_argument('id', type=str, help="ID of the messagegroup")
        remove_messagegroup_parser.add_argument('epoch', type=int, help="Epoch of the messagegroup")
        remove_messagegroup_parser.set_defaults(func=CatalogSubcommands().remove_messagegroup)

        edit_messagegroup_parser = catalog_subparsers.add_parser('messagegroup_edit', help="Edit a messagegroup")
        edit_messagegroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        edit_messagegroup_parser.add_argument('id', type=str, help="ID of the messagegroup")
        edit_messagegroup_parser.add_argument('--format', type=str, choices=["CloudEvents", "None"], help="Format of the messagegroup")
        edit_messagegroup_parser.set_defaults(func=CatalogSubcommands().edit_messagegroup)

        show_messagegroup_parser = catalog_subparsers.add_parser('messagegroup_show', help="Show a messagegroup")
        show_messagegroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        show_messagegroup_parser.add_argument('id', type=str, help="ID of the messagegroup")
        show_messagegroup_parser.set_defaults(func=CatalogSubcommands().show_messagegroup)

        apply_messagegroup_parser = catalog_subparsers.add_parser('messagegroup_apply', help="Apply a messagegroup from a file")
        apply_messagegroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        apply_messagegroup_parser.add_argument('file', type=str, help="File containing the messagegroup definition")
        apply_messagegroup_parser.set_defaults(func=CatalogSubcommands().apply_messagegroup)

        # SchemaGroup commands
        add_schemagroup_parser = catalog_subparsers.add_parser('schemagroup_add', help="Add a schemagroup")
        add_schemagroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        add_schemagroup_parser.add_argument('id', type=str, help="ID of the schemagroup")
        add_schemagroup_parser.add_argument('--format', type=str, help="Format of the schemagroup")
        add_schemagroup_parser.set_defaults(func=CatalogSubcommands().add_schemagroup)

        remove_schemagroup_parser = catalog_subparsers.add_parser('schemagroup_remove', help="Remove a schemagroup")
        remove_schemagroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        remove_schemagroup_parser.add_argument('id', type=str, help="ID of the schemagroup")
        remove_schemagroup_parser.add_argument('epoch', type=int, help="Epoch of the schemagroup")
        remove_schemagroup_parser.set_defaults(func=CatalogSubcommands().remove_schemagroup)

        edit_schemagroup_parser = catalog_subparsers.add_parser('schemagroup_edit', help="Edit a schemagroup")
        edit_schemagroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        edit_schemagroup_parser.add_argument('id', type=str, help="ID of the schemagroup")
        edit_schemagroup_parser.add_argument('--format', type=str, help="Format of the schemagroup")
        edit_schemagroup_parser.set_defaults(func=CatalogSubcommands().edit_schemagroup)

        show_schemagroup_parser = catalog_subparsers.add_parser('schemagroup_show', help="Show a schemagroup")
        show_schemagroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        show_schemagroup_parser.add_argument('id', type=str, help="ID of the schemagroup")
        show_schemagroup_parser.set_defaults(func=CatalogSubcommands().show_schemagroup)

        apply_schemagroup_parser = catalog_subparsers.add_parser('schemagroup_apply', help="Apply a schemagroup from a file")
        apply_schemagroup_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        apply_schemagroup_parser.add_argument('file', type=str, help="File containing the schemagroup definition")
        apply_schemagroup_parser.set_defaults(func=CatalogSubcommands().apply_schemagroup)

        # Schema commands
        add_schema_parser = catalog_subparsers.add_parser('schema_add', help="Add a schema to a schemagroup")
        add_schema_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        add_schema_parser.add_argument('groupid', type=str, help="ID of the schemagroup")
        add_schema_parser.add_argument('id', type=str, help="ID of the schema")
        add_schema_parser.add_argument('format', type=str, help="Format of the schema")
        add_schema_parser.add_argument('--versionid', type=str, default="1", help="Version ID of the schema")
        add_schema_parser.add_argument('--schema', type=str, help="Literal schema content")
        add_schema_parser.add_argument('--schemaimport', type=str, help="File to import schema content from")
        add_schema_parser.add_argument('--schemaurl', type=str, help="URL of the schema content")
        add_schema_parser.set_defaults(func=CatalogSubcommands().add_schema)

        remove_schema_parser = catalog_subparsers.add_parser('schema_remove', help="Remove a schema from a schemagroup")
        remove_schema_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        remove_schema_parser.add_argument('groupid', type=str, help="ID of the schemagroup")
        remove_schema_parser.add_argument('id', type=str, help="ID of the schema")
        remove_schema_parser.add_argument('--versionid', type=str, help="Version ID of the schema")
        remove_schema_parser.set_defaults(func=CatalogSubcommands().remove_schema)

        edit_schema_parser = catalog_subparsers.add_parser('schema_edit', help="Edit a schema in a schemagroup")
        edit_schema_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        edit_schema_parser.add_argument('groupid', type=str, help="ID of the schemagroup")
        edit_schema_parser.add_argument('id', type=str, help="ID of the schema")
        edit_schema_parser.add_argument('format', type=str, help="Format of the schema")
        edit_schema_parser.add_argument('--versionid', type=str, default="1", help="Version ID of the schema")
        edit_schema_parser.add_argument('--schema', type=str, help="Literal schema content")
        edit_schema_parser.add_argument('--schemaimport', type=str, help="File to import schema content from")
        edit_schema_parser.add_argument('--schemaurl', type=str, help="URL of the schema content")
        edit_schema_parser.set_defaults(func=CatalogSubcommands().edit_schema)

        show_schema_parser = catalog_subparsers.add_parser('schema_show', help="Show a schema in a schemagroup")
        show_schema_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        show_schema_parser.add_argument('groupid', type=str, help="ID of the schemagroup")
        show_schema_parser.add_argument('id', type=str, help="ID of the schema")
        show_schema_parser.set_defaults(func=CatalogSubcommands().show_schema)

        apply_schema_parser = catalog_subparsers.add_parser('schema_apply', help="Apply a schema to a schemagroup from a file")
        apply_schema_parser.add_argument('uri', type=str, help="Base URI for the catalog API")
        apply_schema_parser.add_argument('file', type=str, help="File containing the schema definition")
        apply_schema_parser.set_defaults(func=CatalogSubcommands().apply_schema)

    def process_catalog_command(self, args):
        command = args.catalog_command
        catalog_subcommands = CatalogSubcommands()

        if command == 'endpoint_add':
            catalog_subcommands.add_endpoint(args.uri, args.id, args.usage, args.protocol)
        elif command == 'endpoint_remove':
            catalog_subcommands.remove_endpoint(args.uri, args.id, args.epoch)
        elif command == 'endpoint_edit':
            catalog_subcommands.edit_endpoint(args.uri, args.id, args.usage, args.protocol)
        elif command == 'endpoint_show':
            catalog_subcommands.show_endpoint(args.uri, args.id)
        elif command == 'endpoint_apply':
            catalog_subcommands.apply_endpoint(args.uri, args.file)

        elif command == 'messagegroup_add':
            catalog_subcommands.add_messagegroup(args.uri, args.id, args.format)
        elif command == 'messagegroup_remove':
            catalog_subcommands.remove_messagegroup(args.uri, args.id, args.epoch)
        elif command == 'messagegroup_edit':
            catalog_subcommands.edit_messagegroup(args.uri, args.id, args.format)
        elif command == 'messagegroup_show':
            catalog_subcommands.show_messagegroup(args.uri, args.id)
        elif command == 'messagegroup_apply':
            catalog_subcommands.apply_messagegroup(args.uri, args.file)

        elif command == 'schemagroup_add':
            catalog_subcommands.add_schemagroup(args.uri, args.id, args.format)
        elif command == 'schemagroup_remove':
            catalog_subcommands.remove_schemagroup(args.uri, args.id, args.epoch)
        elif command == 'schemagroup_edit':
            catalog_subcommands.edit_schemagroup(args.uri, args.id, args.format)
        elif command == 'schemagroup_show':
            catalog_subcommands.show_schemagroup(args.uri, args.id)
        elif command == 'schemagroup_apply':
            catalog_subcommands.apply_schemagroup(args.uri, args.file)

        elif command == 'schema_add':
            catalog_subcommands.add_schema(args.uri, args.groupid, args.id, args.format, args.versionid, args.schema, args.schemaimport, args.schemaurl)
        elif command == 'schema_remove':
            catalog_subcommands.remove_schema(args.uri, args.groupid, args.id, args.versionid)
        elif command == 'schema_edit':
            catalog_subcommands.edit_schema(args.uri, args.groupid, args.id, args.format, args.versionid, args.schema, args.schemaimport, args.schemaurl)
        elif command == 'schema_show':
            catalog_subcommands.show_schema(args.uri, args.groupid, args.id)
        elif command == 'schema_apply':
            catalog_subcommands.apply_schema(args.uri, args.file)


# Example usage:
# catalog = CatalogSubcommands()
# catalog.add_endpoint("http://example.com/api", "endpoint1", "usage1", "protocol1")
