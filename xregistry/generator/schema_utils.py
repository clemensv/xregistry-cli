import re
import urllib.parse
from typing import Any, Dict, List, Optional, Set, Union

import jsonpointer

from xregistry.cli import logger
from xregistry.generator.generator_context import GeneratorContext
from xregistry.generator.jinja_filters import JinjaFilters

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]

class SchemaUtils:
    """Utility class for schema operations."""

    schema_files_collected: Set[str] = set()
    schema_references_collected: Set[str] = set()

    @staticmethod
    def get_json_pointer(root: JsonNode, node: JsonNode) -> str:
        """Get the JSON Pointer to a node in a JSON document."""
        logger.debug("Getting JSON pointer to node in JSON document")

        def find_path(current: JsonNode, target: JsonNode, path: List[str]) -> Optional[List[str]]:
            if current is target:
                return path
            elif isinstance(current, dict):
                for k, v in current.items():
                    new_path = find_path(v, target, path + [k])
                    if new_path is not None:
                        return new_path
            elif isinstance(current, list):
                for i, item in enumerate(current):
                    new_path = find_path(item, target, path + [str(i)])
                    if new_path is not None:
                        return new_path
            return None

        def path_to_pointer(path: List[str]) -> str:
            pointer = ""
            for p in path:
                escaped = p.replace("~", "~0").replace("/", "~1")
                pointer += f"/{escaped}"
            return pointer

        path = find_path(root, node, [])
        if path is None:
            raise RuntimeError("Node not found in document")
        return path_to_pointer(path)

    @staticmethod
    def schema_type(ctx: GeneratorContext, schema_ref: JsonNode, project_name: str, root: JsonNode, schema_format: str = "jsonschema/draft-07") -> str:
        """Get the schema type from a schema reference."""
        logger.debug("Getting schema type from schema reference")

        class_name: str = ''
        schema_obj: JsonNode = None

        def resolve_pointer(root: JsonNode, schema_ref: str) -> JsonNode:
            if schema_ref.startswith("#"):
                try:
                    obj = jsonpointer.resolve_pointer(root, schema_ref[1:])
                    if isinstance(obj, (dict, list, str)):
                        return obj
                    else:
                        raise RuntimeError(f"Schema not found: {schema_ref}")
                except jsonpointer.JsonPointerException as jpe:
                    schema_ref = schema_ref[1:]
            if schema_ref.startswith("/"):
                schema_ref = urllib.parse.urljoin(ctx.base_uri, schema_ref)            
            schema_ref, fragment = urllib.parse.urldefrag(schema_ref)
            _, obj = ctx.loader.load(schema_ref, {}, True, True)
            if fragment:
                fragment, class_name = fragment.split(":")
                obj = resolve_pointer(obj, fragment)
            return obj

        if schema_format.lower().startswith("proto") and isinstance(schema_ref, str) and SchemaUtils.is_proto_doc(schema_ref):
            ptr = SchemaUtils.get_json_pointer(root, schema_ref)
            ptr = ptr.rsplit("/", 1)[0]
            SchemaUtils.schema_references_collected.add('#' + ptr)
            schema_format = schema_format.lower().split("/")[0]
            schema_obj = schema_ref
            schema_ref = '#' + ptr
        elif isinstance(schema_ref, str):
            if ":" in schema_ref:
                schema_ref, class_name = schema_ref.split(":")
            if schema_ref.startswith("#"):
                if schema_ref not in SchemaUtils.schema_references_collected:
                    SchemaUtils.schema_references_collected.add(schema_ref)
                schema_obj = resolve_pointer(root, schema_ref)
            else:
                schema_ref, fragment = urllib.parse.urldefrag(schema_ref)
                _, schema_obj = ctx.loader.load(schema_ref, {}, True, True)
                if fragment:
                    fragment, class_name = fragment.split(":")
                    schema_obj = resolve_pointer(schema_obj, fragment)

            schema_version = None
            if isinstance(schema_obj, dict) and "versions" in schema_obj and isinstance(schema_obj['versions'], dict):
                latestversion = str(schema_obj.get('defaultversionid', ''))
                if not latestversion or latestversion not in schema_obj['versions']:
                    versions = schema_obj['versions']
                    latestversion = max(versions.keys())
                if latestversion not in schema_obj['versions']:
                    raise RuntimeError(f"Schema version not found: {latestversion}")
                schema_version = schema_obj['versions'][latestversion]
                if not class_name:
                    class_name = str(schema_obj.get("schemaid", ''))
                if not class_name:
                    # Extract schema name from the reference path (e.g., /schemagroups/.../schemas/orderData)
                    path_elements = schema_ref.split('/')
                    if len(path_elements) >= 2 and path_elements[-2] == 'schemas':
                        class_name = path_elements[-1]
                parent_reference = schema_ref.rsplit("/", 2)[0]
                try:
                    parent = jsonpointer.resolve_pointer(root, parent_reference[1:])
                    if parent and isinstance(parent, dict):
                        # Try to get schema group ID from the parent object
                        prefix = parent.get("schemagroupid", '')
                        if not prefix:
                            # If not in the object, extract from the reference path
                            # e.g., #/schemagroups/Contoso.ERP.Events/schemas/orderData → parent_reference = #/schemagroups/Contoso.ERP.Events/schemas
                            # We want "Contoso.ERP.Events"
                            path_elements = schema_ref.split('/')
                            for i, elem in enumerate(path_elements):
                                if elem == 'schemas' and i > 0:
                                    prefix = path_elements[i - 1]
                                    break
                        if class_name and prefix and not class_name.startswith(prefix):
                            class_name = prefix + '.' + class_name
                except jsonpointer.JsonPointerException:
                    raise RuntimeError(f"Schema not found: {parent_reference}")
            elif isinstance(schema_obj, dict) and "versionid" in schema_obj:
                schema_version = schema_obj
                parent_reference = schema_ref.rsplit("/", 1)[0]
                if "schemaid" not in schema_obj:
                    parent = jsonpointer.resolve_pointer(root, parent_reference[1:])
                    if parent and isinstance(parent, dict) and not class_name:
                        class_name = parent.get("schemaid", class_name)
                else:
                    class_name = str(schema_obj.get("schemaid", class_name))
                # we now get the group to see whether we need to prefix the class name
                if "defaultversionurl" not in schema_obj and "self" not in schema_obj:
                    parent_reference = parent_reference.rsplit("/", 2)[0]
                    try:
                        parent = jsonpointer.resolve_pointer(root, parent_reference[1:])
                        if parent and isinstance(parent, dict):
                            prefix = parent.get("schemagroupid", '')
                            if not class_name.startswith(prefix):
                                class_name = prefix + '.' + class_name
                    except jsonpointer.JsonPointerException:
                        raise RuntimeError(f"Schema not found: {parent_reference}")
                else:
                    version_url = str(schema_obj.get("defaultversionurl", schema_obj.get("self", '')))
                    # version url is {baseurl}/schemagroups/{schemagroupid}/schemas/{schemaid}/versions/{versionid}
                    match = re.search(r"/schemagroups/([^/]+)/", version_url)
                    if match:
                        prefix = match.group(1)
                    else:
                        raise RuntimeError(f"Schema group ID not found in version URL: {version_url}")
                    if not class_name.startswith(prefix):
                        class_name = prefix + '.' + class_name

            if not schema_version or not isinstance(schema_version, dict):
                raise RuntimeError(f"Schema version not found: {schema_ref}")
            if not "format" in schema_version or not isinstance(schema_version["format"], str) or schema_format != schema_version["format"]:
                raise RuntimeError(f"Schema format mismatch: {schema_format} != {str(schema_version['format']) if 'format' in schema_version else ''}")
            schema_format = schema_version["format"].lower().split("/")[0]
            if "schemaurl" in schema_version:
                external_schema_url = str(schema_version["schemaurl"])
                _, schema_obj = ctx.loader.load(external_schema_url, {}, True)
                if not schema_obj:
                    raise RuntimeError(f"Schema not found: {external_schema_url}")
            elif "schema" in schema_version:
                schema_obj = schema_version["schema"]
            else:
                raise RuntimeError(f"Schema not found: {schema_ref}")
        else:
            ptr = SchemaUtils.get_json_pointer(root, schema_ref)
            ptr = ptr.rsplit("/", 1)[0]
            SchemaUtils.schema_references_collected.add('#' + ptr)
            schema_format = schema_format.lower().split("/")[0]
            schema_obj = schema_ref
            schema_ref = '#' + ptr

        if schema_format.startswith("avro"):
            if isinstance(schema_obj, dict) and "type" in schema_obj and schema_obj["type"] == "record":
                ref = str(f"{schema_obj['namespace']}.{schema_obj['name']}" if "namespace" in schema_obj else schema_obj["name"])
                #if class_name and ref.lower() != class_name.lower():
                #    raise RuntimeError(f"Avro: Class name reference mismatch for top-level record object: {project_name}.{ref} != {project_name}.{class_name}")
                #    return f"{project_name}.{class_name}"
                return f"{project_name}.{ref}"
            elif isinstance(schema_obj, list):
                if not class_name:
                    raise RuntimeError("Avro: Explicit class name reference (':{classname}' suffix) required for Avro schema with top-level union: ")
                for record in schema_obj:
                    if isinstance(record, dict) and "type" in record and record["type"] == "record":
                        ref = f"{record['namespace']}.{record['name']}" if "namespace" in record else record["name"]
                        if ref == class_name:
                            return f"{project_name}.{ref}"
            raise RuntimeError("Avro: Top-level record object not found in Avro schema: ")
        elif schema_format.startswith("proto"):
            if isinstance(schema_obj, str):
                if class_name:
                    local_class_name = JinjaFilters.strip_namespace(class_name)
                    match = re.search(r"message[\s]+([\w]+)[\s]*{", schema_obj)
                    if local_class_name and match:
                        for g in match.groups():
                            if g.lower() == local_class_name.lower():
                                return f"{project_name}.{class_name}"
                    if match and match.groups() and len(match.groups()) == 1:
                        class_name = JinjaFilters.namespace_dot(class_name) + match.groups()[0]
                        return f"{project_name}.{class_name}"
                    else:
                        raise RuntimeError(f"Proto: Top-level message {class_name} not found in Proto schema")
                else:
                    match = re.search(r"message[\s]+([\w]+)[\s]*{", schema_obj)
                    if match:
                        if len(match.groups()) > 1:
                            raise RuntimeError("Proto: Multiple top-level message objects found in Proto schema: ")
                        return f"{project_name}.{match.group(1)}"
                    else:
                        raise RuntimeError("Proto: Top-level message object not found in Proto schema: ")
            raise RuntimeError("Proto: Top-level message object not found in Proto schema: ")
        else:
            if class_name:
                return f"{project_name}.{class_name}"
            path_elements = schema_ref.split('/')
            if path_elements[-2] == "versions":
                return path_elements[-3]
            else:
                return path_elements[-1]

    @staticmethod
    def schema_object(root: Dict[str, Any], schema_url: str) -> Optional[Any]:
        """Return the object in the document that the schema URL points to."""
        logger.debug("Getting schema object from URL: %s", schema_url)
        try:
            obj = jsonpointer.resolve_pointer(root, schema_url[1:].split(":")[0])
        except jsonpointer.JsonPointerException:
            return None
        return obj

    @staticmethod
    def latest_dict_entry(dict_obj: Dict[str, Any]) -> Any:
        """Return the dictionary entry with the last key."""
        logger.debug("Getting the latest entry from dictionary")
        m = max([len(k) for k in dict_obj.keys()])
        return dict_obj[sorted([k.ljust(m) for k in dict_obj.keys()])[-1].strip()]

    @staticmethod
    def concat_namespace(namespace: str, class_name: str) -> str:
        """Concatenate a namespace and a class name."""
        logger.debug("Concatenating namespace: %s with class name: %s", namespace, class_name)
        if namespace:
            return f"{namespace}.{class_name}"
        return class_name
    
    @staticmethod
    def is_proto_doc(docroot: JsonNode) -> bool:
        """Check if the document is a proto document."""
        return isinstance(docroot, str) and re.search(r"syntax[\s]*=[\s]*\"proto3\"", docroot) is not None