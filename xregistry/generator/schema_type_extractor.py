"""Refactored schema utilities focused on type and name extraction."""

import re
from typing import Any, Dict, List, Optional, Union

from xregistry.cli import logger
from xregistry.generator.jinja_filters import JinjaFilters

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]


class SchemaTypeExtractor:
    """Utility class for extracting schema type information without reference resolution."""

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
    def extract_schema_type_name(schema_obj: JsonNode, class_name: str = '', 
                                 project_name: str = '', schema_format: str = "jsonschema") -> str:
        """Extract type name from a resolved schema object.
        
        Args:
            schema_obj: The resolved schema object
            class_name: Optional explicit class name
            project_name: Project name to prefix the type
            schema_format: Format of the schema (avro, proto, jsonschema)
            
        Returns:
            Fully qualified type name
        """
        logger.debug("Extracting schema type name from resolved object")
        
        format_lower = schema_format.lower()
        
        if format_lower.startswith("avro"):
            return SchemaTypeExtractor._extract_avro_type_name(
                schema_obj, class_name, project_name
            )
        elif format_lower.startswith("proto"):
            return SchemaTypeExtractor._extract_proto_type_name(
                schema_obj, class_name, project_name
            )
        else:
            # JSON Schema or other formats
            return SchemaTypeExtractor._extract_generic_type_name(
                schema_obj, class_name, project_name
            )

    @staticmethod
    def _extract_avro_type_name(schema_obj: JsonNode, class_name: str, project_name: str) -> str:
        """Extract type name from Avro schema."""
        if isinstance(schema_obj, dict) and "type" in schema_obj and schema_obj["type"] == "record":
            ref = str(f"{schema_obj['namespace']}.{schema_obj['name']}" if "namespace" in schema_obj else schema_obj["name"])
            return f"{project_name}.{ref}"
        elif isinstance(schema_obj, list):
            if not class_name:
                raise RuntimeError("Avro: Explicit class name reference (':{classname}' suffix) required for Avro schema with top-level union")
            for record in schema_obj:
                if isinstance(record, dict) and "type" in record and record["type"] == "record":
                    ref = f"{record['namespace']}.{record['name']}" if "namespace" in record else record["name"]
                    if ref == class_name:
                        return f"{project_name}.{ref}"
        raise RuntimeError("Avro: Top-level record object not found in Avro schema")

    @staticmethod
    def _extract_proto_type_name(schema_obj: JsonNode, class_name: str, project_name: str) -> str:
        """Extract type name from Protocol Buffers schema."""
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
                        raise RuntimeError("Proto: Multiple top-level message objects found in Proto schema")
                    return f"{project_name}.{match.group(1)}"
                else:
                    raise RuntimeError("Proto: Top-level message object not found in Proto schema")
        raise RuntimeError("Proto: Top-level message object not found in Proto schema")

    @staticmethod
    def _extract_generic_type_name(schema_obj: JsonNode, class_name: str, project_name: str) -> str:
        """Extract type name for generic schemas (JSON Schema, etc.)."""
        if class_name:
            return f"{project_name}.{class_name}"
        # For generic schemas, we can't easily extract a meaningful name from the schema object
        # So we rely on the caller to provide a class_name
        return f"{project_name}.UnknownType"

    @staticmethod
    def extract_schema_id_and_group(schema_reference: str, schema_data: JsonNode) -> tuple[str, str]:
        """Extract schema ID and group from schema data.
        
        Args:
            schema_reference: The reference to the schema
            schema_data: The schema data
            
        Returns:
            Tuple of (schema_id, schema_group_id)
        """
        schema_id = ""
        schema_group_id = ""
        
        if isinstance(schema_data, dict):
            # Direct schema ID
            if "schemaid" in schema_data:
                schema_id = str(schema_data["schemaid"])
            
            # Try to extract group from parent reference or URL patterns
            if schema_reference.startswith("#"):
                # JSON pointer - extract from path
                path_parts = schema_reference.split("/")
                if len(path_parts) >= 3:
                    # Pattern: #/schemagroups/{groupid}/schemas/{schemaid}
                    for i, part in enumerate(path_parts):
                        if part == "schemagroups" and i + 1 < len(path_parts):
                            schema_group_id = path_parts[i + 1]
                            break
            elif "defaultversionurl" in schema_data or "self" in schema_data:
                # Extract group from version URL
                version_url = str(schema_data.get("defaultversionurl", schema_data.get("self", "")))
                match = re.search(r"/schemagroups/([^/]+)/", version_url)
                if match:
                    schema_group_id = match.group(1)
        
        return schema_id, schema_group_id

    @staticmethod
    def is_proto_doc(doc_root: JsonNode) -> bool:
        """Check if the document is a proto document."""
        return isinstance(doc_root, str) and re.search(r"syntax[\s]*=[\s]*\"proto3\"", doc_root) is not None

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
