""" Core functions for the xregistry commands """

import json
import os
from pyexpat import model
from typing import Any, Dict, List, Tuple, Union
import urllib.request
import urllib.parse
import urllib.error
from pydantic import Json
from pydash import url
import yaml
from ..common.model import Model

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]

class XRegistryLoader:
    """ Class to handle the loading of definitions """
    def __init__(self, model_path: str | None = None):
        self.schemas_handled = set()
        self.current_url = ""
        self.model = Model(model_path=model_path)

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

    def _load_core(self, definition_uri: str, headers: dict, ignore_handled: bool = False) -> Tuple[str|None, JsonNode]:
        """ Load the definition file, which may be a JSON Schema"""
        docroot: JsonNode = {}
        try:
            if definition_uri.startswith("http"):
                parsed_uri = urllib.parse.urlparse(definition_uri)
                query = urllib.parse.parse_qs(parsed_uri.query)
                if "inline" not in query:
                    query["inline"] = ["*"]
                new_query = urllib.parse.urlencode(query, doseq=True)
                definition_uri = urllib.parse.urlunparse(parsed_uri._replace(query=new_query))
                req = urllib.request.Request(definition_uri, headers=headers)
                with urllib.request.urlopen(req) as url:
                    # URIs may redirect and we only want to handle each file once
                    self.current_url = url.url
                    parsed_url = urllib.parse.urlparse(url.url)
                    definition_uri = urllib.parse.urlunparse(
                        parsed_url._replace(fragment=''))
                    if not ignore_handled:
                        if definition_uri not in self.schemas_handled:
                            self.schemas_handled.add(definition_uri)
                        else:
                            return None, None
                    text_doc = url.read().decode()
                    response_headers = dict(url.info())
                    if 'xRegistry-schemaid' in response_headers:
                        new_docroot = {}
                        for header, value in response_headers.items():
                            if header.startswith('xRegistry-'):
                                key = header[len('xRegistry-'):]
                                if key == "defaultversionid":
                                    key = "versionid"
                                new_docroot[key] = value
                        try:
                            new_docroot['schema'] = json.loads(text_doc)
                        except json.decoder.JSONDecodeError:
                            try:
                                new_docroot['schema'] = yaml.safe_load(text_doc)
                            except yaml.YAMLError:
                                new_docroot['schema'] = text_doc
                        docroot = new_docroot
                    else:
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
                    if definition_uri not in self.schemas_handled:
                        self.schemas_handled.add(definition_uri)
                    else:
                        return None, None
                with open(os.path.join(os.getcwd(), definition_uri), "r", encoding='utf-8') as f:
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

        return definition_uri, docroot


    def load(self, definition_uri: str, headers: dict, load_schema: bool = False, ignore_handled: bool = False, messagegroup_filter: str|None = None ) -> Tuple[str|None, JsonNode]:
        """ Load the definition file, which may be a JSON Schema """
        # for a CloudEvents message definition group, we
        # normalize the document to be a messagegroups doc
        _definitions_file, docroot = self._load_core(definition_uri, headers, ignore_handled)
        if docroot is None:
            return None, None
        if _definitions_file:
            definition_uri = _definitions_file
        if load_schema:
            return definition_uri, docroot

        # if "$schema" in docroot:
        #     if docroot["$schema"] != "https://cloudevents.io/schemas/registry":
        #         print("unsupported schema:" + docroot["$schema"])
        #         return None, None
        if not isinstance(docroot, dict):
            raise ValueError("Document is not valid")
        
        newdocroot : Dict[str, JsonNode] = {}
        for key, group in self.model.groups.items():
            id_key:str = group["singular"] + "id"
            plural_key:str = group["plural"]
            if id_key in docroot and isinstance(docroot[id_key], str):
                newdocroot[plural_key] = {str(docroot[id_key]): docroot}
                
        for key, group in self.model.groups.items():
            plural_key:str = group["plural"]
            url_key:str = plural_key + "url"
            if plural_key not in docroot and url_key in docroot and isinstance(docroot[url_key], str):
                _, subroot = self._load_core(str(docroot[url_key]), headers)
                if subroot is not None:
                    newdocroot[plural_key] = subroot
                del docroot[url_key] 

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

        return definition_uri, docroot

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
                                   

                        

        