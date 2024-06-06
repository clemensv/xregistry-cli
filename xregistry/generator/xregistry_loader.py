""" Core functions for the xregistry commands """

import json
import os
from typing import Dict, List, Tuple, Union
import urllib.request
import urllib.parse
import urllib.error
import yaml

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, None]

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


    def load(self, definitions_file: str, headers: dict, load_schema: bool = False, ignore_handled: bool = False) -> Tuple[str|None, JsonNode]:
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

        return definitions_file, docroot
