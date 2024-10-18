""" Core functions for the xregistry commands """

import json
import os
from typing import Any, Dict, List, Tuple, Union
import urllib.request
import urllib.parse
import urllib.error
from pydantic import Json
import yaml

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]

class XRegistryLoader:
    """ Class to handle the loading of definitions """
    def __init__(self):
        self.schemas_handled = set()
        self.current_url = ""

    def add_schema_to_handled(self, url):
        """ Add a schema URL to the set of schemas handled"""
        self.schemas_handled.add(url)

    def reset_schemas_handled(self):
        """ Reset the set of schemas handled """
        self.schemas_handled = set()

    def get_current_url(self):
        """ Get the current URL """
        return self.current_url

    def set_current_url(self, url):
        """ Set the current URL"""
        self.current_url = url

    def get_schemas_handled(self):
        """ Get the set of schemas handled"""
        return self.schemas_handled

    def _load_core(self, definitions_file: str, headers: dict, ignore_handled: bool = False) -> Tuple[str|None, JsonNode]:
        """ Load the definition file, which may be a JSON Schema"""
        docroot: JsonNode = {}
        try:
            if definitions_file.startswith("http"):
                req = urllib.request.Request(definitions_file, headers=headers)
                with urllib.request.urlopen(req) as url:
                    # URIs may redirect and we only want to handle each file once
                    self.current_url = url.url
                    parsed_url = urllib.parse.urlparse(url.url)
                    definitions_file = urllib.parse.urlunparse(
                        parsed_url._replace(fragment=''))
                    if not ignore_handled:
                        if definitions_file not in self.schemas_handled:
                            self.schemas_handled.add(definitions_file)
                        else:
                            return None, None
                    text_doc = url.read().decode()
                    try:
                        docroot = json.loads(text_doc)
                    except json.decoder.JSONDecodeError:
                        try:
                            # if the JSON is invalid, try to parse it as YAML
                            docroot = yaml.safe_load(text_doc)
                        except yaml.YAMLError:
                            docroot = text_doc
            else:
                if not ignore_handled:
                    if definitions_file not in self.schemas_handled:
                        self.schemas_handled.add(definitions_file)
                    else:
                        return None, None
                with open(os.path.join(os.getcwd(), definitions_file), "r", encoding='utf-8') as f:
                    text_doc = f.read()
                    try:
                        docroot = json.loads(text_doc)
                    except json.decoder.JSONDecodeError as e1:
                        try:
                            # if the JSON is invalid, try to parse it as YAML
                            docroot = yaml.safe_load(text_doc)
                        except yaml.YAMLError as e2:
                            raise e1 from e2
        except urllib.error.URLError as e:
            print("An error occurred while trying to open the URL: ", e)
            return None, None
        except json.decoder.JSONDecodeError as e:
            print("An error occurred while trying to parse the JSON file: ", e)
            return None, None
        except IOError as e:
            print("An error occurred while trying to access the file: ", e)
            return None, None

        return definitions_file, docroot


    def load(self, definitions_file: str, headers: dict, load_schema: bool = False, ignore_handled: bool = False, messagegroup_filter: str|None = None ) -> Tuple[str|None, JsonNode]:
        """ Load the definition file, which may be a JSON Schema """
        # for a CloudEvents message definition group, we
        # normalize the document to be a messagegroups doc
        _definitions_file, docroot = self._load_core(definitions_file, headers, ignore_handled)
        if docroot is None:
            return None, None
        if _definitions_file:
            definitions_file = _definitions_file
        if load_schema:
            return definitions_file, docroot

        # if "$schema" in docroot:
        #     if docroot["$schema"] != "https://cloudevents.io/schemas/registry":
        #         print("unsupported schema:" + docroot["$schema"])
        #         return None, None
        if isinstance(docroot, dict):
            if "messagegroupsurl" in docroot and isinstance(docroot["messagegroupsurl"], str):
                _, subroot = self._load_core(docroot["messagegroupsurl"], headers)
                docroot["messagegroups"] = subroot
                docroot["messagegroupsurl"] = None
            if "schemagroupsurl" in docroot and isinstance(docroot["schemagroupsurl"], str):
                _, subroot = self._load_core(docroot["schemagroupsurl"], headers)
                docroot["schemagroups"] = subroot
                docroot["schemagroupsurl"] = None
            if "endpointsurl" in docroot and isinstance(docroot["endpointsurl"], str):
                _, subroot = self._load_core(docroot["endpointsurl"], headers)
                docroot["endpoints"] = subroot
                docroot["endpointsurl"] = None

        self.preprocess_manifest(docroot)

        if messagegroup_filter:
            if isinstance(docroot, dict):
                if "messagegroups" in docroot:
                    if isinstance(docroot["messagegroups"], dict):
                        if messagegroup_filter in docroot["messagegroups"]:
                            docroot["messagegroups"] = {messagegroup_filter: docroot["messagegroups"][messagegroup_filter]}
                    else:
                        print("messagegroups is not a dict")
                        return None, None
                else:
                    print("messagegroups not found in document")
                    return None, None
            else:
                print("document is not a dict")
                return None, None

        return definitions_file, docroot

    def preprocess_manifest(self, xreg_doc: JsonNode):
        """ Preprocess the manifest document """

        def patch_cloudevents_schema(message: Dict[str, JsonNode]):
            """ Patch the CloudEvents schema """
            metadata: JsonNode = message.get("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError(f"Message '{messageid}' has invalid metadata")
            required_fields = ["id", "time", "source", "type"]
            for field in required_fields:
                if field not in metadata.keys():
                    if field == "type":
                        raise ValueError(f"Message '{messageid}' is missing required 'type' attribute")
                    elif field == "source":
                        metadata[field] = {"required": True, "type": "uritemplate", "value": "{sourceuri}", "description": "The URI of the source of the event"}
                    elif field == "id":
                        metadata[field] = {"type": "string", "required": True, "description": "A unique identifier for the event"}
                    elif field == "time":
                        metadata[field] = {"type": "string", "required": True, "description": "A ISO8601 timestamp of when the event happened"}
            message["metadata"] = metadata


        if isinstance(xreg_doc, dict):
            if "messagegroups" in xreg_doc:
                if isinstance(xreg_doc["messagegroups"], dict):
                    for messagegroupid, messagegroup in xreg_doc["messagegroups"].items():
                        if isinstance(messagegroup, dict) and "messages" in messagegroup:
                            if not "messagegroupid" in messagegroup:
                                messagegroup["messagegroupid"] = messagegroupid
                            if isinstance(messagegroup["messages"], dict):
                                for messageid, message in messagegroup["messages"].items():
                                    if isinstance(message, dict):
                                        if not "messageid" in message:
                                            message["messageid"] = messageid
                                        if message.get("format") == "CloudEvents/1.0":
                                            patch_cloudevents_schema(message)
            if "schemagroups" in xreg_doc:
                if isinstance(xreg_doc["schemagroups"], dict):
                    for schemagroupid, schemagroup in xreg_doc["schemagroups"].items():
                        if isinstance(schemagroup, dict) and "schemas" in schemagroup:
                            if not "schemagroupid" in schemagroup:
                                schemagroup["schemagroupid"] = schemagroupid
                            if isinstance(schemagroup["schemas"], dict):
                                for schemaid, schema in schemagroup["schemas"].items():
                                    if isinstance(schema, dict):
                                        if not "schemaid" in schema:
                                            schema["schemaid"] = schemaid
            if "endpoint" in xreg_doc:
                if isinstance(xreg_doc["endpoint"], dict):
                    for endpointid, endpoint in xreg_doc["endpoint"].items():
                        if isinstance(endpoint, dict):
                            if not "endpointid" in endpoint:
                                endpoint["endpointid"] = endpointid
                            if "messages" in endpoint:
                                 if isinstance(endpoint["messages"], dict):
                                    for messageid, message in endpoint["messages"].items():
                                        if isinstance(message, dict):
                                            if not "messageid" in message:
                                                message["messageid"] = messageid
                                            if message.get("format") == "CloudEvents/1.0":
                                               patch_cloudevents_schema(message)
                                   

                        

        