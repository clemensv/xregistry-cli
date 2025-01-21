"""This module contains the CatalogSubcommands class, which provides methods to handle catalog subcommands."""

from email import message
import json
import datetime
import argparse
import re
from typing import List, Dict, Any, Optional
import requests

PROPERTY_TYPES = ["string", "int", "timestamp", "uritemplate"]

def current_time_iso() -> str:
    """Returns the current time in ISO format."""
    return datetime.datetime.now(tz=datetime.UTC).isoformat()

class CatalogSubcommands:
    """Class containing methods to handle catalog subcommands."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def add_endpoint(self, endpointid: str, usage: str, protocol: str, endpoints: Optional[List[str]] = None,
                     options: Optional[Dict[str, Any]] = None, messagegroups: Optional[List[str]] = None, deployed: bool = False,
                     documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                     name: Optional[str] = None, channel: Optional[str] = None, deprecated: Optional[bool] = None) -> None:
        """Adds an endpoint to the catalog."""
        
        endpoint = {
            "endpointid": endpointid,
            "usage": usage,
            "protocol": protocol,
            "createdat": current_time_iso(),
            "modifiedat": current_time_iso(),
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
        if channel:
            endpoint["channel"] = channel
        if deprecated:
            endpoint["deprecated"] = deprecated
        response = requests.put(f"{self.base_url}/endpoints/{endpointid}", json=endpoint)
        if response.status_code != 201 and response.status_code != 200:
            raise ValueError(f"Failed to add endpoint: {response.text}")
        
    def apply_manifest(self, file: str) -> None:
        """Applies a manifest from a file."""
        with open(file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            response = requests.put(f"{self.base_url}/?nested", json=manifest)
            if response.status_code != 200 and response.status_code != 201:
                raise ValueError(f"Failed to apply manifest {response.status_code}: {response.text}")
   
    def remove_endpoint(self, endpointid: str) -> None:
        """Removes an endpoint from the catalog."""
        
        # Fetch the current endpoint to get the epoch
        response = requests.get(f"{self.base_url}/endpoints/{endpointid}")
        if response.status_code != 200:
            raise ValueError(f"Endpoint with id {endpointid} does not exist: {response.text}")
        endpoint = response.json()
        epoch = endpoint.get("epoch", 0)
        
        # Delete the endpoint
        response = requests.delete(f"{self.base_url}/endpoints/{endpointid}", params={"epoch": epoch})
        if response.status_code != 204:
            raise ValueError(f"Failed to remove endpoint: {response.text}")

    def edit_endpoint(self, endpointid: str, usage: Optional[str] = None, protocol: Optional[str] = None, endpoints: Optional[List[str]] = None,
                      options: Optional[Dict[str, Any]] = None, messagegroups: Optional[List[str]] = None, deployed: bool|None = None,
                      documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                      name: Optional[str] = None, channel: Optional[str] = None, deprecated: Optional[bool] = None) -> None:
        """Edits an existing endpoint in the catalog."""
        
        response = requests.get(f"{self.base_url}/endpoints/{endpointid}")
        if response.status_code != 200:
            raise ValueError(f"Endpoint with id {endpointid} does not exist: {response.text}")
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
        if channel:
            endpoint["channel"] = channel
        if deprecated:
            endpoint["deprecated"] = deprecated
        endpoint["modifiedat"] = current_time_iso()
        response = requests.put(f"{self.base_url}/endpoints/{endpointid}", json=endpoint)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit endpoint: {response.text}")

    def show_endpoint(self, endpointid: str) -> None:
        """Shows an endpoint from the catalog."""
        
        response = requests.get(f"{self.base_url}/endpoints/{endpointid}")
        if response.status_code != 200:
            raise ValueError(f"Endpoint with id {endpointid} does not exist: {response.text}")
        print(json.dumps(response.json(), indent=2))

    def apply_endpoint(self, file: str) -> None:
        """Applies an endpoint from a file."""
        
        with open(file, 'r', encoding='utf-8') as ef:
            endpoint = json.load(ef)
            endpointid = endpoint["endpointid"]
            response = requests.get(f"{self.base_url}/endpoints/{endpointid}")
            if response.status_code == 200:
                self.edit_endpoint(endpointid, **endpoint)
            else:
                self.add_endpoint(**endpoint)

    def add_messagegroup(self, messagegroupid: str, envelope: str, protocol: str, messages: Optional[Dict[str, Any]] = None,
                         description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                         name: Optional[str] = None) -> None:
        """Adds a messagegroup to the catalog."""
        
        messagegroup = {
            "messagegroupid": messagegroupid,
            "envelope": envelope,
            "protocol": protocol,
            "createdat": current_time_iso(),
            "modifiedat": current_time_iso(),
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
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}", json=messagegroup)
        if response.status_code != 200 and response.status_code != 201:
            raise ValueError(f"Failed to add messagegroup: {response.text}")

    def remove_messagegroup(self, messagegroupid: str) -> None:
        """Removes a messagegroup from the catalog."""
        
        # Fetch the current messagegroup to get the epoch
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}")
        if response.status_code != 200:
            raise ValueError(f"Messagegroup with id {messagegroupid} does not exist: {response.text}")
        messagegroup = response.json()
        epoch = messagegroup.get("epoch", 0)
        
        # Delete the messagegroup
        response = requests.delete(f"{self.base_url}/messagegroups/{messagegroupid}", params={"epoch": epoch})
        if response.status_code != 204:
            raise ValueError(f"Failed to remove messagegroup: {response.text}")

    def edit_messagegroup(self, messagegroupid: str, envelope: Optional[str] = None, protocol: Optional[str] = None, messages: Optional[Dict[str, Any]] = None,
                          description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                          name: Optional[str] = None) -> None:
        """Edits an existing messagegroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}")
        if response.status_code != 200:
            raise ValueError(f"Messagegroup with id {messagegroupid} does not exist: {response.text}")
        messagegroup = response.json()
        if envelope:
            messagegroup["envelope"] = envelope
        if protocol:
            messagegroup["protocol"] = protocol
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
        messagegroup["modifiedat"] = current_time_iso()
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}", json=messagegroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit messagegroup: {response.text}")

    def show_messagegroup(self, messagegroupid: str) -> None:
        """Shows a messagegroup from the catalog."""
        
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}")
        if response.status_code != 200:
            raise ValueError(f"Messagegroup with id {messagegroupid} does not exist: {response.text}")
        print(json.dumps(response.json(), indent=2))

    def apply_messagegroup(self, file: str) -> None:
        """Applies a messagegroup from a file."""
        
        with open(file, 'r', encoding='utf-8') as ef:
            messagegroup = json.load(ef)
            messagegroupid = messagegroup["messagegroupid"]
            response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}")
            if response.status_code == 200:
                self.edit_messagegroup(messagegroupid, **messagegroup)
            else:
                self.add_messagegroup(**messagegroup)

    def add_schemagroup(self, schemagroupid: str, format: str, schemas: Optional[Dict[str, Any]] = None,
                        description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                        name: Optional[str] = None) -> None:
        """Adds a schemagroup to the catalog."""
        
        schemagroup = {
            "schemagroupid": schemagroupid,
            "format": format,
            "createdat": current_time_iso(),
            "modifiedat": current_time_iso(),
            "epoch": 0
        }
        schemagroup["schemas"] = schemas if schemas else {}
        if description:
            schemagroup["description"] = description
        if documentation:
            schemagroup["documentation"] = documentation
        if labels:
            schemagroup["labels"] = labels
        if name:
            schemagroup["name"] = name
        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200 and response.status_code != 201:
            raise ValueError(f"Failed to add schemagroup: {response.text}")

    def remove_schemagroup(self, schemagroupid: str) -> None:
        """Removes a schemagroup from the catalog."""
        
        # Fetch the current schemagroup to get the epoch
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        schemagroup = response.json()
        epoch = schemagroup.get("epoch", 0)
        
        # Delete the schemagroup
        response = requests.delete(f"{self.base_url}/schemagroups/{schemagroupid}", params={"epoch": epoch})
        if response.status_code != 204:
            raise ValueError(f"Failed to remove schemagroup: {response.text}")

    def edit_schemagroup(self, schemagroupid: str, format: Optional[str] = None, schemas: Optional[Dict[str, Any]] = None,
                         description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                         name: Optional[str] = None) -> None:
        """Edits an existing schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
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
        schemagroup["modifiedat"] = current_time_iso()
        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit schemagroup: {response.text}")

    def show_schemagroup(self, schemagroupid: str) -> None:
        """Shows a schemagroup from the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}?inline=*")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        print(json.dumps(response.json(), indent=2))

    def apply_schemagroup(self, file: str) -> None:
        """Applies a schemagroup from a file."""
        
        with open(file, 'r', encoding='utf-8') as ef:
            schemagroup = json.load(ef)
            schemagroupid = schemagroup["schemagroupid"]
            response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
            if response.status_code == 200:
                self.edit_schemagroup(schemagroupid, **schemagroup)
            else:
                self.add_schemagroup(**schemagroup)

    def add_message(self, messagegroupid: str, messageid: str, envelope: str, protocol: str, dataschemaformat: Optional[str] = None,
                    dataschemagroup: Optional[str] = None, dataschemaid: Optional[str] = None, dataschemauri: Optional[str] = None,
                    documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                    name: Optional[str] = None) -> None:
        """Adds a message to a message group in the catalog."""
        
        message = {
            "messageid": messageid,
            "envelope": envelope,
            "protocol": protocol,
            "createdat": current_time_iso(),
            "modifiedat": current_time_iso(),
            "epoch": 0
        }
        if dataschemaformat:
            message["dataschemaformat"] = dataschemaformat
        if dataschemagroup:
            message["dataschemagroup"] = dataschemagroup
        if dataschemaid:
            message["dataschemaid"] = dataschemaid
        if dataschemauri:
            message["dataschemauri"] = dataschemauri
        if documentation:
            message["documentation"] = documentation
        if description:
            message["description"] = description
        if labels:
            message["labels"] = labels
        if name:
            message["name"] = name

        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200 and response.status_code != 201:
            raise ValueError(f"Failed to add message: {response.text}")

    def remove_message(self, groupid: str, messageid: str) -> None:
        """Removes a message from a message group in the catalog."""
        
        # Fetch the current message to get the epoch
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Message with id {messageid} does not exist: {response.text}")
        message = response.json()
        epoch = message.get("epoch", 0)
        
        # Delete the message
        response = requests.delete(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", params={"epoch": epoch})
        if response.status_code != 204:
            raise ValueError(f"Failed to remove message: {response.text}")

    def edit_message(self, messagegroupid: str, messageid: str, envelope: Optional[str] = None, protocol: Optional[str] = None, dataschemaformat: Optional[str] = None,
                     dataschemagroup: Optional[str] = None, dataschemaid: Optional[str] = None, dataschemauri: Optional[str] = None,
                     documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                     name: Optional[str] = None) -> None:
        """Edits an existing message in a message group in the catalog."""
        
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Message with id {messageid} does not exist: {response.text}")
        message = response.json()
        if envelope:
            message["envelope"] = envelope
        if protocol:
            message["protocol"] = protocol
        if dataschemaformat:
            message["dataschemaformat"] = dataschemaformat
        if dataschemagroup:
            message["dataschemagroup"] = dataschemagroup
        if dataschemaid:
            message["dataschemaid"] = dataschemaid
        if dataschemauri:
            message["dataschemauri"] = dataschemauri
        if documentation:
            message["documentation"] = documentation
        if description:
            message["description"] = description
        if labels:
            message["labels"] = labels
        if name:
            message["name"] = name
        message["modifiedat"] = current_time_iso()
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit message: {response.text}")
    
    def remove_protocol_option(self, messageid: str, message: Any, section: str|None, name: str) -> None:
        """Removes a protocol option from a message in the catalog."""
         # Remove the metadata entry
        if "protocoloptions" in message:
            obj = message["protocoloptions"]
            if section:
                if section in obj:
                    obj = message["protocoloptions"][section]
                else:
                    raise ValueError(f"Section {section} not found in message {messageid}")
            if name in obj:
                del obj[name]           
            else:
                raise ValueError(f"Metadata entry {name} not found in message {messageid}")
        else:
            raise ValueError(f"No protocoloptions found for message {messageid}")

    def set_protocol_option(self, message:Any, section: str|None, name: str, type: str, value: str|None, description: str, required: bool) -> None:
        """Adds a protocol option to a message."""
        obj: Any = {}
        if "protocoloptions" not in message:
            obj = message["protocoloptions"] = {}
        if section not in message["protocoloptions"]:
            obj = message["protocoloptions"][section] = {}
        obj[name] = {}
        if type:
            obj[name]["type"] = type
        if value:
            obj[name]["value"] = value
        if description:
            obj[name]["description"] = description
        if required:
            obj[name]["required"] = required
        

    def remove_amqp_message_metadata(self, messagegroupid: str, messageid: str, section: str|None, name: str) -> None:
        """Removes AMQP message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "AMQP/1.0":
            raise ValueError(f"Message {messageid} is not an AMQP message")
        
        self.remove_protocol_option(messageid, message, section, name)
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove AMQP message metadata: {response.text}")

    def add_amqp_message_metadata(self, messagegroupid: str, messageid: str, section: str|None, name: str, type: str, value: str|None, description: str, required: bool) -> None:
        """Adds AMQP message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
     
        if "protocol" not in message or message["protocol"] != "AMQP/1.0":
            raise ValueError(f"Message {messageid} is not an AMQP message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)

        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add AMQP message metadata: {response.text}")

    def edit_amqp_message_metadata(self, messagegroupid: str, messageid: str, section: str|None, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Edits AMQP message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "AMQP/1.0":
            raise ValueError(f"Message {messageid} is not an AMQP message")
        
        # Update the metadata entry
        self.set_protocol_option(message, section, name, type, value, description, required)
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit AMQP message metadata: {response.text}")

    def add_mqtt_message_metadata(self, messagegroupid: str, messageid: str, mqtt_version: str, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Adds MQTT message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "MQTT/5.0" and message["protocol"] != "MQTT/3.1.1":
            raise ValueError(f"Message {messageid} is not an MQTT message")
        
        self.set_protocol_option(message, None, name, type, value, description, required)
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add MQTT message metadata: {response.text}")

    def remove_mqtt_message_metadata(self, messagegroupid: str, messageid: str, section:str|None, name: str) -> None:
        """Removes MQTT message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "MQTT/5.0" and message["protocol"] != "MQTT/3.1.1":
            raise ValueError(f"Message {messageid} is not an MQTT message")
        
        self.remove_protocol_option(messageid, message, section, name)
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove MQTT message metadata: {response.text}")

    def edit_mqtt_message_metadata(self, messagegroupid: str, messageid: str, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Edits MQTT message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "MQTT/5.0" and message["protocol"] != "MQTT/3.1.1":
            raise ValueError(f"Message {messageid} is not an MQTT message")
        
        self.set_protocol_option(message, None, name, type, value, description, required)
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit MQTT message metadata: {response.text}")

    def add_kafka_message_metadata(self, messagegroupid: str, messageid: str, section: Optional[str], name: str, type: str, value: str, description: str, required: bool) -> None:
        """Adds Kafka message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "KAFKA":
            raise ValueError(f"Message {messageid} is not a Kafka message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)

        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add Kafka message metadata: {response.text}")

    def remove_kafka_message_metadata(self, messagegroupid: str, messageid: str, section: Optional[str], name: str) -> None:
        """Removes Kafka message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "KAFKA":
            raise ValueError(f"Message {messageid} is not a Kafka message")
        
        self.remove_protocol_option(messageid, message, section, name)
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove Kafka message metadata: {response.text}")

    def edit_kafka_message_metadata(self, groupid: str, messageid: str, section: Optional[str], name: str, type: str, value: str, description: str, required: bool) -> None:
        """Edits Kafka message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "KAFKA":
            raise ValueError(f"Message {messageid} is not a Kafka message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)

        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit Kafka message metadata: {response.text}")

    def add_http_message_metadata(self, groupid: str, messageid: str, section: str | None, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Adds HTTP message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "HTTP/1.1":
            raise ValueError(f"Message {messageid} is not an HTTP message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add HTTP message metadata: {response.text}")

    def remove_http_message_metadata(self, messagegroupid: str, messageid: str, section: str | None, name: str) -> None:
        """Removes HTTP message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "HTTP/1.1":
            raise ValueError(f"Message {messageid} is not an HTTP message")

        self.remove_protocol_option(messageid, message, section, name) 
       
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove HTTP message metadata: {response.text}")

    def edit_http_message_metadata(self, messagegroupid: str, messageid: str, section: str | None, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Edits HTTP message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "HTTP/1.1":
            raise ValueError(f"Message {messageid} is not an HTTP message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)        
       
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit HTTP message metadata: {response.text}")

    def set_envelope_metadata(self, message:Any,name: str, type: str, value: str, description: str, required: bool) -> None:
        """Sets envelope metadata for a message."""

        if "envelopemetadata" not in message:
            obj = message["envelopemetadata"] = {}
        else:
            obj = message["envelopemetadata"]
        obj[name] = {}
        if type:
            obj[name]["type"] = type
        if value:
            obj[name]["value"] = value
        if description:
            obj[name]["description"] = description
        if required:
            obj[name]["required"] = required

    def remove_envelope_metadata(self, messageid: str, message: Any,name: str) -> None:
        """Removes envelope metadata from a message in the catalog."""
        
        # Remove the metadata entry
        if "envelopemetadata" in message:
            obj = message["envelopemetadata"]
            if name in obj:
                del obj[name]           
            else:
                raise ValueError(f"Metadata entry {name} not found in message {messageid}")
        else:
            raise ValueError(f"No envelopemetadata found for message {messageid}")
        

    def add_cloudevents_message_metadata(self, messagegroupid: str, messageid: str, attribute: str, type: str, description: str, value: str, required: bool) -> None:
        """Adds CloudEvents message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "envelope" not in message or message["envelope"] != "CloudEvents/1.0":
            raise ValueError(f"Message {messageid} is not a CloudEvents message")
        
        self.set_envelope_metadata(message, attribute, type, value, description, required)
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add CloudEvents message metadata: {response.text}")

    def edit_cloudevents_message_metadata(self, messagegroupid: str, messageid: str, attribute: str, type: str, description: str, value: str, required: bool) -> None:
        """Edits CloudEvents message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "envelope" not in message or message["envelope"] != "CloudEvents/1.0":
            raise ValueError(f"Message {messageid} is not a CloudEvents message")
        
        self.remove_envelope_metadata(messageid, message, attribute)

        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit CloudEvents message metadata: {response.text}")

    def remove_cloudevents_message_metadata(self, messagegroupid: str, messageid: str, attribute: str) -> None:
        """Removes CloudEvents message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        # Remove the metadata entry
        if "metadata" in message:
            message["metadata"] = [m for m in message["metadata"] if m["attribute"] != attribute]
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{messagegroupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove CloudEvents message metadata: {response.text}")

    def add_schema(self, schemagroupid: str, schemaid: str, format: str, versionid: str = "1", schema: Optional[str] = None,
                   schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                   labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Adds a schema to a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        schemagroup = response.json()

        if not format:
            raise ValueError("Schema format is required")

        schema_obj = {
            "schemaid": schemaid,
            "format": format,
            "createdat": current_time_iso(),
            "modifiedat": current_time_iso(),
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
        schemagroup["schemas"][schemaid] = schema_obj

        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200 and response.status_code != 201:
            raise ValueError(f"Failed to add schema: {response.text}")

    def add_schemaversion(self, schemagroupid: str, schemaid: str, format: str, versionid: str = "1", schema: Optional[str] = None,
                          schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                          labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> Any:
        """Adds a schema version to a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        schemagroup = response.json()

        schema_version = {
            "schemaid": schemaid,
            "format": format,
            "versionid": versionid,
            "createdat": current_time_iso(),
            "modifiedat": current_time_iso(),
            "epoch": 0
        }
        if schema:
            try:
                json.loads(schema)
                schema_version["schema"] = schema
            except json.JSONDecodeError:
                schema_version["schemabase64"] = schema.encode("utf-8").hex()
        elif schemaimport:
            with open(schemaimport, 'r', encoding='utf-8') as sf:
                schema_content = sf.read()
                try:
                    json.loads(schema_content)
                    schema_version["schema"] = schema_content
                except json.JSONDecodeError:
                    schema_version["schemabase64"] = schema_content.encode("utf-8").hex()
        elif schemaurl:
            schema_version["schemaurl"] = schemaurl
        if description:
            schema_version["description"] = description
        if documentation:
            schema_version["documentation"] = documentation
        if labels:
            schema_version["labels"] = labels
        if name:
            schema_version["name"] = name

        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}/schemas/{schemaid}/versions/{versionid}$structure", json=schema_version)
        if response.status_code != 200 and response.status_code != 201:
            raise ValueError(f"Failed to add schema version: {response.text}")
        return response.json()
        
    def edit_schemaversion(self, schemagroupid: str, schemaid: str, versionid: str, format: Optional[str] = None, schema: Optional[str] = None,
                            schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                            labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Edits an existing schema version in a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {schemagroupid}")
        
        if "versions" not in schemagroup["schemas"][schemaid] or versionid not in schemagroup["schemas"][schemaid]["versions"]:
            raise ValueError(f"Version with id {versionid} does not exist for schema {schemaid}")
        
        schema_obj = schemagroup["schemas"][schemaid]["versions"][versionid]
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

        schema_obj["modifiedat"] = current_time_iso()
        
        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit schema version: {response.text}")
        
    def remove_schemaversion(self, schemagroupid: str, schemaid: str, versionid: str) -> None:
        """Removes a schema version from a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {schemagroupid}")
        
        if "versions" not in schemagroup["schemas"][schemaid] or versionid not in schemagroup["schemas"][schemaid]["versions"]:
            raise ValueError(f"Version with id {versionid} does not exist for schema {schemaid}")
        
        del schemagroup["schemas"][schemaid]["versions"][versionid]
        if not schemagroup["schemas"][schemaid]["versions"]:
            del schemagroup["schemas"][schemaid]

        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove schema version: {response.text}")


    def remove_schema(self, schemagroupid: str, schemaid: str, versionid: Optional[str] = None) -> None:
        """Removes a schema from a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {schemagroupid}")

        if versionid:
            if "versions" in schemagroup["schemas"][schemaid]:
                versions = schemagroup["schemas"][schemaid]["versions"]
                if versionid in versions:
                    del versions[versionid]
                    if not versions:
                        del schemagroup["schemas"][schemaid]
                else:
                    raise ValueError(f"Version id {versionid} does not exist in schema {schemaid}")
            else:
                raise ValueError(f"No versions found for schema {schemaid}")
        else:
            del schemagroup["schemas"][schemaid]

        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove schema: {response.text}")

    def edit_schema(self, schemagroupid: str, schemaid: str, format: Optional[str] = None, versionid: str = "1", schema: Optional[str] = None,
                    schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                    labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Edits an existing schema in a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {schemagroupid}")

        schema_obj = schemagroup["schemas"][schemaid]
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

        schema_obj["modifiedat"] = current_time_iso()
        
        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit schema: {response.text}")

    def show_schema(self, schemagroupid: str, schemaid: str) -> None:
        """Shows a schema from a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {schemagroupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {schemagroupid}")

        print(json.dumps(schemagroup["schemas"][schemaid], indent=2))

    def show_message(self, groupid: str, messageid: str) -> None:
        """Shows a message from a message group in the catalog."""
        
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Message with id {messageid} does not exist in message group {groupid}")
        message = response.json()

        print(json.dumps(message, indent=2))

    def apply_schema(self, file: str) -> None:
        """Applies a schema from a file."""
        
        with open(file, 'r', encoding='utf-8') as sf:
            schema = json.load(sf)
            groupid = schema["schemagroupid"]
            schemaid = schema["schemaid"]
            response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
            if response.status_code == 200:
                self.edit_schema(groupid, schemaid, **schema)
            else:
                self.add_schema(groupid, schemaid, **schema)

    @classmethod
    @classmethod
    def add_parsers(cls, manifest_parser: argparse.ArgumentParser):
        """
        Add subparsers for the manifest commands.

        Args:
            subparsers (Any): The subparsers object to add the subcommands to.
        """

        manifest_subparsers = manifest_parser.add_subparsers(help="Manifest commands")

        def add_authentication_arguments(parser):
            """
            Add common arguments to the parser.

            Args:
                parser (ArgumentParser): The parser to add arguments to.
            """
            parser.add_argument("--catalog", required=True, help="Catalog URL")
            parser.add_argument("--authmode", choices=["none", "basic", "bearer"], help="Authentication mode")
            parser.add_argument("--username", help="Username")
            parser.add_argument("--password", help="Password")
            parser.add_argument("--token", help="Bearer token")
        
        apply_parser = manifest_subparsers.add_parser("apply", help="Apply a manifest JSON")
        apply_parser.add_argument("-f", "--file", required=True, help="JSON file containing manifest data")
        add_authentication_arguments(apply_parser)
        apply_parser.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).apply_manifest(args.file))

        endpoint_subparsers = manifest_subparsers.add_parser("endpoint", help="Manage endpoints").add_subparsers(
            dest="endpoint_command", help="Endpoint commands")

        endpoint_add = endpoint_subparsers.add_parser("add", help="Add a new endpoint")
        endpoint_add.add_argument("--endpointid", required=True, help="Endpoint ID")
        endpoint_add.add_argument("--description", help="Endpoint description")
        endpoint_add.add_argument("--documentation", help="Endpoint documentation URL")
        endpoint_add.add_argument("--name", help="Endpoint name")
        endpoint_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Endpoint labels (key=value pairs)")
        endpoint_add.add_argument("--usage", required=True,
                                  choices=["subscriber", "producer", "consumer"], help="Usage type")
        endpoint_add.add_argument("--protocol", choices=["HTTP", "AMQP/1.0", "MQTT/3.1.1", "MQTT/5.0", "KAFKA", "NATS"], help="Protocol")
        endpoint_add.add_argument("--deployed", type=bool, help="Deployed status")
        endpoint_add.add_argument("--endpoints", nargs='+', help="Endpoint URIs")
        endpoint_add.add_argument("--options", nargs='*', help="Endpoint options")
        endpoint_add.add_argument("--messagegroups", nargs='*', help="Message group IDs")
        endpoint_add.add_argument("--channel", help="Channel identifier")
        endpoint_add.add_argument("--deprecated", help="Deprecation information")
        add_authentication_arguments(endpoint_add)
        endpoint_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_endpoint(args.endpointid, args.usage, args.protocol, args.deployed, args.endpoints, args.options,
                                                                                                    args.messagegroups, args.documentation, args.description, args.labels, args.name,
                                                                                                    args.channel, args.deprecated
                                                                                                    ))

        endpoint_remove = endpoint_subparsers.add_parser("remove", help="Remove an endpoint")
        endpoint_remove.add_argument("--endpointid", required=True, help="Endpoint ID")
        add_authentication_arguments(endpoint_remove)
        endpoint_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_endpoint(args.endpointid))
        
        endpoint_edit = endpoint_subparsers.add_parser("edit", help="Edit an endpoint")
        endpoint_edit.add_argument("--endpointid", required=True, help="Endpoint ID")
        endpoint_edit.add_argument("--description", help="Endpoint description")
        endpoint_edit.add_argument("--documentation", help="Endpoint documentation URL")
        endpoint_edit.add_argument("--name", help="Endpoint name")
        endpoint_edit.add_argument("--usage", choices=["subscriber", "producer", "consumer"], help="Usage type")
        endpoint_edit.add_argument("--protocol", choices=["HTTP", "AMQP/1.0", "MQTT/3.1.1", "MQTT/5.0", "KAFKA", "NATS"], help="Protocol")
        endpoint_edit.add_argument("--deployed", type=bool, help="Deployed status")
        endpoint_edit.add_argument("--endpoints", nargs='+', help="Endpoint URIs")
        endpoint_edit.add_argument("--options", nargs='*', help="Endpoint options")
        endpoint_edit.add_argument("--messagegroups", nargs='*', help="Message group IDs")
        endpoint_edit.add_argument("--channel", help="Channel identifier")
        endpoint_edit.add_argument("--deprecated", help="Deprecation information")
        add_authentication_arguments(endpoint_edit)
        endpoint_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_endpoint(args.endpointid, args.usage, args.protocol, args.deployed, args.endpoints, args.options,
                                                                                                      args.messagegroups, args.documentation, args.description, args.labels, args.name,
                                                                                                      args.channel, args.deprecated
                                                                                                      ))

        endpoint_show = endpoint_subparsers.add_parser("show", help="Show an endpoint")
        endpoint_show.add_argument("--endpointid", required=True, help="Endpoint ID")
        add_authentication_arguments(endpoint_show)
        endpoint_show.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).show_endpoint(args.endpointid))

        endpoint_apply = endpoint_subparsers.add_parser("apply", help="Apply an endpoint JSON")
        endpoint_apply.add_argument("-f", "--file", required=True, help="JSON file containing endpoint data")
        add_authentication_arguments(endpoint_apply)
        endpoint_apply.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).apply_endpoint(args.file))

        messagegroup_subparsers = manifest_subparsers.add_parser("messagegroup", help="Manage message groups").add_subparsers(
            dest="messagegroup_command", help="Message group commands")

        messagegroup_add = messagegroup_subparsers.add_parser("add", help="Add a new message group")
        messagegroup_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        messagegroup_add.add_argument("--description", help="Message group description")
        messagegroup_add.add_argument("--documentation", help="Message group documentation URL")
        messagegroup_add.add_argument("--name", help="Message group name")
        messagegroup_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message group labels (key=value pairs)")
        messagegroup_add.add_argument("--envelope", choices=["CloudEvents/1.0", "None"], help="Message group envelope")
        messagegroup_add.add_argument("--protocol", help="protocol identifier")
        add_authentication_arguments(messagegroup_add)
        messagegroup_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_messagegroup(
            messagegroupid=args.messagegroupid,
            envelope=args.envelope,
            protocol=args.protocol,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))        
        
        messagegroup_remove = messagegroup_subparsers.add_parser("remove", help="Remove a message group")
        messagegroup_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        add_authentication_arguments(messagegroup_remove)
        messagegroup_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_messagegroup(args.messagegroupid))

        messagegroup_edit = messagegroup_subparsers.add_parser("edit", help="Edit a message group")
        messagegroup_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        messagegroup_edit.add_argument("--description", help="Message group description")
        messagegroup_edit.add_argument("--documentation", help="Message group documentation URL")
        messagegroup_edit.add_argument("--name", help="Message group name")
        messagegroup_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message group labels (key=value pairs)")
        messagegroup_edit.add_argument("--envelope", choices=["CloudEvents/1.0", "None"], help="Message group envelope")
        messagegroup_edit.add_argument("--protocol", help="protocol identifier")
        add_authentication_arguments(messagegroup_edit)
        messagegroup_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_messagegroup(
            messagegroupid=args.messagegroupid,
            envelope=args.envelope,
            protocol=args.protocol,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))

        messagegroup_show = messagegroup_subparsers.add_parser("show", help="Show a message group")
        messagegroup_show.add_argument("--messagegroupid", required=True, help="Message group ID")
        add_authentication_arguments(messagegroup_show)
        messagegroup_show.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).show_messagegroup(args.messagegroupid))

        messagegroup_apply = messagegroup_subparsers.add_parser("apply", help="Apply a message group JSON")
        messagegroup_apply.add_argument("-f", "--file", required=True, help="JSON file containing message group data")
        add_authentication_arguments(messagegroup_apply)
        messagegroup_apply.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).apply_messagegroup(args.file))

        message_subparsers = manifest_subparsers.add_parser(
            "message", help="Manage messages").add_subparsers(dest="message_command", help="Message commands")

        message_add = message_subparsers.add_parser("add", help="Add a new message")
        message_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_add.add_argument("--messageid", required=True, help="Message ID")
        message_add.add_argument("--description", help="Message description")
        message_add.add_argument("--documentation", help="Message documentation URL")
        message_add.add_argument("--name", help="Message name")
        message_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_add.add_argument("--envelope", choices=["CloudEvents/1.0", "None"],
                                 help="Message envelope", default="CloudEvents/1.0")
        message_add.add_argument("--protocol", choices=["AMQP/1.0", "MQTT/3.1.1", "MQTT/5.0", "NATS",
                                 "HTTP", "KAFKA", "None"], help="Message protocol", default="None")
        message_add.add_argument("--dataschemaformat", help="Schema format")
        message_add.add_argument("--dataschemagroup", help="Schema group ID")
        message_add.add_argument("--dataschemaid", help="Schema ID")
        message_add.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_add)
        message_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_message(
            messagegroupid=args.messagegroupid,
            messageid=args.messageid,
            envelope=args.envelope,
            protocol=args.protocol,
            dataschemaformat=args.dataschemaformat,
            dataschemagroup=args.dataschemagroup,
            dataschemaid=args.dataschemaid,
            dataschemauri=args.dataschemauri,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))
          
        message_remove = message_subparsers.add_parser("remove", help="Remove a message")
        message_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_remove.add_argument("--messageid", required=True, help="Message ID")
        add_authentication_arguments(message_remove)
        message_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_message(args.messagegroupid, args.messageid))

        message_edit = message_subparsers.add_parser("edit", help="Edit a message")
        message_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_edit.add_argument("--messageid", required=True, help="Message ID")
        message_edit.add_argument("--description", help="Message description")
        message_edit.add_argument("--documentation", help="Message documentation URL")
        message_edit.add_argument("--name", help="Message name")
        message_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")  
        message_edit.add_argument("--envelope", choices=["CloudEvents/1.0", "None"], help="Message envelope", default="CloudEvents/1.0")
        message_edit.add_argument("--protocol", choices=["AMQP/1.0", "MQTT/3.1.1", "MQTT/5.0",
                                  "NATS", "HTTP", "KAFKA", "None"], help="Message protocol", default="None")
        message_edit.add_argument("--dataschemaformat", help="Schema format")
        message_edit.add_argument("--dataschemagroup", help="Schema group ID")
        message_edit.add_argument("--dataschemaid", help="Schema ID")
        message_edit.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_edit)
        message_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            messagegroupid=args.messagegroupid,
            messageid=args.messageid,
            envelope=args.envelope,
            protocol=args.protocol,
            dataschemaformat=args.dataschemaformat,
            dataschemagroup=args.dataschemagroup,
            dataschemaid=args.dataschemaid,
            dataschemauri=args.dataschemauri,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name))

        message_cloudevent_subparsers = manifest_subparsers.add_parser(
            "cloudevent", help="Manage CloudEvents").add_subparsers(dest="cloudevents_command", help="CloudEvents commands")
        message_cloudevent_add = message_cloudevent_subparsers.add_parser("add", help="Add a new CloudEvent")
        message_cloudevent_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_cloudevent_add.add_argument("--messageid", required=True, help="Message ID and CloudEvents type")
        message_cloudevent_add.add_argument("--description", help="Message description")
        message_cloudevent_add.add_argument("--documentation", help="Message documentation URL")
        message_cloudevent_add.add_argument("--name", help="Message name")
        message_cloudevent_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_cloudevent_add.add_argument("--dataschemaformat", help="Schema format")
        message_cloudevent_add.add_argument("--dataschemagroup", help="Schema group ID")
        message_cloudevent_add.add_argument("--dataschemaid", help="Schema ID")
        message_cloudevent_add.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_cloudevent_add)

        def _add_cloudevent(args):
            sc = CatalogSubcommands(args.catalog)
            sc.add_message(
                args.messagegroupid, args.messageid, "CloudEvents/1.0", "None", args.dataschemaformat, args.dataschemagroup, args.dataschemaid,
                args.dataschemauri, args.documentation, args.description, args.labels, args.name)
            sc.add_cloudevents_message_metadata(args.messagegroupid, args.messageid, "specversion",
                                                "string", "CloudEvents version", "1.0", True)
            sc.add_cloudevents_message_metadata(args.messagegroupid, args.messageid, "type", "string", "Event type", args.messageid, True)
            sc.add_cloudevents_message_metadata(args.messagegroupid, args.messageid, "source",
                                                "string", "Event source", "{source}", True)
            return
        message_cloudevent_add.set_defaults(func=_add_cloudevent)

        message_cloudevent_edit = message_cloudevent_subparsers.add_parser("edit", help="Edit a CloudEvent")
        message_cloudevent_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_cloudevent_edit.add_argument("--messageid", required=True, help="Message ID and CloudEvents type")
        message_cloudevent_edit.add_argument("--description", help="Message description")
        message_cloudevent_edit.add_argument("--documentation", help="Message documentation URL")
        message_cloudevent_edit.add_argument("--name", help="Message name")
        message_cloudevent_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_cloudevent_edit.add_argument("--dataschemaformat", help="Schema format")
        message_cloudevent_edit.add_argument("--dataschemagroup", help="Schema group ID")
        message_cloudevent_edit.add_argument("--dataschemaid", help="Schema ID")
        message_cloudevent_edit.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_cloudevent_edit)
        message_cloudevent_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            args.messagegroupid, args.messageid, "CloudEvents/1.0", "None", args.dataschemaformat, args.dataschemagroup, args.dataschemaid,
            args.dataschemauri, args.documentation, args.description, args.labels, args.name))

        message_cloudevent_remove = message_cloudevent_subparsers.add_parser("remove", help="Remove a CloudEvent")
        message_cloudevent_remove.add_argument("--messagegroupid", required=True, help="Message group ID", type=str)
        message_cloudevent_remove.add_argument("--messageid", required=True, help="Message ID and CloudEvents type", type=str)
        add_authentication_arguments(message_cloudevent_remove)
        message_cloudevent_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_message(args.messagegroupid, args.messageid))

        message_cloudevent_metadata_subparsers = message_cloudevent_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")
        message_cloudevent_metadata_add = message_cloudevent_metadata_subparsers.add_parser(
            "add", help="Add a new metadata field")
        message_cloudevent_metadata_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_cloudevent_metadata_add.add_argument("--messageid", required=True, help="Message ID")
        message_cloudevent_metadata_add.add_argument("--attribute", required=True, help="Attribute name")
        message_cloudevent_metadata_add.add_argument(
            "--type", choices=PROPERTY_TYPES, help="Metadata type", default="string")
        message_cloudevent_metadata_add.add_argument("--description", help="Metadata description")
        message_cloudevent_metadata_add.add_argument(
            "--value", help="Attribute value, may contain template expressions if the type is 'uritemplate'")
        message_cloudevent_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_cloudevent_metadata_add)
        message_cloudevent_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_cloudevents_message_metadata(
            args.messagegroupid, args.messageid, args.attribute, args.type, args.description, args.value, args.required))

        message_cloudevent_metadata_edit = message_cloudevent_metadata_subparsers.add_parser(
            "edit", help="Edit a MQTT metadata field")
        message_cloudevent_metadata_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_cloudevent_metadata_edit.add_argument("--messageid", required=True, help="Message ID")
        message_cloudevent_metadata_edit.add_argument("--attribute", required=True, help="Attribute name")
        message_cloudevent_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Attribute type")
        message_cloudevent_metadata_edit.add_argument("--description", help="Attribute description")
        message_cloudevent_metadata_edit.add_argument(
            "--value", help="Attribute value, may contain template expressions if the type is 'uritemplate'")
        message_cloudevent_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_cloudevent_metadata_edit)
        message_cloudevent_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_cloudevents_message_metadata(
            messagegroupid=args.messagegroupid, 
            messageid=args.messageid, 
            attribute=args.attribute, 
            type=args.type, 
            description=args.description, 
            value=args.value, 
            required=args.required
        ))

        message_cloudevent_metadata_remove = message_cloudevent_metadata_subparsers.add_parser(
            "remove", help="Remove a MQTT metadata field")
        message_cloudevent_metadata_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_cloudevent_metadata_remove.add_argument("--messageid", required=True, help="Message ID")
        message_cloudevent_metadata_remove.add_argument("--attribute", required=True, help="CloudEvents attribute")
        add_authentication_arguments(message_cloudevent_metadata_remove)
        message_cloudevent_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_cloudevents_message_metadata(args.messagegroupid, args.messageid, args.key))

        message_amqp_subparsers = manifest_subparsers.add_parser(
            "amqp", help="Manage AMQP messages").add_subparsers(dest="amqp_command", help="AMQP commands")
        message_amqp_metadata_subparsers = message_amqp_subparsers.add_parser(
            "metadata", help="Manage AMQP message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_amqp_message(args):
            sc = CatalogSubcommands(args.catalog)
            sc.add_message(
                messagegroupid=args.messagegroupid,
                messageid=args.messageid,
                envelope="None",
                protocol="AMQP/1.0",
                dataschemaformat=args.dataschemaformat,
                dataschemagroup=args.dataschemagroup,
                dataschemaid=args.dataschemaid,
                dataschemauri=args.dataschemauri,
                documentation=args.documentation,
                description=args.description,
                labels=args.labels,
                name=args.name
            )
            sc.add_amqp_message_metadata(
                messagegroupid=args.messagegroupid,
                messageid=args.messageid,
                section="properties",
                name="subject",
                type="string",
                value=None,
                description="Subject",
                required=True
            )

        message_amqp_add = message_amqp_subparsers.add_parser("add", help="Add a new AMQP message")
        message_amqp_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_amqp_add.add_argument("--messageid", required=True, help="Message ID")
        message_amqp_add.add_argument("--description", help="Message description")
        message_amqp_add.add_argument("--documentation", help="Message documentation URL")
        message_amqp_add.add_argument("--name", help="Message name")
        message_amqp_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_amqp_add.add_argument("--dataschemaformat", help="Schema format")
        message_amqp_add.add_argument("--dataschemagroup", help="Schema group ID")
        message_amqp_add.add_argument("--dataschemaid", help="Schema ID")
        message_amqp_add.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_amqp_add)
        message_amqp_add.set_defaults(func=_add_amqp_message)

        message_amqp_edit = message_amqp_subparsers.add_parser("edit", help="Edit a Kafka message")
        message_amqp_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_amqp_edit.add_argument("--messageid", required=True, help="Message ID")
        message_amqp_edit.add_argument("--description", help="Message description")
        message_amqp_edit.add_argument("--documentation", help="Message documentation URL")
        message_amqp_edit.add_argument("--name", help="Message name")
        message_amqp_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_amqp_edit.add_argument("--dataschemaformat", help="Schema format")
        message_amqp_edit.add_argument("--dataschemagroup", help="Schema group ID")
        message_amqp_edit.add_argument("--dataschemaid", help="Schema ID")
        message_amqp_edit.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_amqp_edit)
        message_amqp_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            messagegroupid=args.messagegroupid,
            messageid=args.messageid,
            envelope="None",
            protocol="AMQP/1.0",
            dataschemaformat=args.dataschemaformat,
            dataschemagroup=args.dataschemagroup,
            dataschemaid=args.dataschemaid,
            dataschemauri=args.dataschemauri,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))

        message_amqp_remove = message_amqp_subparsers.add_parser("remove", help="Remove an AMQP message")
        message_amqp_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_amqp_remove.add_argument("--messageid", required=True, help="Message ID")
        add_authentication_arguments(message_amqp_remove)
        message_amqp_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_message(args.messagegroupid, args.messageid))

        message_amqp_metadata_add = message_amqp_metadata_subparsers.add_parser("add", help="Add a new AMQP metadata field")
        message_amqp_metadata_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_amqp_metadata_add.add_argument("--messageid", required=True, help="Message ID")
        message_amqp_metadata_add.add_argument("--section", required=True, choices=[
                                               "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_amqp_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_amqp_metadata_add.add_argument("--value", required=False, help="Metadata value")
        message_amqp_metadata_add.add_argument("--description", help="Metadata description")
        message_amqp_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_amqp_metadata_add)
        message_amqp_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_amqp_message_metadata(
            messagegroupid=args.messagegroupid, messageid=args.messageid, section=args.section, name=args.name, type=args.type, value=args.value, description=args.description, required=args.required))

        message_amqp_metadata_edit = message_amqp_metadata_subparsers.add_parser("edit", help="Edit an AMQP metadata field")
        message_amqp_metadata_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_amqp_metadata_edit.add_argument("--messageid", required=True, help="Message ID")
        message_amqp_metadata_edit.add_argument("--section", required=True, choices=[
                                                "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_edit.add_argument("--name", help="Metadata name")
        message_amqp_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_amqp_metadata_edit.add_argument("--value", required=False, help="Metadata value")
        message_amqp_metadata_edit.add_argument("--description", help="Metadata description")
        message_amqp_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_amqp_metadata_edit)
        message_amqp_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_amqp_message_metadata(
            args.messagegroupid, args.messageid, args.section, args.name, args.type, args.value, args.description, args.required))

        message_amqp_metadata_remove = message_amqp_metadata_subparsers.add_parser(
            "remove", help="Remove an AMQP metadata field")
        message_amqp_metadata_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_amqp_metadata_remove.add_argument("--messageid", required=True, help="Message ID")
        message_amqp_metadata_remove.add_argument("--section", required=True, choices=[
                                                  "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        add_authentication_arguments(message_amqp_metadata_remove)
        message_amqp_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_amqp_message_metadata(args.messagegroupid, args.messageid, args.name, args.section))

        message_mqtt_subparsers = manifest_subparsers.add_parser("mqtt", help="Manage MQTT messages").add_subparsers(dest="mqtt_command", help="MQTT commands")
        message_mqtt_metadata_subparsers = message_mqtt_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_mqtt_message(args):
            sc = CatalogSubcommands(args.catalog)
            sc.add_message(
                args.messagegroupid, args.messageid, "None", "MQTT/" + args.mqtt_version, args.dataschemaformat, args.dataschemagroup, args.dataschemaid,
                args.dataschemauri, args.documentation, args.description, args.labels, args.name)
            sc.add_mqtt_message_metadata(args.messagegroupid, args.messageid, args.mqtt_version, "topic",
                                         "string", "{topic}/"+args.messageid,  "MQTT topic", True)

        message_mqtt_add = message_mqtt_subparsers.add_parser("add", help="Add a new MQTT message")
        message_mqtt_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_mqtt_add.add_argument("--messageid", required=True, help="Message ID")
        message_mqtt_add.add_argument("--description", help="Message description")
        message_mqtt_add.add_argument("--documentation", help="Message documentation URL")
        message_mqtt_add.add_argument("--name", help="Message name")
        message_mqtt_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_mqtt_add.add_argument("--mqtt-version", required=True,
                                      choices=["3", "5", "3.1.1", "5.0"], help="MQTT version", default="5.0")
        message_mqtt_add.add_argument("--dataschemaformat", help="Schema format")
        message_mqtt_add.add_argument("--dataschemagroup", help="Schema group ID")
        message_mqtt_add.add_argument("--dataschemaid", help="Schema ID")
        message_mqtt_add.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_mqtt_add)
        message_mqtt_add.set_defaults(func=_add_mqtt_message)

        message_mqtt_edit = message_mqtt_subparsers.add_parser("edit", help="Edit a MQTT message")
        message_mqtt_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_mqtt_edit.add_argument("--messageid", required=True, help="Message ID")
        message_mqtt_edit.add_argument("--description", help="Message description")
        message_mqtt_edit.add_argument("--documentation", help="Message documentation URL")
        message_mqtt_edit.add_argument("--name", help="Message name")
        message_mqtt_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_mqtt_edit.add_argument("--mqtt-version", required=True, 
                                        choices=["3", "5", "3.1.1", "5.0"], help="MQTT version", default="5.0")
        message_mqtt_edit.add_argument("--dataschemaformat", help="Schema format")
        message_mqtt_edit.add_argument("--dataschemagroup", help="Schema group ID")
        message_mqtt_edit.add_argument("--dataschemaid", help="Schema ID")
        message_mqtt_edit.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_mqtt_edit)
        message_mqtt_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            messagegroupid=args.messagegroupid,
            messageid=args.messageid,
            envelope="None",
            protocol="MQTT/" + args.mqtt_version,
            dataschemaformat=args.dataschemaformat,
            dataschemagroup=args.dataschemagroup,
            dataschemaid=args.dataschemaid,
            dataschemauri=args.dataschemauri,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))

        message_mqtt_remove = message_mqtt_subparsers.add_parser("remove", help="Remove a message")
        message_mqtt_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_mqtt_remove.add_argument("--messageid", required=True, help="Message ID")
        add_authentication_arguments(message_mqtt_remove)
        message_mqtt_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_message(args.messagegroupid, args.messageid))

        message_mqtt_metadata_add = message_mqtt_metadata_subparsers.add_parser("add", help="Add a new metadata field")
        message_mqtt_metadata_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_mqtt_metadata_add.add_argument("--messageid", required=True, help="Message ID")
        message_mqtt_metadata_add.add_argument("--mqtt-version", required=True,
                                               choices=["3", "5", "3.1.1", "5.0"], help="MQTT version", default="5.0")
        message_mqtt_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_mqtt_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_mqtt_metadata_add.add_argument("--value", required=True, help="Metadata value")
        message_mqtt_metadata_add.add_argument("--description", help="Metadata description")
        message_mqtt_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_mqtt_metadata_add)
        message_mqtt_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_mqtt_message_metadata(
            messagegroupid=args.messagegroupid, 
            messageid=args.messageid, 
            mqtt_version=args.mqtt_version, 
            name=args.name, 
            type=args.type, 
            value=args.value, 
            description=args.description, 
            required=args.required
        ))

        message_mqtt_metadata_edit = message_mqtt_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_mqtt_metadata_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_mqtt_metadata_edit.add_argument("--messageid", required=True, help="Message ID")
        message_mqtt_metadata_edit.add_argument("--mqtt_version", required=True,
                                                choices=["3", "5", "3.1.1", "5.0"], help="MQTT version")
        message_mqtt_metadata_edit.add_argument("--name", help="Metadata name")
        message_mqtt_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_mqtt_metadata_edit.add_argument("--value", help="Metadata value")
        message_mqtt_metadata_edit.add_argument("--description", help="Metadata description")
        message_mqtt_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_mqtt_metadata_edit)
        message_mqtt_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_mqtt_message_metadata(
            messagegroupid=args.messagegroupid, 
            messageid=args.messageid, 
            name=args.name, 
            type=args.type, 
            value=args.value, 
            description=args.description, 
            required=args.required
        ))

        message_mqtt_metadata_remove = message_mqtt_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_mqtt_metadata_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_mqtt_metadata_remove.add_argument("--messageid", required=True, help="Message ID")
        message_mqtt_metadata_remove.add_argument("--section", required=False, choices=["properties", "topic"], help="Metadata section")
        message_mqtt_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        add_authentication_arguments(message_mqtt_metadata_remove)
        message_mqtt_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_mqtt_message_metadata(
            messagegroupid=args.messagegroupid, 
            messageid=args.messageid, 
            section=args.section, 
            name=args.name
        ))

        message_kafka_subparsers = manifest_subparsers.add_parser(
            "kafka", help="Manage Kafka messages").add_subparsers(dest="kafka_command", help="Kafka commands")
        message_kafka_metadata_subparsers = message_kafka_subparsers.add_parser(
            "metadata", help="Manage Kafka message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_kafka_message(args):
            sc = CatalogSubcommands(args.catalog)
            sc.add_message(
                messagegroupid=args.messagegroupid,
                messageid=args.messageid,
                envelope="None",
                protocol="KAFKA",
                dataschemaformat=args.dataschemaformat,
                dataschemagroup=args.dataschemagroup,
                dataschemaid=args.dataschemaid,
                dataschemauri=args.dataschemauri,
                documentation=args.documentation,
                description=args.description,
                labels=args.labels,
                name=args.name
            )
            sc.add_kafka_message_metadata(
                messagegroupid=args.messagegroupid,
                messageid=args.messageid,
                section="headers",
                name="message_type",
                type="string",
                value=args.messageid,
                description="Message ID",
                required=True
            )
            sc.add_kafka_message_metadata(
                messagegroupid=args.messagegroupid,
                messageid=args.messageid,
                section=None,
                name="key",
                type="string",
                value="{key}",
                description="Message key",
                required=False
            )

        message_kafka_add = message_kafka_subparsers.add_parser("add", help="Add a new Kafka message")
        message_kafka_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_kafka_add.add_argument("--messageid", required=True, help="Message ID")
        message_kafka_add.add_argument("--description", help="Message description")
        message_kafka_add.add_argument("--documentation", help="Message documentation URL")
        message_kafka_add.add_argument("--name", help="Message name")
        message_kafka_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_kafka_add.add_argument("--dataschemaformat", help="Schema format")
        message_kafka_add.add_argument("--dataschemagroup", help="Schema group ID")
        message_kafka_add.add_argument("--dataschemaid", help="Schema ID")
        message_kafka_add.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_kafka_add)
        message_kafka_add.set_defaults(func=_add_kafka_message)

        message_kafka_edit = message_kafka_subparsers.add_parser("edit", help="Edit a message")
        message_kafka_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_kafka_edit.add_argument("--messageid", required=True, help="Message ID")
        message_kafka_edit.add_argument("--description", help="Message description")
        message_kafka_edit.add_argument("--documentation", help="Message documentation URL")
        message_kafka_edit.add_argument("--name", help="Message name")
        message_kafka_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_kafka_edit.add_argument("--dataschemaformat", help="Schema format")
        message_kafka_edit.add_argument("--dataschemagroup", help="Schema group ID")
        message_kafka_edit.add_argument("--dataschemaid", help="Schema ID")
        message_kafka_edit.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_kafka_edit)
        message_kafka_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            messagegroupid=args.messagegroupid,
            messageid=args.messageid,
            envelope="None",
            protocol="KAFKA",
            dataschemaformat=args.dataschemaformat,
            dataschemagroup=args.dataschemagroup,
            dataschemaid=args.dataschemaid,
            dataschemauri=args.dataschemauri,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))

        message_kafka_remove = message_kafka_subparsers.add_parser("remove", help="Remove a message")
        message_kafka_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_kafka_remove.add_argument("--messageid", required=True, help="Message ID")
        add_authentication_arguments(message_kafka_remove)
        message_kafka_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_message(args.messagegroupid, args.messageid))

        message_kafka_metadata_add = message_kafka_metadata_subparsers.add_parser(
            "add", help="Add a new metadata field")
        message_kafka_metadata_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_kafka_metadata_add.add_argument("--messageid", required=True, help="Message ID")
        message_kafka_metadata_add.add_argument("--section", required=True, choices=["headers"], help="Metadata section")
        message_kafka_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_kafka_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_kafka_metadata_add.add_argument("--value", required=True, help="Metadata value")
        message_kafka_metadata_add.add_argument("--description", help="Metadata description")
        message_kafka_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_kafka_metadata_add)
        message_kafka_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_kafka_message_metadata(
            messagegroupid=args.messagegroupid, 
            messageid=args.messageid, 
            section=args.section, 
            name=args.name, 
            type=args.type, 
            value=args.value, 
            description=args.description, 
            required=args.required
        ))

        message_kafka_metadata_edit = message_kafka_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_kafka_metadata_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_kafka_metadata_edit.add_argument("--messageid", required=True, help="Message ID")
        message_kafka_metadata_edit.add_argument("--section", required=True, choices=["headers"], help="Metadata section")
        message_kafka_metadata_edit.add_argument("--name", help="Metadata name")
        message_kafka_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_kafka_metadata_edit.add_argument("--value", help="Metadata value")
        message_kafka_metadata_edit.add_argument("--description", help="Metadata description")
        message_kafka_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_kafka_metadata_edit)
        message_kafka_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_kafka_message_metadata(
            groupid=args.messagegroupid, 
            messageid=args.messageid, 
            section=args.section, 
            name=args.name, 
            type=args.type, 
            value=args.value, 
            description=args.description, 
            required=args.required
        ))

        message_kafka_metadata_remove = message_kafka_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_kafka_metadata_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_kafka_metadata_remove.add_argument("--messageid", required=True, help="Message ID")
        message_kafka_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        message_kafka_metadata_remove.add_argument(
            "--section", required=True, choices=["headers"], help="Metadata section")
        add_authentication_arguments(message_kafka_metadata_remove)
        message_kafka_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_kafka_message_metadata(
            messagegroupid=args.messagegroupid, 
            messageid=args.messageid, 
            section=args.section, 
            name=args.name
        ))

        message_http_subparsers = manifest_subparsers.add_parser(
            "http", help="Manage HTTP").add_subparsers(dest="http_command", help="HTTP commands")
        message_http_metadata_subparsers = message_http_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_http_message(args):
            sc = CatalogSubcommands(args.catalog)
            sc.add_message(
                messagegroupid=args.messagegroupid,
                messageid=args.messageid,
                envelope="None",
                protocol="HTTP",
                dataschemaformat=args.dataschemaformat,
                dataschemagroup=args.dataschemagroup,
                dataschemaid=args.dataschemaid,
                dataschemauri=args.dataschemauri,
                documentation=args.documentation,
                description=args.description,
                labels=args.labels,
                name=args.name
            )
            sc.add_http_message_metadata(
                groupid=args.messagegroupid,
                messageid=args.messageid,
                section="headers",
                name="content-type",
                type="string",
                value="application/json",
                description="Content type",
                required=True
            )
            sc.add_http_message_metadata(
                groupid=args.messagegroupid,
                messageid=args.messageid,
                section=None,
                name="method",
                type="string",
                value="POST",
                description="HTTP method",
                required=True
            )

        message_http_add = message_http_subparsers.add_parser("add", help="Add a new message")
        message_http_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_http_add.add_argument("--messageid", required=True, help="Message ID")
        message_http_add.add_argument("--description", help="Message description")
        message_http_add.add_argument("--documentation", help="Message documentation URL")
        message_http_add.add_argument("--name", help="Message name")
        message_http_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_http_add.add_argument("--dataschemaformat", help="Schema format")
        message_http_add.add_argument("--dataschemagroup", help="Schema group ID")
        message_http_add.add_argument("--dataschemaid", help="Schema ID")
        message_http_add.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_http_add)
        message_http_add.set_defaults(func=_add_http_message)

        message_http_edit = message_http_subparsers.add_parser("edit", help="Edit a message")
        message_http_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_http_edit.add_argument("--messageid", required=True, help="Message ID")
        message_http_edit.add_argument("--description", help="Message description")
        message_http_edit.add_argument("--documentation", help="Message documentation URL")
        message_http_edit.add_argument("--name", help="Message name")
        message_http_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Message labels (key=value pairs)")
        message_http_edit.add_argument("--dataschemaformat", help="Schema format")
        message_http_edit.add_argument("--dataschemagroup", help="Schema group ID")
        message_http_edit.add_argument("--dataschemaid", help="Schema ID")
        message_http_edit.add_argument("--dataschemauri", help="Schema URL")
        add_authentication_arguments(message_http_edit)
        message_http_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            messagegroupid=args.messagegroupid,
            messageid=args.messageid,
            envelope="None",
            protocol="HTTP",
            dataschemaformat=args.dataschemaformat,
            dataschemagroup=args.dataschemagroup,
            dataschemaid=args.dataschemaid,
            dataschemauri=args.dataschemauri,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))

        message_http_remove = message_http_subparsers.add_parser("remove", help="Remove a message")
        message_http_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_http_remove.add_argument("--messageid", required=True, help="Message ID")
        add_authentication_arguments(message_http_remove)
        message_http_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_message(args.messagegroupid, args.messageid))

        message_http_metadata_add = message_http_metadata_subparsers.add_parser("add", help="Add a new metadata field")
        message_http_metadata_add.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_http_metadata_add.add_argument("--messageid", required=True, help="Message ID")
        message_http_metadata_add.add_argument("--key", required=True, help="Metadata key")
        message_http_metadata_add.add_argument("--section", required=False,
                                               choices=["headers", "query"], help="Metadata section")
        message_http_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_http_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_http_metadata_add.add_argument("--value", required=True, help="Metadata value")
        message_http_metadata_add.add_argument("--description", help="Metadata description")
        message_http_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_http_metadata_add)
        message_http_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_http_message_metadata(
            groupid=args.messagegroupid, 
            messageid=args.messageid, 
            section=args.section, 
            name=args.name, 
            type=args.type, 
            value=args.value, 
            description=args.description, 
            required=args.required
        ))

        message_http_metadata_edit = message_http_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_http_metadata_edit.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_http_metadata_edit.add_argument("--messageid", required=True, help="Message ID")
        message_http_metadata_edit.add_argument("--key", required=True, help="Metadata key")
        message_http_metadata_edit.add_argument("--section", required=False,
                                                choices=["headers", "query"], help="Metadata section")
        message_http_metadata_edit.add_argument("--name", help="Metadata name")
        message_http_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_http_metadata_edit.add_argument("--value", help="Metadata value")
        message_http_metadata_edit.add_argument("--description", help="Metadata description")
        message_http_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        add_authentication_arguments(message_http_metadata_edit)
        message_http_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_http_message_metadata(
            messagegroupid=args.messagegroupid, 
            messageid=args.messageid, 
            section=args.section, 
            name=args.name, 
            type=args.type, 
            value=args.value, 
            description=args.description, 
            required=args.required
        ))

        message_http_metadata_remove = message_http_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_http_metadata_remove.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_http_metadata_remove.add_argument("--messageid", required=True, help="Message ID")
        message_http_metadata_remove.add_argument("--name", required=True, help="Metadata key")
        message_http_metadata_remove.add_argument(
            "--section", required=False, choices=["headers", "query"], help="Metadata section")
        add_authentication_arguments(message_http_metadata_remove)
        message_http_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_http_message_metadata(
            messagegroupid=args.messagegroupid, 
            messageid=args.messageid, 
            section=args.section, 
            name=args.name
        ))

        message_show = message_subparsers.add_parser("show", help="Show a message")
        message_show.add_argument("--messagegroupid", required=True, help="Message group ID")
        message_show.add_argument("--messageid", required=True, help="Message ID")
        
        add_authentication_arguments(message_show)
        message_show.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).show_message(args.messagegroupid, args.messageid))

        schemagroup_subparsers = manifest_subparsers.add_parser("schemagroup", help="Manage schema groups").add_subparsers(
            dest="schemagroup_command", help="Schema group commands")

        schemagroup_add = schemagroup_subparsers.add_parser("add", help="Add a new schema group")
        schemagroup_add.add_argument("--schemagroupid", required=True, help="Schema group ID")
        schemagroup_add.add_argument("--description", help="Schema group description")
        schemagroup_add.add_argument("--documentation", help="Schema group documentation URL")
        schemagroup_add.add_argument("--format", required=True, help="Schema group format")
        schemagroup_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Schema group labels (key=value pairs)")
        schemagroup_add.add_argument("--name", help="Schema group name")
        add_authentication_arguments(schemagroup_add)
        schemagroup_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_schemagroup(
            schemagroupid=args.schemagroupid, 
            description=args.description,
            documentation=args.documentation,
            format=args.format,
            labels=args.labels,
            name=args.name))

        schemagroup_remove = schemagroup_subparsers.add_parser("remove", help="Remove a schema group")
        schemagroup_remove.add_argument("--schemagroupid", required=True, help="Schema group ID")
        add_authentication_arguments(schemagroup_remove)
        schemagroup_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_schemagroup(args.schemagroupid))

        schemagroup_edit = schemagroup_subparsers.add_parser("edit", help="Edit a schema group")
        schemagroup_edit.add_argument("--schemagroupid", required=True, help="Schema group ID")
        schemagroup_edit.add_argument("--description", help="Schema group description")
        schemagroup_edit.add_argument("--format", help="Schema group format ('None' to clear format)")
        schemagroup_edit.add_argument("--documentation", help="Schema group documentation URL")
        schemagroup_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Schema group labels (key=value pairs)")
        schemagroup_edit.add_argument("--name", help="Schema group name")
        add_authentication_arguments(schemagroup_edit)
        schemagroup_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_schemagroup(
            schemagroupid=args.schemagroupid,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))

        schemagroup_show = schemagroup_subparsers.add_parser("show", help="Show a schema group")
        schemagroup_show.add_argument("--schemagroupid", required=True, help="Schema group ID")
        add_authentication_arguments(schemagroup_show)
        schemagroup_show.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).show_schemagroup(args.schemagroupid))

        schemagroup_apply = schemagroup_subparsers.add_parser("apply", help="Apply a schema group JSON")
        schemagroup_apply.add_argument("-f", "--file", required=True, help="JSON file containing schema group data")
        add_authentication_arguments(schemagroup_apply)
        schemagroup_apply.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).apply_schemagroup(args.file))

        schema_subparsers = manifest_subparsers.add_parser(
            "schemaversion", help="Manage schema versions").add_subparsers(dest="schema_command", help="Schema commands")

        schema_add = schema_subparsers.add_parser("add", help="Add a new schema version")
        schema_add.add_argument("--schemagroupid", required=True, help="Schema group ID")
        schema_add.add_argument("--schemaid", required=True, help="Schema ID")
        schema_add.add_argument("--description", help="Schema description")
        schema_add.add_argument("--documentation", help="Schema documentation URL")
        schema_add.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Schema labels (key=value pairs)")
        schema_add.add_argument("--name", help="Schema name")
        schema_add.add_argument("--format", required=True, help="Schema format")
        schema_add.add_argument("--versionid", help="Schema version ID")
        schema_add.add_argument("--schema", help="Inline schema")
        schema_add.add_argument("--schemaimport", help="Schema import file location or URL")
        schema_add.add_argument("--schemaurl", help="Schema URL")
        add_authentication_arguments(schema_add)
        schema_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_schemaversion(
            schemagroupid=args.schemagroupid,
            schemaid=args.schemaid,
            format=args.format,
            versionid=args.versionid,
            schema=args.schema,
            schemaimport=args.schemaimport,
            schemaurl=args.schemaurl,
            description=args.description,
            documentation=args.documentation,
            labels=args.labels,
            name=args.name
        ))

        schema_remove = schema_subparsers.add_parser("remove", help="Remove a schema or schema version")
        schema_remove.add_argument("--schemagroupid", required=True, help="Schema group ID")
        schema_remove.add_argument("--schemaid", required=True, help="Schema ID")
        schema_remove.add_argument("--versionid", required=True, help="Schema version ID")
        add_authentication_arguments(schema_remove)
        schema_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_schema(
            schemagroupid=args.schemagroupid,
            schemaid=args.schemaid,
            versionid=args.versionid
        ))

        schema_edit = schema_subparsers.add_parser("edit", help="Edit a schema or schema version")
        schema_edit.add_argument("--schemagroupid", required=True, help="Schema group ID")
        schema_edit.add_argument("--schemaid", required=True, help="Schema ID")
        schema_edit.add_argument("--description", help="Schema description")
        schema_edit.add_argument("--documentation", help="Schema documentation URL")
        schema_edit.add_argument("--name", help="Schema name")
        schema_edit.add_argument("--labels", nargs='*', metavar='KEY=VALUE', help="Schema labels (key=value pairs)")
        schema_edit.add_argument("--format", help="Schema format")
        schema_edit.add_argument("--versionid", required=True, help="Schema version ID")
        schema_edit.add_argument("--schema", help="Inline schema")
        schema_edit.add_argument("--schemaimport", help="Schema import file location or URL")
        schema_edit.add_argument("--schemaurl", help="Schema URL")
        add_authentication_arguments(schema_edit)
        schema_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_schemaversion(
            schemagroupid=args.schemagroupid,
            schemaid=args.schemaid,
            versionid=args.versionid,
            format=args.format,
            schema=args.schema,
            schemaimport=args.schemaimport,
            schemaurl=args.schemaurl,
            documentation=args.documentation,
            description=args.description,
            labels=args.labels,
            name=args.name
        ))

        schema_show = schema_subparsers.add_parser("show", help="Show a schema")
        schema_show.add_argument("--schemagroupid", required=True, help="Schema group ID")
        schema_show.add_argument("--schemaid", required=True, help="Schema ID")
        add_authentication_arguments(schema_show)
        schema_show.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).show_schema(
            schemagroupid=args.schemagroupid, 
            schemaid=args.schemaid
        ))

        schema_apply = schema_subparsers.add_parser("apply", help="Apply a schema JSON")
        schema_apply.add_argument("-f", "--file", required=True, help="JSON file containing schema data")
        add_authentication_arguments(schema_apply)
        schema_apply.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).apply_schema(args.file))