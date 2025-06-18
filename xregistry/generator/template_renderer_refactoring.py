"""Simple refactoring patch for template_renderer.py to remove redundant reference resolution.

This module provides helper functions to replace the complex reference resolution 
logic in template_renderer.py with calls to the loader's composed document.
"""

import re
from typing import Any, Dict, List, Optional, Set, Union
import jsonpointer
from xregistry.cli import logger

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]


class TemplateRendererRefactoring:
    """Helper class to refactor template renderer logic."""

    def __init__(self, ctx, composed_document: JsonNode):
        """Initialize with context and composed document."""
        self.ctx = ctx
        self.composed_document = composed_document
        self.handled_resources: Set[str] = set()

    def mark_resource_handled(self, resource_ref: str) -> str:
        """Mark a resource as handled by templates."""
        self.handled_resources.add(resource_ref)
        return resource_ref

    def is_resource_handled(self, resource_ref: str) -> bool:
        """Check if resource is handled."""
        return resource_ref in self.handled_resources

    def collect_schema_references_from_document(self) -> Set[str]:
        """Collect all schema references from the composed document."""
        schema_refs = set()
        
        def scan_for_schemas(obj: JsonNode, path: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}/{key}" if path else key
                    
                    # Look for schema reference properties
                    if key in ["dataschema", "schema", "schemaurl"] and isinstance(value, str):
                        schema_refs.add(value)
                    
                    # Look for inline schemas
                    elif key == "schema" and isinstance(value, (dict, str)):
                        schema_pointer = f"#{path}/schema"
                        schema_refs.add(schema_pointer)
                    
                    # Recursively scan nested objects
                    scan_for_schemas(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    scan_for_schemas(item, f"{path}[{i}]")
        
        scan_for_schemas(self.composed_document)
        return schema_refs

    def get_unhandled_schema_references(self) -> Set[str]:
        """Get schema references that haven't been marked as handled."""
        all_schemas = self.collect_schema_references_from_document()
        return all_schemas - self.handled_resources

    def resolve_schema_reference_in_document(self, schema_ref: str) -> Optional[JsonNode]:
        """Resolve a schema reference in the composed document."""
        try:
            if schema_ref.startswith("#"):                # JSON pointer - resolve in composed document
                result = jsonpointer.resolve_pointer(self.composed_document, schema_ref[1:])
                return result  # type: ignore
            else:
                # For external references, they should already be resolved in the composed document
                # We can scan the document to find them
                return self._find_external_schema_in_document(schema_ref)
        except (jsonpointer.JsonPointerException, Exception) as e:
            logger.warning("Failed to resolve schema reference %s: %s", schema_ref, str(e))
            return None

    def _find_external_schema_in_document(self, schema_url: str) -> Optional[JsonNode]:
        """Find an external schema that was resolved into the composed document."""
        # This is a simplified approach - in practice, the loader should track 
        # the mapping of external URLs to their resolved locations
        logger.debug("Looking for external schema: %s", schema_url)
        return None

    def extract_schema_info_from_resolved_data(self, schema_ref: str, schema_data: JsonNode) -> Optional[Dict[str, Any]]:
        """Extract schema information from resolved schema data."""
        if not schema_data:
            return None

        # Handle string schemas (likely proto)
        if isinstance(schema_data, str):
            if self._is_proto_doc(schema_data):
                return {
                    "reference": schema_ref,
                    "content": schema_data,
                    "format": "proto3",
                    "format_short": "proto",
                    "class_name": self._extract_proto_class_name(schema_data, "")
                }
            return None

        # Handle dictionary schemas
        if isinstance(schema_data, dict):
            return self._extract_schema_info_from_dict(schema_ref, schema_data)

        return None

    def _extract_schema_info_from_dict(self, schema_ref: str, schema_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract schema info from a dictionary."""
        # Handle schema definitions with versions
        if "versions" in schema_dict and isinstance(schema_dict["versions"], dict):
            latest_version_id = schema_dict.get("defaultversionid")
            if not latest_version_id or latest_version_id not in schema_dict["versions"]:
                latest_version_id = max(schema_dict["versions"].keys())
            
            schema_version = schema_dict["versions"][latest_version_id]
            if isinstance(schema_version, dict):
                return self._extract_from_schema_version(schema_ref, schema_version, schema_dict)

        # Handle direct schema versions
        elif "versionid" in schema_dict or "format" in schema_dict or "dataschemaformat" in schema_dict:
            return self._extract_from_schema_version(schema_ref, schema_dict, schema_dict)

        return None

    def _extract_from_schema_version(self, schema_ref: str, schema_version: Dict[str, Any], 
                                   parent_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract info from a schema version."""
        # Get format
        schema_format = schema_version.get("dataschemaformat") or schema_version.get("format", "")
        if not schema_format:
            return None

        # Get content
        if "schema" in schema_version:
            content = schema_version["schema"]
        elif "schemaurl" in schema_version:
            # External schema - should be resolved in document already
            logger.warning("External schema URL in version, skipping: %s", schema_version["schemaurl"])
            return None
        else:
            return None

        # Extract names
        schema_id = schema_version.get("schemaid") or parent_schema.get("schemaid", "")
        class_name = schema_id

        # Extract group from reference path
        schema_group_id = ""
        if schema_ref.startswith("#"):
            path_parts = schema_ref.split("/")
            for i, part in enumerate(path_parts):
                if part == "schemagroups" and i + 1 < len(path_parts):
                    schema_group_id = path_parts[i + 1]
                    break

        # Build qualified class name
        if schema_group_id and class_name and not class_name.startswith(schema_group_id):
            class_name = f"{schema_group_id}.{class_name}"

        format_short = self._get_format_short(schema_format)

        return {
            "reference": schema_ref,
            "content": content,
            "format": schema_format,
            "format_short": format_short,
            "class_name": class_name,
            "schema_id": schema_id,
            "schema_group_id": schema_group_id
        }

    def _get_format_short(self, schema_format: str) -> str:
        """Get short format identifier."""
        format_lower = schema_format.lower()
        if format_lower.startswith("proto"):
            return "proto"
        elif format_lower.startswith("jsonschema"):
            return "json"
        elif format_lower.startswith("avro"):
            return "avro"
        return "unknown"

    def _is_proto_doc(self, content: str) -> bool:
        """Check if content is a proto document."""
        return re.search(r"syntax[\s]*=[\s]*\"proto3\"", content) is not None

    def _extract_proto_class_name(self, proto_content: str, class_hint: str) -> str:
        """Extract class name from proto content."""
        match = re.search(r"message[\s]+([\w]+)[\s]*{", proto_content)
        if match:
            return match.group(1)
        return class_hint or "Message"

    def should_use_avrotize(self, schema_info: Dict[str, Any], language: str) -> bool:
        """Check if schema should be processed with avrotize."""
        return (language in ["py", "cs", "java", "js", "ts"] and 
                schema_info["format_short"] != "proto")

    def convert_json_to_avro_if_needed(self, schema_info: Dict[str, Any]) -> None:
        """Convert JSON schema to Avro if needed."""
        if schema_info["format_short"] == "json":
            schema_info["content"] = self._convert_json_to_avro(
                schema_info["content"], schema_info["class_name"]
            )
            schema_info["format_short"] = "avro"

    def _convert_json_to_avro(self, json_schema: JsonNode, class_name: str) -> JsonNode:
        """Basic JSON to Avro conversion."""
        if isinstance(json_schema, dict):
            # Basic conversion
            avro_schema = {
                "type": "record",
                "name": class_name.split('.')[-1] if class_name else "Record",
                "namespace": '.'.join(class_name.split('.')[:-1]) if '.' in class_name else "",
                "fields": []
            }
            
            if "properties" in json_schema and isinstance(json_schema["properties"], dict):
                for prop_name, prop_def in json_schema["properties"].items():
                    field = {
                        "name": prop_name,
                        "type": self._convert_json_type_to_avro(prop_def)
                    }
                    avro_schema["fields"].append(field)
            
            return avro_schema
        
        return json_schema

    def _convert_json_type_to_avro(self, json_type_def: Any) -> Any:
        """Convert JSON type to Avro type."""
        if isinstance(json_type_def, dict):
            json_type = json_type_def.get("type", "string")
            type_map = {
                "string": "string",
                "number": "double", 
                "integer": "long",
                "boolean": "boolean"
            }
            return type_map.get(json_type, "string")
        return "string"
