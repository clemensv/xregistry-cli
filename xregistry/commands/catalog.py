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
    return datetime.datetime.now().isoformat()

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
        if response.status_code != 200:
            raise ValueError(f"Failed to add endpoint: {response.text}")

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
        endpoint["epoch"] += 1
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

    def add_messagegroup(self, messagegroupid: str, format: str, binding: str, messages: Optional[Dict[str, Any]] = None,
                         description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                         name: Optional[str] = None) -> None:
        """Adds a messagegroup to the catalog."""
        
        messagegroup = {
            "messagegroupid": messagegroupid,
            "format": format,
            "binding": binding,
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
        if response.status_code != 200:
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

    def edit_messagegroup(self, messagegroupid: str, format: Optional[str] = None, binding: Optional[str] = None, messages: Optional[Dict[str, Any]] = None,
                          description: Optional[str] = None, documentation: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                          name: Optional[str] = None) -> None:
        """Edits an existing messagegroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/messagegroups/{messagegroupid}")
        if response.status_code != 200:
            raise ValueError(f"Messagegroup with id {messagegroupid} does not exist: {response.text}")
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
        messagegroup["modifiedat"] = current_time_iso()
        messagegroup["epoch"] += 1
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
        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200:
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
        schemagroup["epoch"] += 1
        response = requests.put(f"{self.base_url}/schemagroups/{schemagroupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit schemagroup: {response.text}")

    def show_schemagroup(self, schemagroupid: str) -> None:
        """Shows a schemagroup from the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{schemagroupid}")
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

    def add_message(self, groupid: str, messageid: str, format: str, protocol: str, schemaformat: Optional[str] = None,
                    schemagroup: Optional[str] = None, schemaid: Optional[str] = None, schemaurl: Optional[str] = None,
                    documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                    name: Optional[str] = None) -> None:
        """Adds a message to a message group in the catalog."""
        
        message = {
            "messageid": messageid,
            "format": format,
            "protocol": protocol,
            "createdat": current_time_iso(),
            "modifiedat": current_time_iso(),
            "epoch": 0
        }
        if schemaformat:
            message["schemaformat"] = schemaformat
        if schemagroup:
            message["schemagroup"] = schemagroup
        if schemaid:
            message["schemaid"] = schemaid
        if schemaurl:
            message["schemaurl"] = schemaurl
        if documentation:
            message["documentation"] = documentation
        if description:
            message["description"] = description
        if labels:
            message["labels"] = labels
        if name:
            message["name"] = name

        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
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

    def edit_message(self, groupid: str, messageid: str, format: Optional[str] = None, protocol: Optional[str] = None, schemaformat: Optional[str] = None,
                     schemagroup: Optional[str] = None, schemaid: Optional[str] = None, schemaurl: Optional[str] = None,
                     documentation: Optional[str] = None, description: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                     name: Optional[str] = None) -> None:
        """Edits an existing message in a message group in the catalog."""
        
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Message with id {messageid} does not exist: {response.text}")
        message = response.json()
        if format:
            message["format"] = format
        if protocol:
            message["protocol"] = protocol
        if schemaformat:
            message["schemaformat"] = schemaformat
        if schemagroup:
            message["schemagroup"] = schemagroup
        if schemaid:
            message["schemaid"] = schemaid
        if schemaurl:
            message["schemaurl"] = schemaurl
        if documentation:
            message["documentation"] = documentation
        if description:
            message["description"] = description
        if labels:
            message["labels"] = labels
        if name:
            message["name"] = name
        message["modifiedat"] = current_time_iso()
        message["epoch"] += 1
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
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
        

    def remove_amqp_message_metadata(self, groupid: str, messageid: str, section: str|None, name: str) -> None:
        """Removes AMQP message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "AMQP/1.0":
            raise ValueError(f"Message {messageid} is not an AMQP message")
        
        self.remove_protocol_option(messageid, message, section, name)
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove AMQP message metadata: {response.text}")

    def add_amqp_message_metadata(self, groupid: str, messageid: str, section: str|None, name: str, type: str, value: str|None, description: str, required: bool) -> None:
        """Adds AMQP message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
     
        if "protocol" not in message or message["protocol"] != "AMQP/1.0":
            raise ValueError(f"Message {messageid} is not an AMQP message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)

        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add AMQP message metadata: {response.text}")

    def edit_amqp_message_metadata(self, groupid: str, messageid: str, section: str|None, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Edits AMQP message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "AMQP/1.0":
            raise ValueError(f"Message {messageid} is not an AMQP message")
        
        # Update the metadata entry
        self.set_protocol_option(message, section, name, type, value, description, required)
        
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit AMQP message metadata: {response.text}")

    def add_mqtt_message_metadata(self, groupid: str, messageid: str, mqtt_version: str, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Adds MQTT message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "MQTT/5.0" and message["protocol"] != "MQTT/3.1.1":
            raise ValueError(f"Message {messageid} is not an MQTT message")
        
        self.set_protocol_option(message, None, name, type, value, description, required)
        
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add MQTT message metadata: {response.text}")

    def remove_mqtt_message_metadata(self, groupid: str, messageid: str, section:str|None, name: str) -> None:
        """Removes MQTT message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "MQTT/5.0" and message["protocol"] != "MQTT/3.1.1":
            raise ValueError(f"Message {messageid} is not an MQTT message")
        
        self.remove_protocol_option(messageid, message, section, name)
        
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove MQTT message metadata: {response.text}")

    def edit_mqtt_message_metadata(self, groupid: str, messageid: str, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Edits MQTT message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "MQTT/5.0" and message["protocol"] != "MQTT/3.1.1":
            raise ValueError(f"Message {messageid} is not an MQTT message")
        
        self.set_protocol_option(message, None, name, type, value, description, required)
        
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit MQTT message metadata: {response.text}")

    def add_kafka_message_metadata(self, groupid: str, messageid: str, section: Optional[str], name: str, type: str, value: str, description: str, required: bool) -> None:
        """Adds Kafka message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "Kafka":
            raise ValueError(f"Message {messageid} is not a Kafka message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)

        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add Kafka message metadata: {response.text}")

    def remove_kafka_message_metadata(self, groupid: str, messageid: str, section: Optional[str], name: str) -> None:
        """Removes Kafka message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "Kafka":
            raise ValueError(f"Message {messageid} is not a Kafka message")
        
        self.remove_protocol_option(messageid, message, section, name)
                
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove Kafka message metadata: {response.text}")

    def edit_kafka_message_metadata(self, groupid: str, messageid: str, section: Optional[str], name: str, type: str, value: str, description: str, required: bool) -> None:
        """Edits Kafka message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        if "protocol" not in message or message["protocol"] != "Kafka":
            raise ValueError(f"Message {messageid} is not a Kafka message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)

        # Increment the epoch
        message["epoch"] += 1
        
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
        
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add HTTP message metadata: {response.text}")

    def remove_http_message_metadata(self, groupid: str, messageid: str, section: str | None, name: str) -> None:
        """Removes HTTP message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "HTTP/1.1":
            raise ValueError(f"Message {messageid} is not an HTTP message")

        self.remove_protocol_option(messageid, message, section, name) 
       
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove HTTP message metadata: {response.text}")

    def edit_http_message_metadata(self, groupid: str, messageid: str, section: str | None, name: str, type: str, value: str, description: str, required: bool) -> None:
        """Edits HTTP message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "protocol" not in message or message["protocol"] != "HTTP/1.1":
            raise ValueError(f"Message {messageid} is not an HTTP message")
        
        self.set_protocol_option(message, section, name, type, value, description, required)        
       
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
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
        

    def add_cloudevents_message_metadata(self, groupid: str, messageid: str, attribute: str, type: str, description: str, value: str, required: bool) -> None:
        """Adds CloudEvents message metadata to a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "envelope" not in message or message["envelope"] != "CloudEvents/1.0":
            raise ValueError(f"Message {messageid} is not a CloudEvents message")
        
        self.set_envelope_metadata(message, attribute, type, value, description, required)
        
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to add CloudEvents message metadata: {response.text}")

    def edit_cloudevents_message_metadata(self, groupid: str, messageid: str, attribute: str, type: str, description: str, value: str, required: bool) -> None:
        """Edits CloudEvents message metadata for a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()

        if "envelope" not in message or message["envelope"] != "CloudEvents/1.0":
            raise ValueError(f"Message {messageid} is not a CloudEvents message")
        
        self.remove_envelope_metadata(messageid, message, attribute)

        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit CloudEvents message metadata: {response.text}")

    def remove_cloudevents_message_metadata(self, groupid: str, messageid: str, attribute: str) -> None:
        """Removes CloudEvents message metadata from a message in a message group in the catalog."""
        
        # Fetch the current message
        response = requests.get(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}")
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch message: {response.text}")
        message = response.json()
        
        # Remove the metadata entry
        if "metadata" in message:
            message["metadata"] = [m for m in message["metadata"] if m["attribute"] != attribute]
        
        # Increment the epoch
        message["epoch"] += 1
        
        # Update the message with a PUT request
        response = requests.put(f"{self.base_url}/messagegroups/{groupid}/messages/{messageid}", json=message)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove CloudEvents message metadata: {response.text}")

    def add_schema(self, groupid: str, schemaid: str, format: str, versionid: str = "1", schema: Optional[str] = None,
                   schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                   labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Adds a schema to a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
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

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to add schema: {response.text}")

    def add_schemaversion(self, groupid: str, schemaid: str, format: str, versionid: str = "1", schema: Optional[str] = None,
                          schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                          labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Adds a schema version to a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        schema_obj = {
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
        if schemaid not in schemagroup["schemas"]:
            schemagroup["schemas"][schemaid] = {"versions": {}}
        schemagroup["schemas"][schemaid]["versions"][versionid] = schema_obj

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to add schema version: {response.text}")
        
    def edit_schemaversion(self, groupid: str, schemaid: str, versionid: str, format: Optional[str] = None, schema: Optional[str] = None,
                            schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                            labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Edits an existing schema version in a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {groupid}")
        
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
        schema_obj["epoch"] += 1

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit schema version: {response.text}")
        
    def remove_schemaversion(self, groupid: str, schemaid: str, versionid: str) -> None:
        """Removes a schema version from a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {groupid}")
        
        if "versions" not in schemagroup["schemas"][schemaid] or versionid not in schemagroup["schemas"][schemaid]["versions"]:
            raise ValueError(f"Version with id {versionid} does not exist for schema {schemaid}")
        
        del schemagroup["schemas"][schemaid]["versions"][versionid]
        if not schemagroup["schemas"][schemaid]["versions"]:
            del schemagroup["schemas"][schemaid]

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove schema version: {response.text}")


    def remove_schema(self, groupid: str, schemaid: str, versionid: Optional[str] = None) -> None:
        """Removes a schema from a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {groupid}")

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

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to remove schema: {response.text}")

    def edit_schema(self, groupid: str, schemaid: str, format: Optional[str] = None, versionid: str = "1", schema: Optional[str] = None,
                    schemaimport: Optional[str] = None, schemaurl: Optional[str] = None, description: Optional[str] = None, documentation: Optional[str] = None,
                    labels: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> None:
        """Edits an existing schema in a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {groupid}")

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
        schema_obj["epoch"] += 1

        response = requests.put(f"{self.base_url}/schemagroups/{groupid}", json=schemagroup)
        if response.status_code != 200:
            raise ValueError(f"Failed to edit schema: {response.text}")

    def show_schema(self, groupid: str, schemaid: str) -> None:
        """Shows a schema from a schemagroup in the catalog."""
        
        response = requests.get(f"{self.base_url}/schemagroups/{groupid}")
        if response.status_code != 200:
            raise ValueError(f"Schemagroup with id {groupid} does not exist: {response.text}")
        schemagroup = response.json()

        if "schemas" not in schemagroup or schemaid not in schemagroup["schemas"]:
            raise ValueError(f"Schema with id {schemaid} does not exist in schemagroup {groupid}")

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
        endpoint_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_endpoint(args.id, args.usage, args.protocol, args.deployed, args.endpoints, args.options,
                                                                                                    args.messagegroups, args.documentation, args.description, args.labels, args.name,
                                                                                                    args.channel, args.deprecated
                                                                                                    ))

        endpoint_remove = endpoint_subparsers.add_parser("remove", help="Remove an endpoint")
        endpoint_remove.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_endpoint(args.id))

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
        endpoint_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_endpoint(args.id, args.usage, args.protocol, args.deployed, args.endpoints, args.options,
                                                                                                      args.messagegroups, args.documentation, args.description, args.labels, args.name,
                                                                                                      args.channel, args.deprecated
                                                                                                      ))

        endpoint_show = endpoint_subparsers.add_parser("show", help="Show an endpoint")
        endpoint_show.add_argument("--id", required=True, help="Endpoint ID")
        endpoint_show.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).show_endpoint(args.id))

        endpoint_apply = endpoint_subparsers.add_parser("apply", help="Apply an endpoint JSON")
        endpoint_apply.add_argument("-f", "--file", required=True, help="JSON file containing endpoint data")
        endpoint_apply.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).apply_endpoint(args.file))

        messagegroup_subparsers = manifest_subparsers.add_parser("messagegroup", help="Manage message groups").add_subparsers(
            dest="messagegroup_command", help="Message group commands")

        messagegroup_add = messagegroup_subparsers.add_parser("add", help="Add a new message group")
        messagegroup_add.add_argument("--id", required=True, help="Message group ID")
        messagegroup_add.add_argument("--format", choices=["CloudEvents", "None"], help="Message group format")
        messagegroup_add.add_argument("--protocol", help="protocol identifier")
        add_common_arguments(messagegroup_add)
        messagegroup_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_messagegroup(args.id, args.format, args.documentation, args.description, args.labels, args.name,
                                                                                                            args.protocol
                                                                                                            ))

        messagegroup_remove = messagegroup_subparsers.add_parser("remove", help="Remove a message group")
        messagegroup_remove.add_argument("--id", required=True, help="Message group ID")
        messagegroup_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_messagegroup(args.id))

        messagegroup_edit = messagegroup_subparsers.add_parser("edit", help="Edit a message group")
        messagegroup_edit.add_argument("--id", required=True, help="Message group ID")
        messagegroup_edit.add_argument("--format", choices=["CloudEvents", "None"], help="Message group format")
        messagegroup_edit.add_argument("--protocol", help="protocol identifier")
        add_common_arguments(messagegroup_edit)
        messagegroup_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_messagegroup(args.id, args.format, args.documentation, args.description, args.labels, args.name,
                                                                                                              args.protocol
                                                                                                              ))

        messagegroup_show = messagegroup_subparsers.add_parser("show", help="Show a message group")
        messagegroup_show.add_argument("--id", required=True, help="Message group ID")
        messagegroup_show.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).show_messagegroup(args.id))

        messagegroup_apply = messagegroup_subparsers.add_parser("apply", help="Apply a message group JSON")
        messagegroup_apply.add_argument("-f", "--file", required=True, help="JSON file containing message group data")
        messagegroup_apply.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).apply_messagegroup(args.file))

        message_subparsers = manifest_subparsers.add_parser(
            "message", help="Manage messages").add_subparsers(dest="message_command", help="Message commands")

        message_add = message_subparsers.add_parser("add", help="Add a new message")
        message_add.add_argument("--groupid", required=True, help="Message group ID")
        message_add.add_argument("--id", required=True, help="Message ID")
        message_add.add_argument("--format", choices=["CloudEvents", "None"],
                                 help="Message format", default="CloudEvents")
        message_add.add_argument("--protocol", choices=["AMQP", "MQTT", "NATS",
                                 "HTTP", "Kafka", "None"], help="Message protocol", default="None")
        message_add.add_argument("--schemaformat", help="Schema format")
        message_add.add_argument("--schemagroup", help="Schema group ID")
        message_add.add_argument("--schemaid", help="Schema ID")
        message_add.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_add)
        message_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_message(args.groupid, args.id, args.format, args.protocol, args.schemaformat, args.schemagroup, args.schemaid,
                                                                                                  args.schemaurl, args.documentation, args.description, args.labels, args.name
                                                                                                  ))

        message_remove = message_subparsers.add_parser("remove", help="Remove a message")
        message_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_remove.add_argument("--id", required=True, help="Message ID")
        message_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_message(args.groupid, args.id))

        message_edit = message_subparsers.add_parser("edit", help="Edit a message")
        message_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_edit.add_argument("--id", required=True, help="Message ID")
        message_edit.add_argument("--format", choices=["CloudEvents", "None"], help="Message format")
        message_edit.add_argument("--protocol", choices=["AMQP", "MQTT",
                                  "NATS", "HTTP", "Kafka", "None"], help="Message protocol")
        message_edit.add_argument("--schemaformat", help="Schema format")
        message_edit.add_argument("--schemagroup", help="Schema group ID")
        message_edit.add_argument("--schemaid", help="Schema ID")
        message_edit.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(message_edit)
        message_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(args.groupid, args.id, args.format, args.protocol, args.schemaformat, args.schemagroup, args.schemaid,
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
            sc = CatalogSubcommands(args.catalog)
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
        message_cloudevent_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            args.groupid, args.id, "CloudEvents/1.0", "None", args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_cloudevent_remove = message_cloudevent_subparsers.add_parser("remove", help="Remove a CloudEvent")
        message_cloudevent_remove.add_argument("--groupid", required=True, help="Message group ID", type=str)
        message_cloudevent_remove.add_argument("--id", required=True, help="Message ID and CloudEvents type", type=str)
        message_cloudevent_remove.add_argument("--epoch", required=True, type=int, help="Epoch number")
        message_cloudevent_remove.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).remove_message(args.groupid, args.id))

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
        message_cloudevent_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_cloudevents_message_metadata(
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
        message_cloudevent_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_cloudevents_message_metadata(
            args.groupid, args.id, args.attribute, args.type, args.description, args.value, args.required))

        message_cloudevent_metadata_remove = message_cloudevent_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_cloudevent_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_cloudevent_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_cloudevent_metadata_remove.add_argument("--attribute", required=True, help="CloudEvents attribute")
        message_cloudevent_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_cloudevents_message_metadata(args.groupid, args.id, args.key))

        message_amqp_subparsers = manifest_subparsers.add_parser(
            "amqp", help="Manage AMQP").add_subparsers(dest="amqp_command", help="AMQP commands")
        message_amqp_metadata_subparsers = message_amqp_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_amqp_message(args):
            sc = CatalogSubcommands(args.catalog)
            sc.add_message(args.groupid, args.id, "None", "AMQP/1.0", args.schemaformat, args.schemagroup,
                           args.schemaid, args.schemaurl, args.documentation, args.description, args.labels, args.name)
            sc.add_amqp_message_metadata(args.groupid, args.id, "properties",
                                         "subject", "string", None, "Subject", True)

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
        message_amqp_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            args.groupid, args.id, "None", "AMQP/1.0", args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_amqp_remove = message_amqp_subparsers.add_parser("remove", help="Remove a message")
        message_amqp_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_remove.add_argument("--id", required=True, help="Message ID")
        message_amqp_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_message(args.groupid, args.id))

        message_amqp_metadata_add = message_amqp_metadata_subparsers.add_parser("add", help="Add a new metadata field")
        message_amqp_metadata_add.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_metadata_add.add_argument("--id", required=True, help="Message ID")
        message_amqp_metadata_add.add_argument("--section", required=True, choices=[
                                               "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_amqp_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_amqp_metadata_add.add_argument("--value", required=False, help="Metadata value")
        message_amqp_metadata_add.add_argument("--description", help="Metadata description")
        message_amqp_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        message_amqp_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_amqp_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.value, args.description, args.required))

        message_amqp_metadata_edit = message_amqp_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_amqp_metadata_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_metadata_edit.add_argument("--id", required=True, help="Message ID")
        message_amqp_metadata_edit.add_argument("--section", required=True, choices=[
                                                "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_edit.add_argument("--name", help="Metadata name")
        message_amqp_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_amqp_metadata_edit.add_argument("--value", required=False, help="Metadata value")
        message_amqp_metadata_edit.add_argument("--description", help="Metadata description")
        message_amqp_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        message_amqp_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_amqp_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.value, args.description, args.required))

        message_amqp_metadata_remove = message_amqp_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_amqp_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_amqp_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_amqp_metadata_remove.add_argument("--section", required=True, choices=[
                                                  "properties", "application-properties"], help="Metadata section")
        message_amqp_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        message_amqp_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_amqp_message_metadata(args.groupid, args.id, args.name, args.section))

        message_mqtt_subparsers = manifest_subparsers.add_parser(
            "mqtt", help="Manage MQTT").add_subparsers(dest="mqtt_command", help="MQTT commands")
        message_mqtt_metadata_subparsers = message_mqtt_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_mqtt_message(args):
            sc = CatalogSubcommands(args.catalog)
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
        message_mqtt_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            args.groupid, args.id, "None", "MQTT/" + args.mqtt_version, args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_mqtt_remove = message_mqtt_subparsers.add_parser("remove", help="Remove a message")
        message_mqtt_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_mqtt_remove.add_argument("--id", required=True, help="Message ID")
        message_mqtt_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_message(args.groupid, args.id))

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
        message_mqtt_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_mqtt_message_metadata(
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
        message_mqtt_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_mqtt_message_metadata(
            args.groupid, args.id, args.name, args.type, args.value, args.description, args.required))

        message_mqtt_metadata_remove = message_mqtt_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_mqtt_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_mqtt_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_mqtt_metadata_remove.add_argument("--section", required=False, choices=["properties", "topic"], help="Metadata section")
        message_mqtt_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        message_mqtt_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_mqtt_message_metadata(args.groupid, args.id, args.section, args.name))

        message_kafka_subparsers = manifest_subparsers.add_parser(
            "kafka", help="Manage Kafka").add_subparsers(dest="kafka_command", help="Kafka commands")
        message_kafka_metadata_subparsers = message_kafka_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_kafka_message(args):
            sc = CatalogSubcommands(args.catalog)
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
        message_kafka_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            args.groupid, args.id, "None", "Kafka", args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_kafka_remove = message_kafka_subparsers.add_parser("remove", help="Remove a message")
        message_kafka_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_remove.add_argument("--id", required=True, help="Message ID")
        message_kafka_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_message(args.groupid, args.id))

        message_kafka_metadata_add = message_kafka_metadata_subparsers.add_parser(
            "add", help="Add a new metadata field")
        message_kafka_metadata_add.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_metadata_add.add_argument("--id", required=True, help="Message ID")
        message_kafka_metadata_add.add_argument("--section", required=True, choices=["headers"], help="Metadata section")
        message_kafka_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_kafka_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_kafka_metadata_add.add_argument("--value", required=True, help="Metadata value")
        message_kafka_metadata_add.add_argument("--description", help="Metadata description")
        message_kafka_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        message_kafka_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_kafka_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.value, args.description, args.required))

        message_kafka_metadata_edit = message_kafka_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_kafka_metadata_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_metadata_edit.add_argument("--id", required=True, help="Message ID")
        message_kafka_metadata_edit.add_argument("--section", required=True, choices=["headers"], help="Metadata section")
        message_kafka_metadata_edit.add_argument("--name", help="Metadata name")
        message_kafka_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_kafka_metadata_edit.add_argument("--value", help="Metadata value")
        message_kafka_metadata_edit.add_argument("--description", help="Metadata description")
        message_kafka_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        message_kafka_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_kafka_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.value, args.description, args.required))

        message_kafka_metadata_remove = message_kafka_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_kafka_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_kafka_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_kafka_metadata_remove.add_argument("--name", required=True, help="Metadata name")
        message_kafka_metadata_remove.add_argument(
            "--section", required=True, choices=["headers"], help="Metadata section")
        message_kafka_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_kafka_message_metadata(args.groupid, args.id, args.section, args.name))

        message_http_subparsers = manifest_subparsers.add_parser(
            "http", help="Manage HTTP").add_subparsers(dest="http_command", help="HTTP commands")
        message_http_metadata_subparsers = message_http_subparsers.add_parser(
            "metadata", help="Manage message metadata").add_subparsers(dest="metadata_command", help="Metadata commands")

        def _add_http_message(args):
            sc = CatalogSubcommands(args.catalog)
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
        message_http_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_message(
            args.groupid, args.id, "None", "HTTP", args.schemaformat, args.schemagroup, args.schemaid,
            args.schemaurl, args.documentation, args.description, args.labels, args.name))

        message_http_remove = message_http_subparsers.add_parser("remove", help="Remove a message")
        message_http_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_http_remove.add_argument("--id", required=True, help="Message ID")
        message_http_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_message(args.groupid, args.id))

        message_http_metadata_add = message_http_metadata_subparsers.add_parser("add", help="Add a new metadata field")
        message_http_metadata_add.add_argument("--groupid", required=True, help="Message group ID")
        message_http_metadata_add.add_argument("--id", required=True, help="Message ID")
        message_http_metadata_add.add_argument("--key", required=True, help="Metadata key")
        message_http_metadata_add.add_argument("--section", required=False,
                                               choices=["headers", "query"], help="Metadata section")
        message_http_metadata_add.add_argument("--name", required=True, help="Metadata name")
        message_http_metadata_add.add_argument("--type", required=True, choices=PROPERTY_TYPES, help="Metadata type")
        message_http_metadata_add.add_argument("--value", required=True, help="Metadata value")
        message_http_metadata_add.add_argument("--description", help="Metadata description")
        message_http_metadata_add.add_argument("--required", type=bool, help="Metadata required status")
        message_http_metadata_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_http_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.value, args.description, args.required))

        message_http_metadata_edit = message_http_metadata_subparsers.add_parser("edit", help="Edit a metadata field")
        message_http_metadata_edit.add_argument("--groupid", required=True, help="Message group ID")
        message_http_metadata_edit.add_argument("--id", required=True, help="Message ID")
        message_http_metadata_edit.add_argument("--key", required=True, help="Metadata key")
        message_http_metadata_edit.add_argument("--section", required=False,
                                                choices=["headers", "query"], help="Metadata section")
        message_http_metadata_edit.add_argument("--name", help="Metadata name")
        message_http_metadata_edit.add_argument("--type", choices=PROPERTY_TYPES, help="Metadata type")
        message_http_metadata_edit.add_argument("--value", help="Metadata value")
        message_http_metadata_edit.add_argument("--description", help="Metadata description")
        message_http_metadata_edit.add_argument("--required", type=bool, help="Metadata required status")
        message_http_metadata_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_http_message_metadata(
            args.groupid, args.id, args.section, args.name, args.type, args.value, args.description, args.required))

        message_http_metadata_remove = message_http_metadata_subparsers.add_parser(
            "remove", help="Remove a metadata field")
        message_http_metadata_remove.add_argument("--groupid", required=True, help="Message group ID")
        message_http_metadata_remove.add_argument("--id", required=True, help="Message ID")
        message_http_metadata_remove.add_argument("--name", required=True, help="Metadata key")
        message_http_metadata_remove.add_argument(
            "--section", required=False, choices=["headers", "query"], help="Metadata section")
        message_http_metadata_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_http_message_metadata(args.groupid, args.id, args.section, args.name))

        message_show = message_subparsers.add_parser("show", help="Show a message")
        message_show.add_argument("--groupid", required=True, help="Message group ID")
        message_show.add_argument("--id", required=True, help="Message ID")
        message_show.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).show_message(args.groupid, args.id))

        schemagroup_subparsers = manifest_subparsers.add_parser("schemagroup", help="Manage schema groups").add_subparsers(
            dest="schemagroup_command", help="Schema group commands")

        schemagroup_add = schemagroup_subparsers.add_parser("add", help="Add a new schema group")
        schemagroup_add.add_argument("--id", required=True, help="Schema group ID")
        add_common_arguments(schemagroup_add)
        schemagroup_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_schemagroup(
            args.id, args.documentation, args.description, args.labels, args.name))

        schemagroup_remove = schemagroup_subparsers.add_parser("remove", help="Remove a schema group")
        schemagroup_remove.add_argument("--id", required=True, help="Schema group ID")
        schemagroup_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_schemagroup(args.id))

        schemagroup_edit = schemagroup_subparsers.add_parser("edit", help="Edit a schema group")
        schemagroup_edit.add_argument("--id", required=True, help="Schema group ID")
        add_common_arguments(schemagroup_edit)
        schemagroup_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_schemagroup(args.id, args.documentation, args.description, args.labels, args.name ))

        schemagroup_show = schemagroup_subparsers.add_parser("show", help="Show a schema group")
        schemagroup_show.add_argument("--id", required=True, help="Schema group ID")
        schemagroup_show.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).show_schemagroup(args.id))

        schemagroup_apply = schemagroup_subparsers.add_parser("apply", help="Apply a schema group JSON")
        schemagroup_apply.add_argument("-f", "--file", required=True, help="JSON file containing schema group data")
        schemagroup_apply.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).apply_schemagroup(args.file))

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
        schema_add.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).add_schemaversion(args.groupid, args.id, args.format, args.versionid, args.schema, args.schemaimport,
                                                                                                args.schemaurl, args.documentation, args.description, args.labels, args.name
                                                                                                ))

        schema_remove = schema_subparsers.add_parser("remove", help="Remove a schema or schema version")
        schema_remove.add_argument("--groupid", required=True, help="Schema group ID")
        schema_remove.add_argument("--id", required=True, help="Schema ID")
        schema_remove.add_argument("--versionid", required=True, help="Schema version ID")
        schema_remove.set_defaults(func=lambda args: CatalogSubcommands(
            args.catalog).remove_schema(args.groupid, args.id, args.versionid))

        schema_edit = schema_subparsers.add_parser("edit", help="Edit a schema or schema version")
        schema_edit.add_argument("--groupid", required=True, help="Schema group ID")
        schema_edit.add_argument("--id", required=True, help="Schema ID")
        schema_edit.add_argument("--format", help="Schema format")
        schema_edit.add_argument("--versionid", required=True, help="Schema version ID")
        schema_edit.add_argument("--schema", help="Inline schema")
        schema_edit.add_argument("--schemaimport", help="Schema import file location or URL")
        schema_edit.add_argument("--schemaurl", help="Schema URL")
        add_common_arguments(schema_edit)
        schema_edit.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).edit_schemaversion(args.groupid, args.id, args.versionid, args.format, args.schema, args.schemaimport,
                                                                                                  args.schemaurl, args.documentation, args.description, args.labels, args.name
                                                                                                  ))

        schema_show = schema_subparsers.add_parser("show", help="Show a schema")
        schema_show.add_argument("--groupid", required=True, help="Schema group ID")
        schema_show.add_argument("--id", required=True, help="Schema ID")
        schema_show.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).show_schema(args.groupid, args.id))

        schema_apply = schema_subparsers.add_parser("apply", help="Apply a schema JSON")
        schema_apply.add_argument("-f", "--file", required=True, help="JSON file containing schema data")
        schema_apply.set_defaults(func=lambda args: CatalogSubcommands(args.catalog).apply_schema(args.file))