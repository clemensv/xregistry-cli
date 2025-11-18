"""Schema-specific resource processor with avrotize integration."""

import json
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Set, Union

import jsonpointer
import avrotize

from xregistry.cli import logger
from xregistry.generator.jinja_filters import JinjaFilters

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]


class SchemaProcessor(ResourceProcessor):
    """Specialized processor for schema resources with avrotize integration."""

    def __init__(self, ctx: GeneratorContext):
        """Initialize the schema processor."""
        super().__init__(ctx)
        self.avrotize_queue: List[Dict[str, Any]] = []

    def collect_schema_references(self, document: JsonNode) -> Set[str]:
        """Collect all schema references from a document.
        
        Args:
            document: The xRegistry document to scan
            
        Returns:
            Set of schema reference strings
        """
        schema_refs = set()
        
        def scan_object(obj: JsonNode, current_path: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{current_path}/{key}" if current_path else key
                    
                    # Look for schema reference properties
                    if key in ["dataschema", "schema", "schemaurl"] and isinstance(value, str):
                        schema_refs.add(value)
                    
                    # Recursively scan nested objects
                    scan_object(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    scan_object(item, f"{current_path}[{i}]")
        
        scan_object(document)
        return schema_refs

    def process_schema_reference(self, schema_ref: str, root_document: JsonNode, 
                                project_name: str, language: str) -> Optional[Dict[str, Any]]:
        """Process a single schema reference and extract its information.
        
        Args:
            schema_ref: The schema reference to process
            root_document: The root document for resolution
            project_name: Project name for type naming
            language: Target language for code generation
            
        Returns:
            Dictionary with schema information or None if processing failed
        """
        logger.debug("Processing schema reference: %s", schema_ref)
        
        # Parse class name suffix if present
        class_name = ''
        if ":" in schema_ref:
            schema_ref, class_name = schema_ref.split(":", 1)

        # Resolve the schema reference to actual data
        schema_data = self.resolve_resource_reference(schema_ref, root_document)
        if not schema_data:
            logger.warning("Could not resolve schema reference: %s", schema_ref)
            return None

        # Extract schema format and actual schema content
        schema_format, schema_content = self._extract_schema_format_and_content(
            schema_data, schema_ref, root_document
        )
        
        if not schema_format or not schema_content:
            logger.warning("Could not extract schema format or content for: %s", schema_ref)
            return None

        # Extract schema ID and group information
        schema_id, schema_group_id = SchemaTypeExtractor.extract_schema_id_and_group(
            schema_ref, schema_data
        )
        
        # Build qualified class name
        qualified_class_name = self._build_qualified_class_name(
            class_name, schema_id, schema_group_id, schema_ref, root_document
        )

        # Determine processing method based on language and format
        schema_format_short = self._get_schema_format_short(schema_format)
        
        return {
            "schema_reference": schema_ref,
            "schema_content": schema_content,
            "schema_format": schema_format,
            "schema_format_short": schema_format_short,
            "class_name": qualified_class_name,
            "schema_id": schema_id,
            "schema_group_id": schema_group_id,
            "requires_avrotize": self._requires_avrotize(language, schema_format_short)
        }

    def queue_for_avrotize(self, schema_info: Dict[str, Any]) -> None:
        """Queue a schema for avrotize processing.
        
        Args:
            schema_info: Schema information dictionary
        """
        if schema_info.get("requires_avrotize", False):
            self.avrotize_queue.append(schema_info)

    def process_avrotize_queue(self, project_data_dir: str, data_project_name: str, 
                              template_args: Dict[str, Any]) -> None:
        """Process all schemas in the avrotize queue.
        
        Args:
            project_data_dir: Directory for generated data classes
            data_project_name: Name of the data project
            template_args: Template arguments with encoding preferences
        """
        if not self.avrotize_queue:
            return

        logger.debug("Processing avrotize queue with %d schemas", len(self.avrotize_queue))
        
        # Determine encoding options
        avro_enabled = (template_args.get("avro-encoding", "false") == "true" or 
                       any("avro" in s.get("schema_format_short", "") for s in self.avrotize_queue))
        json_enabled = template_args.get("json-encoding", "true") == "true"

        # Merge all schemas
        merged_schema = []
        for schema_info in self.avrotize_queue:
            schema_content = schema_info["schema_content"]
            if isinstance(schema_content, list):
                merged_schema.extend(schema_content)
            else:
                merged_schema.append(schema_content)

        if len(merged_schema) == 1:
            merged_schema = merged_schema[0]

        # Generate code based on language
        language = self.ctx.language
        if language == "py":
            avrotize.convert_avro_schema_to_python(
                merged_schema, project_data_dir, package_name=data_project_name,
                dataclasses_json_annotation=json_enabled, avro_annotation=avro_enabled
            )
        elif language == "cs":
            avrotize.convert_avro_schema_to_csharp(
                merged_schema, project_data_dir, base_namespace=JinjaFilters.pascal(data_project_name),
                pascal_properties=True, system_text_json_annotation=json_enabled, avro_annotation=avro_enabled
            )
        elif language == "java":
            avrotize.convert_avro_schema_to_java(
                merged_schema, project_data_dir, package_name=data_project_name,
                jackson_annotation=json_enabled, avro_annotation=avro_enabled
            )
        elif language == "js":
            avrotize.convert_avro_schema_to_javascript(
                merged_schema, project_data_dir, package_name=data_project_name, 
                avro_annotation=avro_enabled
            )
        elif language == "ts":
            avrotize.convert_avro_schema_to_typescript(
                merged_schema, project_data_dir, package_name=data_project_name,
                avro_annotation=avro_enabled, typedjson_annotation=json_enabled
            )
        elif language == "go":
            avrotize.convert_avro_schema_to_go(
                merged_schema, project_data_dir, package_name=data_project_name,
                avro_annotation=avro_enabled, json_annotation=json_enabled
            )

        # Clear the queue after processing
        self.avrotize_queue.clear()

    def _extract_schema_format_and_content(self, schema_data: JsonNode, schema_ref: str, 
                                          root_document: JsonNode) -> tuple[str, JsonNode]:
        """Extract schema format and content from schema data."""
        if isinstance(schema_data, str) and SchemaTypeExtractor.is_proto_doc(schema_data):
            return "proto3", schema_data

        if not isinstance(schema_data, dict):
            return "", None        # Check if this is a schema definition with versions
        if "versions" in schema_data and isinstance(schema_data["versions"], dict):
            # Get the latest version
            latest_version_id = schema_data.get("defaultversionid")
            if not latest_version_id or latest_version_id not in schema_data["versions"]:
                latest_version_id = max(schema_data["versions"].keys())
            
            schema_version = schema_data["versions"][latest_version_id]
            if isinstance(schema_version, dict):
                return self._extract_format_and_content_from_version(schema_version, schema_ref)

        # Check if this is a schema version
        elif "versionid" in schema_data or "format" in schema_data or "dataschemaformat" in schema_data:
            return self._extract_format_and_content_from_version(schema_data, schema_ref)

        return "", None

    def _extract_format_and_content_from_version(self, schema_version: Dict[str, Any], 
                                                schema_ref: str) -> tuple[str, JsonNode]:
        """Extract format and content from a schema version."""
        # Get format
        schema_format = schema_version.get("dataschemaformat") or schema_version.get("format", "")
        
        # Get content
        if "schemaurl" in schema_version:
            # External schema - load it
            schema_url = schema_version["schemaurl"]
            _, external_schema = self.ctx.loader.load(schema_url, {})
            return schema_format, external_schema
        elif "schema" in schema_version:
            return schema_format, schema_version["schema"]
        
        return schema_format, None

    def _build_qualified_class_name(self, class_name: str, schema_id: str, schema_group_id: str,
                                   schema_ref: str, root_document: JsonNode) -> str:
        """Build a qualified class name for the schema."""
        if not class_name:
            class_name = schema_id

        if not class_name:
            # Extract from reference path
            if schema_ref.startswith("#"):
                path_parts = schema_ref.split("/")
                if len(path_parts) > 1:
                    class_name = path_parts[-1]

        # Add group prefix if needed
        if schema_group_id and class_name and not class_name.startswith(schema_group_id):
            class_name = f"{schema_group_id}.{class_name}"

        return class_name or "Unknown"

    def _get_schema_format_short(self, schema_format: str) -> str:
        """Get short format identifier."""
        format_lower = schema_format.lower()
        if format_lower.startswith("proto"):
            return "proto"
        elif format_lower.startswith("jsonschema"):
            return "json"
        elif format_lower.startswith("avro"):
            return "avro"
        return "unknown"

    def _requires_avrotize(self, language: str, schema_format_short: str) -> bool:
        """Check if schema requires avrotize processing."""
        return language in ["py", "cs", "java", "js", "ts", "go"]

    def convert_jsons_to_avro(self, schema_reference: str, schema_root: JsonNode,
                             namespace_name: str, class_name: str) -> JsonNode:
        """Convert JSON Schema to Avro format.
        
        Args:
            schema_reference: Reference to the schema
            schema_root: The JSON schema content
            namespace_name: Namespace for the Avro schema
            class_name: Class name for the Avro record
            
        Returns:
            Converted Avro schema
        """
        logger.debug("Converting JSON Schema to Avro for: %s", schema_reference)
        
        if isinstance(schema_root, dict):
            # Basic JSON Schema to Avro conversion
            avro_schema = {
                "type": "record",
                "name": class_name,
                "namespace": namespace_name,
                "fields": []
            }
              # Convert properties to fields
            if "properties" in schema_root and isinstance(schema_root["properties"], dict):
                for prop_name, prop_def in schema_root["properties"].items():
                    field = {
                        "name": prop_name,
                        "type": self._convert_json_type_to_avro(prop_def)
                    }
                    avro_schema["fields"].append(field)
            
            return avro_schema
        
        return schema_root

    def _convert_json_type_to_avro(self, json_type_def: Any) -> Any:
        """Convert JSON Schema type definition to Avro type."""
        if isinstance(json_type_def, dict):
            json_type = json_type_def.get("type", "string")
            if json_type == "string":
                return "string"
            elif json_type == "number":
                return "double"
            elif json_type == "integer":
                return "long"
            elif json_type == "boolean":
                return "boolean"
            elif json_type == "array":
                item_type = self._convert_json_type_to_avro(json_type_def.get("items", {"type": "string"}))
                return {"type": "array", "items": item_type}
            elif json_type == "object":
                return "string"  # Simplified - could be more complex
        
        return "string"  # Default fallback
