"""Resource processor for managing handled resources during code generation."""

import re
import urllib.parse
from typing import Any, Dict, List, Optional, Set, Union

import jsonpointer

from xregistry.cli import logger
from xregistry.generator.generator_context import GeneratorContext

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]


class ResourceProcessor:
    """Handles marking and processing of resources during code generation."""

    def __init__(self, ctx: GeneratorContext):
        """Initialize the resource processor.
        
        Args:
            ctx: The generator context containing the loader and other state
        """
        self.ctx = ctx
        self.handled_resources: Set[str] = set()
        self.queued_resources: Dict[str, Dict[str, Any]] = {}

    def mark_handled(self, resource_reference: str) -> None:
        """Mark a resource as handled by templates.
        
        Args:
            resource_reference: Reference to the resource (e.g., JSON pointer, URL)
        """
        logger.debug("Marking resource as handled: %s", resource_reference)
        self.handled_resources.add(resource_reference)

    def is_handled(self, resource_reference: str) -> bool:
        """Check if a resource has been marked as handled.
        
        Args:
            resource_reference: Reference to the resource
            
        Returns:
            True if the resource has been marked as handled
        """
        return resource_reference in self.handled_resources

    def queue_resource(self, resource_reference: str, resource_data: Dict[str, Any]) -> None:
        """Queue a resource for later processing.
        
        Args:
            resource_reference: Reference to the resource
            resource_data: Data associated with the resource
        """
        logger.debug("Queueing resource: %s", resource_reference)
        self.queued_resources[resource_reference] = resource_data

    def get_queued_resources(self) -> Dict[str, Dict[str, Any]]:
        """Get all queued resources.
        
        Returns:
            Dictionary of resource references to their data
        """
        return self.queued_resources.copy()

    def clear_queued_resources(self) -> None:
        """Clear all queued resources."""
        self.queued_resources.clear()

    def get_unhandled_resources(self, all_resources: Set[str]) -> Set[str]:
        """Get resources that haven't been marked as handled.
        
        Args:
            all_resources: Set of all available resources
            
        Returns:
            Set of unhandled resource references
        """
        return all_resources - self.handled_resources

    def extract_type_and_name(self, resource_reference: str, resource_data: JsonNode) -> tuple[str, str]:
        """Extract type and name information from a resource.
        
        Args:
            resource_reference: Reference to the resource
            resource_data: The resource data
            
        Returns:
            Tuple of (resource_type, resource_name)
        """
        # Default implementation - can be overridden for specific resource types
        resource_type = "unknown"
        resource_name = ""

        if isinstance(resource_data, dict):
            # Check for common xRegistry resource types
            if "schemaid" in resource_data:
                resource_type = "schema"
                resource_name = str(resource_data["schemaid"])
            elif "messageid" in resource_data:
                resource_type = "message"
                resource_name = str(resource_data["messageid"])
            elif "endpointid" in resource_data:
                resource_type = "endpoint"
                resource_name = str(resource_data["endpointid"])
            elif "schemagroupid" in resource_data:
                resource_type = "schemagroup"
                resource_name = str(resource_data["schemagroupid"])
            elif "messagegroupid" in resource_data:
                resource_type = "messagegroup"
                resource_name = str(resource_data["messagegroupid"])
            elif "endpointgroupid" in resource_data:
                resource_type = "endpointgroup"
                resource_name = str(resource_data["endpointgroupid"])

        # Fall back to extracting from reference if no ID found
        if not resource_name and isinstance(resource_reference, str):
            if resource_reference.startswith("#"):
                # JSON pointer reference
                path_parts = resource_reference.split("/")
                if len(path_parts) > 1:
                    resource_name = path_parts[-1]
                    if len(path_parts) > 2:
                        resource_type = path_parts[-2].rstrip("s")  # Remove plural 's'
            else:
                # URL reference
                url_parts = resource_reference.split("/")
                if len(url_parts) > 1:
                    resource_name = url_parts[-1]

        return resource_type, resource_name

    def resolve_resource_reference(self, reference: str, root_document: JsonNode) -> Optional[JsonNode]:
        """Resolve a resource reference to its actual data.
        
        Args:
            reference: The resource reference (JSON pointer or URL)
            root_document: The root document for JSON pointer resolution
            
        Returns:
            The resolved resource data, or None if not found
        """
        try:
            if reference.startswith("#"):
                # xRegistry fragment reference - convert to JSON pointer format
                pointer = reference[1:]  # Remove #
                if not pointer.startswith('/'):
                    pointer = '/' + pointer  # Add leading / for JSON Pointer
                result = jsonpointer.resolve_pointer(root_document, pointer)
                return result  # type: ignore
            else:
                # External URL - use the loader
                _, resource_data = self.ctx.loader.load(
                    reference, {},
                    messagegroup_filter=self.ctx.messagegroup_filter,
                    endpoint_filter=self.ctx.endpoint_filter
                )
                return resource_data
        except (jsonpointer.JsonPointerException, Exception) as e:
            logger.warning("Failed to resolve resource reference %s: %s", reference, str(e))
            return None
