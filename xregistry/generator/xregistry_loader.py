""" Core functions for the xregistry commands with dependency resolution """

import json
import os
from typing import Any, Dict, List, Tuple, Union, Set, Optional
import urllib.request
import urllib.parse
import urllib.error
import logging
import yaml
import base64
from ..common.model import Model

JsonNode = Union[Dict[str, 'JsonNode'], List['JsonNode'], str, bool, int, float, None]

logger = logging.getLogger(__name__)


class XRegistryUrlParser:
    """Parse xRegistry URLs to determine entry point and resource paths."""
    
    def __init__(self, url: str):
        self.url = url
        self.parsed = urllib.parse.urlparse(url)
        self.base_url = f"{self.parsed.scheme}://{self.parsed.netloc}"
        self.path_parts = [p for p in self.parsed.path.strip('/').split('/') if p]
        
        # Track if this is a registry-level URL
        self.is_registry_root = False
        
        # File paths (no scheme) default to registry level
        if not self.parsed.scheme or not self.parsed.netloc:
            self.is_registry_root = True
            # Keep path_parts for potential file path handling, but mark as registry
        # If URL starts with /registry, strip it and mark as registry root if that's all there is
        elif self.path_parts and self.path_parts[0] == 'registry':
            if len(self.path_parts) == 1:
                # Just /registry - this is the registry root
                self.is_registry_root = True
                self.path_parts = []
            else:
                # /registry/something - strip registry prefix
                self.path_parts = self.path_parts[1:]
        
    def get_base_url(self) -> str:
        """Get the base registry URL."""
        return self.base_url
    
    def get_entry_type(self) -> str:
        """Determine the type of entry point."""
        # Check for registry root first
        if self.is_registry_root or not self.path_parts:
            return "registry"
        elif len(self.path_parts) == 1:
            return "group_type"
        elif len(self.path_parts) == 2:
            return "group_instance"
        elif len(self.path_parts) == 3:
            return "resource_collection"
        elif len(self.path_parts) == 4:
            return "resource"
        elif len(self.path_parts) == 5:
            return "version_collection"
        elif len(self.path_parts) == 6:
            return "version"
        else:
            return "unknown"
    
    def get_group_type(self) -> Optional[str]:
        """Get the group type (e.g., 'messagegroups', 'schemagroups')."""
        return self.path_parts[0] if self.path_parts and not self.is_registry_root else None
    
    def get_group_id(self) -> Optional[str]:
        """Get the group instance ID."""
        return self.path_parts[1] if len(self.path_parts) > 1 else None
    
    def get_resource_id(self) -> Optional[str]:
        """Get the resource ID."""
        return self.path_parts[3] if len(self.path_parts) > 3 else None
    
    def get_version_id(self) -> Optional[str]:
        """Get the version ID."""
        return self.path_parts[5] if len(self.path_parts) > 5 else None


class DependencyResolver:
    """Resolves xRegistry dependencies by following xid references."""
    
    def __init__(self, model: Model, loader: 'XRegistryLoader'):
        self.model = model
        self.loader = loader
        self.resolved_resources: Dict[str, JsonNode] = {}
        self.pending_resolution: Set[str] = set()
        self.logger = logging.getLogger(__name__ + ".DependencyResolver")
    
    def find_xid_references(self, data: JsonNode, group_type: str) -> List[str]:
        """Find all external xid references in the given data structure."""
        references = []
        
        # Get group types dynamically from model
        model_groups = self.model.groups
        group_patterns = [f"/{group_key}/" for group_key in model_groups.keys()]
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Check for URI-like references that might point to external xRegistry resources
                if isinstance(value, str) and (key.endswith("uri") or key.endswith("url") or "ref" in key.lower()):
                    # Only include external URLs, not fragment references starting with #
                    if not value.startswith("#") and any(pattern in value for pattern in group_patterns):
                        references.append(value)
                
                # Recursively check nested structures
                nested_refs = self.find_xid_references(value, group_type)
                references.extend(nested_refs)
                
        elif isinstance(data, list):
            for item in data:
                # Check if list item is a string that looks like an xRegistry URL
                if isinstance(item, str):
                    # Only include external URLs, not fragment references starting with #
                    if not item.startswith("#") and any(pattern in item for pattern in group_patterns):
                        references.append(item)
                else:
                    # Recursively check nested structures
                    nested_refs = self.find_xid_references(item, group_type)
                    references.extend(nested_refs)
        
        return references
    
    def _mark_inline_resources_as_resolved(self, doc: Dict[str, Any], base_url: str) -> None:
        """Mark all inline resources in the document as already resolved to prevent re-fetching.
        
        When using ?inline=*, the API returns nested resources (messages, schemas, versions, etc.)
        already embedded in the response. We need to mark these as resolved so we don't try to
        fetch them again from their 'self' URLs.
        """
        if not isinstance(doc, dict):
            return
        
        # Extract the registry root from base_url for constructing absolute URLs
        registry_root = None
        if base_url.startswith("http"):
            parsed = urllib.parse.urlparse(base_url)
            registry_root = f"{parsed.scheme}://{parsed.netloc}"
        
        # Process each group type in the document
        model_groups = self.model.groups
        for group_type, group_def in model_groups.items():
            if group_type not in doc or not isinstance(doc[group_type], dict):
                continue
                
            group_collection = doc[group_type]
            group_resources = group_def.get("resources", {})
            
            for group_id, group in group_collection.items():
                if not isinstance(group, dict):
                    continue
                
                # Mark the group instance itself as resolved
                if "self" in group and isinstance(group["self"], str):
                    self.resolved_resources[group["self"]] = group
                if "xid" in group and isinstance(group["xid"], str) and registry_root:
                    full_url = urllib.parse.urljoin(registry_root, group["xid"])
                    self.resolved_resources[full_url] = group
                
                # Process each resource collection type (messages, schemas, etc.)
                for resource_collection in group_resources.keys():
                    if resource_collection not in group or not isinstance(group[resource_collection], dict):
                        continue
                    
                    resources = group[resource_collection]
                    for resource_id, resource in resources.items():
                        if not isinstance(resource, dict):
                            continue
                        
                        # Mark the resource itself as resolved
                        if "self" in resource and isinstance(resource["self"], str):
                            self.resolved_resources[resource["self"]] = resource
                        if "xid" in resource and isinstance(resource["xid"], str) and registry_root:
                            full_url = urllib.parse.urljoin(registry_root, resource["xid"])
                            self.resolved_resources[full_url] = resource
                        
                        # If the resource has versions, mark each version as resolved
                        if "versions" in resource and isinstance(resource["versions"], dict):
                            for version_id, version in resource["versions"].items():
                                if not isinstance(version, dict):
                                    continue
                                    
                                if "self" in version and isinstance(version["self"], str):
                                    self.resolved_resources[version["self"]] = version
                                if "xid" in version and isinstance(version["xid"], str) and registry_root:
                                    full_url = urllib.parse.urljoin(registry_root, version["xid"])
                                    self.resolved_resources[full_url] = version
    
    def resolve_reference(self, ref_url: str, headers: Dict[str, str], base_url: Optional[str] = None) -> Optional[JsonNode]:
        """Resolve a single xid reference.
        
        Args:
            ref_url: The reference URL to resolve (can be relative or absolute)
            headers: HTTP headers for authentication
            base_url: Base URL for resolving relative references
            
        Returns:
            The resolved resource data, or None if resolution fails
        """
        # Resolve relative references against base URL
        if base_url and ref_url.startswith("/"):
            ref_url = urllib.parse.urljoin(base_url, ref_url)
            self.logger.debug(f"Resolved relative reference to: {ref_url}")
        
        if ref_url in self.resolved_resources:
            return self.resolved_resources[ref_url]
        
        if ref_url in self.pending_resolution:
            self.logger.warning(f"Circular dependency detected for {ref_url}")
            return None
        
        self.pending_resolution.add(ref_url)
        
        try:
            self.logger.debug(f"Resolving reference: {ref_url}")
            _, resource_data = self.loader._load_core(ref_url, headers, ignore_handled=True)
            
            if resource_data is not None:
                self.resolved_resources[ref_url] = resource_data
                
                # Find and resolve nested dependencies
                parser = XRegistryUrlParser(ref_url)
                group_type = parser.get_group_type() or "unknown"
                nested_refs = self.find_xid_references(resource_data, group_type)
                
                # Extract base URL from ref_url for resolving nested relative references
                nested_base_url = None
                if ref_url.startswith("http"):
                    parsed = urllib.parse.urlparse(ref_url)
                    nested_base_url = f"{parsed.scheme}://{parsed.netloc}"
                
                for nested_ref in nested_refs:
                    self.resolve_reference(nested_ref, headers, nested_base_url)
                
                return resource_data
            
        except Exception as e:
            self.logger.error(f"Failed to resolve reference {ref_url}: {e}")
        
        finally:
            self.pending_resolution.discard(ref_url)        
        return None
    
    def _normalize_schema_references(self, doc: Dict[str, Any]) -> None:
        """Convert relative URI schema references to JSON pointers.
        
        After loading all dependencies, messages may reference schemas using relative URIs
        like '/schemagroups/Contoso.ERP/schemas/SchemaName'. These should be normalized
        to JSON pointers like '#/schemagroups/Contoso.ERP/schemas/SchemaName' so they can
        be resolved within the composed document.
        """
        if not isinstance(doc, dict):
            return
        
        # Process all message groups
        if "messagegroups" in doc and isinstance(doc["messagegroups"], dict):
            for mg_id, mg in doc["messagegroups"].items():
                if not isinstance(mg, dict) or "messages" not in mg:
                    continue
                    
                if not isinstance(mg["messages"], dict):
                    continue
                    
                for msg_id, msg in mg["messages"].items():
                    if not isinstance(msg, dict):
                        continue
                    
                    # Normalize dataschemauri if present
                    if "dataschemauri" in msg:
                        schema_uri = msg["dataschemauri"]
                        if isinstance(schema_uri, str) and schema_uri.startswith("/"):
                            # Convert relative URI to JSON pointer
                            msg["dataschemauri"] = "#" + schema_uri
        
        # Process all endpoints (they may also reference schemas or messages)
        if "endpoints" in doc and isinstance(doc["endpoints"], dict):
            for ep_id, ep in doc["endpoints"].items():
                if not isinstance(ep, dict):
                    continue
                
                # Normalize message references in endpoint configurations
                # This is a placeholder for endpoint-specific normalization if needed
                pass
    
    def _restructure_single_resource(self, version_obj: Dict[str, Any], group_type: str, resource_id: str) -> Dict[str, Any]:
        """Restructure a single message/schema version object into proper group structure.
        
        When fetching a single message like /messagegroups/X/messages/Y, the API returns
        a message version object with inline versions. We need to restructure this into:
        - A proper group object with just this one message
        - The message as a resource within the group's messages collection
        
        Args:
            version_obj: The version object returned by the API
            group_type: The group type (messagegroups, schemagroups, etc.)
            resource_id: The resource ID (message name, schema name, etc.)
            
        Returns:
            Properly structured group object
        """
        # Create the group structure
        group_obj: Dict[str, Any] = {}
        
        # Determine resource collection name
        if group_type == "messagegroups":
            resource_collection = "messages"
            id_field = "messageid"
        elif group_type == "schemagroups":
            resource_collection = "schemas"
            id_field = "schemaid"
        elif group_type == "endpoints":
            resource_collection = "endpoints"
            id_field = "endpointid"
        else:
            # Unknown group type, return as-is
            return {resource_collection: {resource_id: version_obj}}
        
        # Create message/schema resource from the version object
        # Extract metadata that belongs at the message level
        resource_obj: Dict[str, Any] = {
            id_field: version_obj.get(id_field, resource_id)
        }
        
        # Copy message-level fields
        message_level_fields = [
            'description', 'envelope', 'envelopemetadata',
            'dataschema', 'dataschemauri', 'dataschemaformat',
            'format', 'schemaformat', 'schemaurl'
        ]
        
        for field in message_level_fields:
            if field in version_obj:
                resource_obj[field] = version_obj[field]
        
        # If there are versions, keep them
        if 'versions' in version_obj and isinstance(version_obj['versions'], dict):
            resource_obj['versions'] = version_obj['versions']
        
        # Add resource URLs if present
        if 'self' in version_obj:
            # Convert version URL to resource URL by removing /versions/X
            resource_url = version_obj['self'].rsplit('/versions/', 1)[0] if '/versions/' in version_obj['self'] else version_obj['self']
            resource_obj['self'] = resource_url
        
        if 'xid' in version_obj:
            resource_xid = version_obj['xid'].rsplit('/versions/', 1)[0] if '/versions/' in version_obj['xid'] else version_obj['xid']
            resource_obj['xid'] = resource_xid
        
        # Create the group with the resource collection
        group_obj[resource_collection] = {resource_id: resource_obj}
        
        return group_obj

    def build_composed_document(self, entry_url: str, entry_data: JsonNode, headers: Dict[str, str], registry_root: Optional[str] = None) -> JsonNode:
        """Build a composed xRegistry document with all dependencies.
        
        Args:
            entry_url: The URL of the entry point
            entry_data: The loaded entry data
            headers: HTTP headers for authentication
            registry_root: The discovered registry root URL for resolving relative references
            
        Returns:
            Composed document with all dependencies
        """
        parser = XRegistryUrlParser(entry_url)
        entry_type = parser.get_entry_type()
        
        # Start with empty document structure
        composed_doc: Dict[str, Any] = {}
          # Override entry_type detection based on document content
        if isinstance(entry_data, dict):
            # If the document contains top-level xRegistry collections, treat it as a full registry
            model_groups = self.model.groups
            xreg_collections = set(model_groups.keys())
            if any(key in entry_data for key in xreg_collections):
                entry_type = "registry"
        
        # Add the entry data based on its type
        if entry_type == "registry":
            # Full registry - use as-is but filter dependencies
            if isinstance(entry_data, dict):
                composed_doc = dict(entry_data)
                # Mark all inline resources as already resolved to prevent re-fetching
                self._mark_inline_resources_as_resolved(composed_doc, entry_url)
        
        elif entry_type == "group_type":
            # Group type collection
            group_type = parser.get_group_type()
            if group_type and isinstance(entry_data, dict):
                composed_doc[group_type] = entry_data
                # Mark all inline resources as already resolved
                self._mark_inline_resources_as_resolved(composed_doc, entry_url)
        
        elif entry_type in ["group_instance", "resource_collection", "resource", "version"]:
            # Specific group, resource, or version
            group_type = parser.get_group_type()
            group_id = parser.get_group_id()
            resource_id = parser.get_resource_id()
            
            if group_type and group_id:
                # Special handling for single message/schema resource
                # The API returns a version object with inline versions, but we need proper structure
                if entry_type == "resource" and resource_id and isinstance(entry_data, dict):
                    if 'messageid' in entry_data or 'schemaid' in entry_data:
                        # This is a message/schema version object, needs restructuring
                        entry_data = self._restructure_single_resource(entry_data, group_type, resource_id)
                
                composed_doc[group_type] = {group_id: entry_data}
                # Mark all inline resources (like messages fetched with ?inline=*) as already resolved
                self._mark_inline_resources_as_resolved(composed_doc, entry_url)
        
        # Find and resolve all dependencies
        group_type = parser.get_group_type() or "unknown"
        all_refs = self.find_xid_references(composed_doc, group_type)
        
        # Use the provided registry_root for resolving relative references
        # If not provided, fall back to extracting from entry_url
        base_url = registry_root
        if not base_url and entry_url.startswith("http"):
            parsed = urllib.parse.urlparse(entry_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        for ref_url in all_refs:
            resolved_resource = self.resolve_reference(ref_url, headers, base_url)
            if resolved_resource is not None:
                # Add resolved resource to composed document
                self._add_resource_to_document(composed_doc, ref_url, resolved_resource)
        
        # Normalize schema references from relative URIs to JSON pointers
        self._normalize_schema_references(composed_doc)
        
        return composed_doc
    
    def _add_resource_to_document(self, doc: Dict[str, Any], resource_url: str, resource_data: JsonNode) -> None:
        """Add a resolved resource to the composed document."""
        parser = XRegistryUrlParser(resource_url)
        group_type = parser.get_group_type()
        group_id = parser.get_group_id()
        resource_id = parser.get_resource_id()
        version_id = parser.get_version_id()
        
        if not group_type or not isinstance(resource_data, dict):
            return
        
        # Ensure group type exists in document
        if group_type not in doc:
            doc[group_type] = {}
        
        if not isinstance(doc[group_type], dict):
            doc[group_type] = {}
        
        if group_id:
            # Ensure group instance exists
            if group_id not in doc[group_type]:
                doc[group_type][group_id] = {}
            
            if resource_id:
                # Determine the resource collection name from the URL path
                # URL format: /grouptype/groupid/resourcecollection/resourceid
                url_parts = [p for p in urllib.parse.urlparse(resource_url).path.split('/') if p]
                resource_collection = url_parts[2] if len(url_parts) > 2 else None
                
                if not resource_collection:
                    self.logger.warning(f"Could not determine resource collection from URL: {resource_url}")
                    return
                
                if not isinstance(doc[group_type][group_id], dict):
                    doc[group_type][group_id] = {}
                
                if resource_collection not in doc[group_type][group_id]:
                    doc[group_type][group_id][resource_collection] = {}
                
                if version_id:
                    # Add specific version
                    if resource_id not in doc[group_type][group_id][resource_collection]:
                        doc[group_type][group_id][resource_collection][resource_id] = {"versions": {}}
                    if isinstance(doc[group_type][group_id][resource_collection][resource_id], dict):
                        if "versions" not in doc[group_type][group_id][resource_collection][resource_id]:
                            doc[group_type][group_id][resource_collection][resource_id]["versions"] = {}
                        doc[group_type][group_id][resource_collection][resource_id]["versions"][version_id] = resource_data
                else:
                    # Add resource (might contain versions)
                    # If the resource already exists, merge the data instead of replacing it
                    # This preserves inline data fetched with ?inline=*
                    if resource_id in doc[group_type][group_id][resource_collection]:
                        existing = doc[group_type][group_id][resource_collection][resource_id]
                        if isinstance(existing, dict) and isinstance(resource_data, dict):
                            # Merge: resource_data takes precedence, but we preserve existing keys
                            existing.update(resource_data)
                        else:
                            # Can't merge, replace
                            doc[group_type][group_id][resource_collection][resource_id] = resource_data
                    else:
                        # Resource doesn't exist, add it
                        doc[group_type][group_id][resource_collection][resource_id] = resource_data
            else:
                # Add group data
                if isinstance(doc[group_type][group_id], dict) and isinstance(resource_data, dict):
                    doc[group_type][group_id].update(resource_data)
        else:
            # Add to group type level
            if isinstance(doc[group_type], dict) and isinstance(resource_data, dict):
                doc[group_type].update(resource_data)


class ResourceResolver:
    """Resolves resource data from various sources (inline, URL, base64)."""
    
    def __init__(self, loader: 'XRegistryLoader'):
        self.loader = loader
        self.logger = logging.getLogger(__name__ + ".ResourceResolver")
    
    def resolve_resource(self, entity: Dict[str, Any], headers: Dict[str, str], 
                        resource_field_name: str = "resource") -> None:
        """Resolve resource data from resource/resourceurl/resourcebase64 fields.
        
        Args:
            entity: The entity (schema version, message, etc.) that may contain resource references
            headers: HTTP headers for URL fetching
            resource_field_name: The field name to store the resolved resource (e.g., "schema", "resource")
        """
        if not isinstance(entity, dict):
            return
          # Check if resource is already resolved
        if resource_field_name in entity:
            return
        
        # Determine field names based on resource type
        resource_inline_field = resource_field_name
        resource_url_field = f"{resource_field_name}url"
        resource_base64_field = f"{resource_field_name}base64"
        
        # Priority order: {singular} -> {singular}url -> {singular}base64
        # Also check legacy field names for backward compatibility
        if resource_inline_field in entity:
            # Resource is already inline
            entity[resource_field_name] = entity[resource_inline_field]
            
        elif "resource" in entity and resource_field_name != "resource":
            # Legacy inline resource field
            entity[resource_field_name] = entity["resource"]
            
        elif resource_url_field in entity:
            # Fetch resource from URL using singular-specific field
            resource_url = entity[resource_url_field]
            if isinstance(resource_url, str):
                try:
                    self.logger.debug(f"Fetching resource from URL: {resource_url}")
                    _, resource_data = self.loader._load_core(resource_url, headers, ignore_handled=True)
                    if resource_data is not None:
                        entity[resource_field_name] = resource_data
                        self.logger.debug(f"Successfully resolved resource from URL: {resource_url}")
                    else:
                        self.logger.warning(f"Failed to fetch resource from URL: {resource_url}")
                except Exception as e:
                    self.logger.error(f"Error fetching resource from URL {resource_url}: {e}")
                    
        elif "resourceurl" in entity:
            # Legacy resourceurl field
            resource_url = entity["resourceurl"]
            if isinstance(resource_url, str):
                try:
                    self.logger.debug(f"Fetching resource from legacy resourceurl: {resource_url}")
                    _, resource_data = self.loader._load_core(resource_url, headers, ignore_handled=True)
                    if resource_data is not None:
                        entity[resource_field_name] = resource_data
                        self.logger.debug(f"Successfully resolved resource from legacy resourceurl: {resource_url}")
                    else:
                        self.logger.warning(f"Failed to fetch resource from legacy resourceurl: {resource_url}")
                except Exception as e:
                    self.logger.error(f"Error fetching resource from legacy resourceurl {resource_url}: {e}")
                    
        elif resource_base64_field in entity:
            # Decode base64 resource using singular-specific field
            resource_b64 = entity[resource_base64_field]
            if isinstance(resource_b64, str):
                try:
                    decoded_data = base64.b64decode(resource_b64).decode('utf-8')
                    # Try to parse as JSON/YAML
                    try:
                        entity[resource_field_name] = json.loads(decoded_data)
                    except json.JSONDecodeError:
                        try:
                            entity[resource_field_name] = yaml.safe_load(decoded_data)
                        except yaml.YAMLError:
                            # Store as raw text if parsing fails
                            entity[resource_field_name] = decoded_data
                    self.logger.debug(f"Successfully decoded {resource_base64_field} resource")
                except Exception as e:
                    self.logger.error(f"Error decoding {resource_base64_field} resource: {e}")
                    
        elif "resourcebase64" in entity:
            # Legacy resourcebase64 field
            resource_b64 = entity["resourcebase64"]
            if isinstance(resource_b64, str):
                try:
                    decoded_data = base64.b64decode(resource_b64).decode('utf-8')
                    # Try to parse as JSON/YAML
                    try:
                        entity[resource_field_name] = json.loads(decoded_data)
                    except json.JSONDecodeError:
                        try:
                            entity[resource_field_name] = yaml.safe_load(decoded_data)
                        except yaml.YAMLError:
                            # Store as raw text if parsing fails
                            entity[resource_field_name] = decoded_data
                    self.logger.debug(f"Successfully decoded legacy resourcebase64 resource")
                except Exception as e:
                    self.logger.error(f"Error decoding legacy resourcebase64 resource: {e}")
    
    def resolve_collection_urls(self, xreg_doc: JsonNode, headers: Dict[str, str]) -> None:
        """Resolve collection URL references (like messagesurl, schemasurl) in group instances."""
        if not isinstance(xreg_doc, dict):
            return
        
        # Get model groups to process dynamically
        model_groups = self.loader.model.groups
        
        for group_type, group_def in model_groups.items():
            if group_type in xreg_doc and isinstance(xreg_doc[group_type], dict):
                group_collection = xreg_doc[group_type]
                if not isinstance(group_collection, dict):
                    continue
                    
                # Get resource collections for this group type
                group_resources = group_def.get("resources", {})
                if not isinstance(group_resources, dict):
                    continue
                
                for group_id, group in group_collection.items():
                    if not isinstance(group, dict):
                        continue
                    
                    # Check for collection URL references (e.g., messagesurl, schemasurl)
                    for resource_collection, resource_def in group_resources.items():
                        collection_url_field = f"{resource_collection}url"
                        
                        # If the collection is not present but a URL reference exists, fetch it
                        if collection_url_field in group and resource_collection not in group:
                            collection_url = group[collection_url_field]
                            if isinstance(collection_url, str):
                                try:
                                    self.logger.debug(f"Fetching collection from {collection_url_field}: {collection_url}")
                                    _, collection_data = self.loader._load_core(collection_url, headers, ignore_handled=True)
                                    if collection_data is not None and isinstance(collection_data, dict):
                                        group[resource_collection] = collection_data
                                        self.logger.debug(f"Successfully resolved collection from {collection_url_field}: {collection_url}")
                                    else:
                                        self.logger.warning(f"Failed to fetch collection from {collection_url_field}: {collection_url}")
                                except Exception as e:
                                    self.logger.error(f"Error fetching collection from {collection_url_field} {collection_url}: {e}")
    
    def resolve_all_resources(self, xreg_doc: JsonNode, headers: Dict[str, str]) -> None:
        """Recursively resolve all resource references in an xRegistry document."""
        if not isinstance(xreg_doc, dict):
            return
        
        # First resolve collection URLs (like messagesurl, schemasurl)
        self.resolve_collection_urls(xreg_doc, headers)
        
        # Get model groups to process dynamically
        model_groups = self.loader.model.groups
        
        for group_type, group_def in model_groups.items():
            if group_type in xreg_doc and isinstance(xreg_doc[group_type], dict):
                group_collection = xreg_doc[group_type]
                if not isinstance(group_collection, dict):
                    continue
                    
                # Get resource collections for this group type
                group_resources = group_def.get("resources", {})
                if not isinstance(group_resources, dict):
                    continue
                
                for group_id, group in group_collection.items():
                    if isinstance(group, dict):                        # Process each resource collection type in this group
                        for resource_collection, resource_def in group_resources.items():
                            if resource_collection in group and isinstance(group[resource_collection], dict):
                                resource_collection_data = group[resource_collection]
                                if not isinstance(resource_collection_data, dict):
                                    continue
                                    
                                # Get the singular name for this resource type from the model
                                resource_field_name = "resource"  # default fallback
                                if isinstance(resource_def, dict) and "singular" in resource_def:
                                    resource_field_name = resource_def["singular"]
                                
                                for resource_id, resource in resource_collection_data.items():
                                    if isinstance(resource, dict):
                                        # Handle resource versions
                                        if "versions" in resource and isinstance(resource["versions"], dict):
                                            versions = resource["versions"]
                                            if isinstance(versions, dict):
                                                for version_id, version in versions.items():
                                                    if isinstance(version, dict):
                                                        self.resolve_resource(version, headers, resource_field_name)
                                        else:
                                            # Handle direct resource (no versions)
                                            self.resolve_resource(resource, headers, resource_field_name)


class MessageResolver:
    """Resolves basemessage references in message definitions."""
    
    def __init__(self, loader: 'XRegistryLoader'):
        self.loader = loader
        self.logger = logging.getLogger(__name__ + ".MessageResolver")
    
    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries with overlay shadowing base.
        
        Args:
            base: The base dictionary
            overlay: The overlay dictionary that shadows the base
            
        Returns:
            Merged dictionary
        """
        result = dict(base)
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Deep merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Scalar or list: complete replacement
                result[key] = value
        
        return result
    
    def _resolve_basemessage_chain(self, message: Dict[str, Any], xreg_doc: Dict[str, Any], 
                                   visited: Set[str]) -> Optional[Dict[str, Any]]:
        """Resolve the basemessage chain for a message definition.
        
        Args:
            message: The message definition to resolve
            xreg_doc: The full xRegistry document for resolving references
            visited: Set of visited message XID/URLs to detect circular references
            
        Returns:
            The fully resolved message with all base messages merged, or None if circular reference detected
        """
        # Check for basemessageurl reference
        base_ref = message.get('basemessageurl')
        if not base_ref:
            # No base message - return as-is
            return dict(message)
        
        # Check for circular reference
        if base_ref in visited:
            self.logger.error(f"Circular basemessage reference detected: {base_ref}")
            return None
        
        visited.add(base_ref)
        
        # Find the base message in the document
        base_message = self._find_message_by_ref(base_ref, xreg_doc)
        if not base_message:
            self.logger.warning(f"Base message not found: {base_ref}")
            # Per spec: "If the referenced message can not be found then an error MUST NOT be generated"
            # Return current message without base, but remove basemessageurl
            result = dict(message)
            if 'basemessageurl' in result:
                del result['basemessageurl']
            return result
        
        # Recursively resolve the base message's chain
        resolved_base = self._resolve_basemessage_chain(base_message, xreg_doc, visited)
        if resolved_base is None:
            # Circular reference in base chain
            return None
        
        # Remove basemessageurl from both before merging
        current = dict(message)
        if 'basemessageurl' in current:
            del current['basemessageurl']
        if 'basemessageurl' in resolved_base:
            del resolved_base['basemessageurl']
        
        # Merge: base first, then overlay with current message
        merged = self._deep_merge(resolved_base, current)
        
        return merged
    
    def _find_message_by_ref(self, ref: str, xreg_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a message definition by XID or URL reference.
        
        Args:
            ref: The XID or URL reference (e.g., "/messagegroups/group1/messages/msg1")
            xreg_doc: The xRegistry document to search in
            
        Returns:
            The message definition, or None if not found
        """
        # Parse the reference - handle both absolute and fragment identifiers
        ref = ref.lstrip('#')  # Remove fragment prefix if present
        
        # Handle XID format: /messagegroups/{groupid}/messages/{messageid}[/versions/{versionid}]
        parts = [p for p in ref.split('/') if p]
        
        if len(parts) < 4:
            self.logger.warning(f"Invalid message reference format: {ref}")
            return None
        
        # Extract path components
        group_collection = parts[0]  # e.g., "messagegroups"
        group_id = parts[1]
        resource_collection = parts[2]  # e.g., "messages"
        message_id = parts[3]
        
        # Navigate to the message
        if group_collection not in xreg_doc:
            return None
        
        groups = xreg_doc[group_collection]
        if not isinstance(groups, dict) or group_id not in groups:
            return None
        
        group = groups[group_id]
        if not isinstance(group, dict) or resource_collection not in group:
            return None
        
        messages = group[resource_collection]
        if not isinstance(messages, dict) or message_id not in messages:
            return None
        
        message = messages[message_id]
        if not isinstance(message, dict):
            return None
        
        # Check if specific version is requested
        if len(parts) >= 6 and parts[4] == "versions":
            version_id = parts[5]
            if "versions" in message and isinstance(message["versions"], dict):
                if version_id in message["versions"]:
                    return message["versions"][version_id]
            return None
        
        return message
    
    def resolve_all_basemessages(self, xreg_doc: Dict[str, Any]) -> None:
        """Resolve all basemessage references in an xRegistry document.
        
        This processes both messagegroups and endpoints (which can contain embedded messages).
        
        Args:
            xreg_doc: The xRegistry document to process
        """
        if not isinstance(xreg_doc, dict):
            return
        
        # Process messagegroups
        if "messagegroups" in xreg_doc and isinstance(xreg_doc["messagegroups"], dict):
            for group_id, group in xreg_doc["messagegroups"].items():
                if isinstance(group, dict) and "messages" in group:
                    messages = group["messages"]
                    if isinstance(messages, dict):
                        self._resolve_messages_in_collection(messages, xreg_doc)
        
        # Process endpoints (which can have embedded messages)
        if "endpoints" in xreg_doc and isinstance(xreg_doc["endpoints"], dict):
            for endpoint_id, endpoint in xreg_doc["endpoints"].items():
                if isinstance(endpoint, dict) and "messages" in endpoint:
                    messages = endpoint["messages"]
                    if isinstance(messages, dict):
                        self._resolve_messages_in_collection(messages, xreg_doc)
    
    def _resolve_messages_in_collection(self, messages: Dict[str, Any], xreg_doc: Dict[str, Any]) -> None:
        """Resolve basemessage references for all messages in a collection.
        
        Args:
            messages: Dictionary of message definitions
            xreg_doc: The full xRegistry document for resolving references
        """
        for message_id, message in list(messages.items()):
            if not isinstance(message, dict):
                continue
            
            # Check if this message has a basemessageurl
            if 'basemessageurl' not in message:
                continue
            
            self.logger.debug(f"Resolving basemessage for message: {message_id}")
            
            # Resolve the basemessage chain
            visited: Set[str] = set()
            resolved_message = self._resolve_basemessage_chain(message, xreg_doc, visited)
            
            if resolved_message is not None:
                # Replace the message with the resolved version
                messages[message_id] = resolved_message
                self.logger.debug(f"Successfully resolved basemessage for: {message_id}")
            else:
                self.logger.error(f"Failed to resolve basemessage for: {message_id} (circular reference)")


class XRegistryLoader:
    """Main loader class for xRegistry documents with dependency resolution."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = Model(model_path)
        self.dependency_resolver = DependencyResolver(self.model, self)
        self.resource_resolver = ResourceResolver(self)
        self.message_resolver = MessageResolver(self)
        self.logger = logging.getLogger(__name__ + ".XRegistryLoader")
        
        # Schema handling state for template rendering compatibility
        self.schemas_handled: Set[str] = set()
        self.current_url: Optional[str] = None
        
        # Cache for discovered registry roots
        self._registry_roots: Dict[str, str] = {}
    
    def discover_registry_root(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Discover the xRegistry root by finding the /capabilities endpoint.
        
        This method traverses the URL path from the base to find where /capabilities
        is available, which indicates the registry root.
        
        Args:
            url: Any URL within an xRegistry
            headers: HTTP headers for authentication
            
        Returns:
            The registry root URL, or None if not found
        """
        if headers is None:
            headers = {}
        
        # Check cache first
        if url in self._registry_roots:
            return self._registry_roots[url]
        
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            # Not an HTTP URL, can't discover
            return None
        
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # Try the base URL first (most common case)
        try:
            caps_url = urllib.parse.urljoin(base, "/capabilities")
            request = urllib.request.Request(caps_url)
            for key, value in headers.items():
                request.add_header(key, value)
            response = urllib.request.urlopen(request)
            response.read()  # Just check if it exists
            self.logger.info(f"Discovered registry root: {base}")
            self._registry_roots[url] = base
            return base
        except:
            pass
        
        # Try progressively deeper paths
        path_parts = [p for p in parsed.path.split('/') if p]
        for i in range(len(path_parts)):
            test_path = '/' + '/'.join(path_parts[:i+1])
            registry_candidate = urllib.parse.urljoin(base, test_path)
            caps_url = registry_candidate + "/capabilities"
            try:
                request = urllib.request.Request(caps_url)
                for key, value in headers.items():
                    request.add_header(key, value)
                response = urllib.request.urlopen(request)
                response.read()
                self.logger.info(f"Discovered registry root: {registry_candidate}")
                self._registry_roots[url] = registry_candidate
                return registry_candidate
            except:
                continue
        
        # Fallback: assume base is the registry root
        self.logger.warning(f"Could not discover registry root for {url}, using base URL: {base}")
        self._registry_roots[url] = base
        return base
    
    def load(self, uri: str, headers: Optional[Dict[str, str]] = None, 
             is_schema_style: bool = False, expand_refs: bool = False,
             messagegroup_filter: str = "", endpoint_filter: str = "") -> Tuple[str, Optional[JsonNode]]:
        """Load an xRegistry document with basic preprocessing.
        
        Args:
            uri: The URI to load from
            headers: HTTP headers for authentication
            is_schema_style: Whether to use schema-style loading
            expand_refs: Whether to expand references (legacy parameter)
            messagegroup_filter: Filter for message groups
            endpoint_filter: Filter for endpoints
            
        Returns:
            Tuple of (resolved_uri, document) or (uri, None) on error
        """
        if headers is None:
            headers = {}
        
        try:
            resolved_uri, document = self._load_core(uri, headers)
            if document is None:
                return uri, None
            
            # Check if we loaded a single resource (not a full xRegistry document)
            # and wrap it into a proper document structure
            if isinstance(document, dict):
                # Detect if this is a full xRegistry document or a single resource
                model_groups = self.model.groups
                xreg_collections = set(model_groups.keys())
                is_full_document = any(key in document for key in xreg_collections)
                
                if not is_full_document:
                    # This appears to be a single resource - wrap it
                    parser = XRegistryUrlParser(resolved_uri)
                    entry_type = parser.get_entry_type()
                    
                    if entry_type in ["group_instance", "resource_collection", "resource", "version"]:
                        # Wrap single group instance or resource into proper document
                        group_type = parser.get_group_type()
                        group_id = parser.get_group_id()
                        
                        if group_type and group_id:
                            wrapped_doc = {group_type: {group_id: document}}
                            self.logger.debug(f"Wrapped single resource into document structure: {group_type}/{group_id}")
                            document = wrapped_doc
            
            # Apply basic resource resolution
            self.resource_resolver.resolve_all_resources(document, headers)
            
            # Resolve basemessage references
            if isinstance(document, dict):
                self.message_resolver.resolve_all_basemessages(document)
            
            # Apply message group filtering if needed
            if messagegroup_filter and isinstance(document, dict):
                document = self._apply_messagegroup_filter(document, messagegroup_filter)
            
            # Apply endpoint filtering if needed
            if endpoint_filter and isinstance(document, dict):
                document = self._apply_endpoint_filter(document, endpoint_filter)
            
            return resolved_uri, document
            
        except Exception as e:
            self.logger.error(f"Failed to load document from {uri}: {e}")
            return uri, None
    
    def load_stacked(self, uris: List[str], headers: Optional[Dict[str, str]] = None,
                     is_schema_style: bool = False, expand_refs: bool = False,
                     messagegroup_filter: str = "", endpoint_filter: str = "") -> Tuple[str, Optional[JsonNode]]:
        """Load multiple xRegistry documents and stack them with later documents shadowing earlier ones.
        
        Documents are loaded in the order provided. When documents are stacked:
        - Top-level keys from later documents override those from earlier documents
        - Within collections (messagegroups, schemagroups, endpoints, etc.), items are merged by ID
        - Later items with the same ID completely replace earlier items
        
        Args:
            uris: List of URIs to load from (files or URLs can be mixed)
            headers: HTTP headers for authentication
            is_schema_style: Whether to use schema-style loading
            expand_refs: Whether to expand references (legacy parameter)
            messagegroup_filter: Filter for message groups
            endpoint_filter: Filter for endpoints
            
        Returns:
            Tuple of (last_resolved_uri, stacked_document) or (first_uri, None) on error
        """
        if headers is None:
            headers = {}
        
        if not uris:
            self.logger.error("No URIs provided for stacking")
            return "", None
        
        try:
            stacked_document: Optional[Dict[str, Any]] = None
            last_resolved_uri = uris[0]
            
            for uri in uris:
                self.logger.debug(f"Loading document for stacking: {uri}")
                resolved_uri, document = self._load_core(uri, headers)
                last_resolved_uri = resolved_uri
                
                if document is None:
                    self.logger.error(f"Failed to load document from {uri}")
                    return uri, None
                
                if not isinstance(document, dict):
                    self.logger.error(f"Document from {uri} is not a dictionary")
                    return uri, None
                
                # Apply basic resource resolution to this document
                self.resource_resolver.resolve_all_resources(document, headers)
                
                # Stack/merge this document
                if stacked_document is None:
                    stacked_document = document
                else:
                    stacked_document = self._merge_documents(stacked_document, document)
            
            if stacked_document is None:
                return uris[0], None
            
            # Resolve basemessage references in the final stacked document
            if isinstance(stacked_document, dict):
                self.message_resolver.resolve_all_basemessages(stacked_document)
            
            # Apply filters to the final stacked document
            if messagegroup_filter and isinstance(stacked_document, dict):
                stacked_document = self._apply_messagegroup_filter(stacked_document, messagegroup_filter)
            
            if endpoint_filter and isinstance(stacked_document, dict):
                stacked_document = self._apply_endpoint_filter(stacked_document, endpoint_filter)
            
            return last_resolved_uri, stacked_document
            
        except Exception as e:
            self.logger.error(f"Failed to stack documents: {e}")
            return uris[0], None
    
    def _merge_documents(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two xRegistry documents with overlay shadowing base.
        
        For xRegistry collection keys (messagegroups, schemagroups, endpoints, etc.), items
        are merged by ID with overlay items replacing base items. Within each collection,
        group instances are also merged, and within groups, resource collections (messages,
        schemas, etc.) are merged by ID.
        
        Args:
            base: The base document
            overlay: The overlay document that shadows the base
            
        Returns:
            Merged document
        """
        result = dict(base)
        
        # Get model groups to identify xRegistry collections
        model_groups = self.model.groups
        collection_keys = set(model_groups.keys())
        
        for key, value in overlay.items():
            if key in collection_keys and isinstance(value, dict) and isinstance(result.get(key), dict):
                # This is an xRegistry collection (e.g., messagegroups, schemagroups)
                # Merge group instances within the collection
                merged_collection = dict(result[key])
                
                for group_id, group_data in value.items():
                    if group_id in merged_collection and isinstance(group_data, dict) and isinstance(merged_collection[group_id], dict):
                        # This group exists in both - merge the group contents
                        merged_group = dict(merged_collection[group_id])
                        
                        # Get resource collection names for this group type from the model
                        group_def = model_groups.get(key, {})
                        resource_collections = group_def.get("resources", {})
                        
                        if isinstance(resource_collections, dict):
                            resource_collection_names = set(resource_collections.keys())
                        else:
                            resource_collection_names = set()
                        
                        for group_key, group_value in group_data.items():
                            if group_key in resource_collection_names and isinstance(group_value, dict) and isinstance(merged_group.get(group_key), dict):
                                # This is a resource collection (e.g., messages, schemas)
                                # Merge resources by ID within the collection
                                merged_resources = dict(merged_group[group_key])
                                for resource_id, resource_data in group_value.items():
                                    merged_resources[resource_id] = resource_data
                                merged_group[group_key] = merged_resources
                            else:
                                # Not a resource collection - replace completely
                                merged_group[group_key] = group_value
                        
                        merged_collection[group_id] = merged_group
                    else:
                        # Group doesn't exist in base or types don't match - replace completely
                        merged_collection[group_id] = group_data
                
                result[key] = merged_collection
            else:
                # Not a collection or types don't match - replace completely
                result[key] = value
        
        return result
    
    def load_with_dependencies(self, uri: str, headers: Optional[Dict[str, str]] = None,
                              messagegroup_filter: str = "", endpoint_filter: str = "") -> Tuple[str, Optional[JsonNode]]:
        """Load an xRegistry document with full dependency resolution.
        
        Args:
            uri: The URI to load from
            headers: HTTP headers for authentication
            messagegroup_filter: Filter for message groups
            endpoint_filter: Filter for endpoints
            
        Returns:
            Tuple of (resolved_uri, document) or (uri, None) on error
        """
        self.logger.info(f"[ENTRY] load_with_dependencies called with uri: {uri}")
        if headers is None:
            headers = {}
        
        try:
            # Discover the registry root for resolving relative URIs
            registry_root = None
            if uri.startswith("http"):
                registry_root = self.discover_registry_root(uri, headers)
                self.logger.info(f"Using registry root: {registry_root}")
            
            # Load the entry point
            resolved_uri, entry_data = self._load_core(uri, headers)
            if entry_data is None:
                return uri, None
            
            # Build composed document with all dependencies
            composed_document = self.dependency_resolver.build_composed_document(
                resolved_uri, entry_data, headers, registry_root)
            
            # Resolve collection URLs (like messagesurl, schemasurl) first
            # This fetches collections that may contain additional references
            self.resource_resolver.resolve_collection_urls(composed_document, headers)
            
            # Iteratively resolve dependencies until no new references are found
            max_iterations = 10  # Prevent infinite loops
            for iteration in range(max_iterations):
                # Find all references in the current document
                all_refs = []
                model_groups = self.model.groups
                for group_type in model_groups.keys():
                    if group_type in composed_document:
                        refs = self.dependency_resolver.find_xid_references(
                            {group_type: composed_document[group_type]}, group_type)
                        all_refs.extend(refs)
                
                # Filter out already resolved references
                new_refs = [ref for ref in all_refs if ref not in self.dependency_resolver.resolved_resources]
                
                if not new_refs:
                    self.logger.debug(f"Dependency resolution complete after {iteration} iterations")
                    break
                
                self.logger.debug(f"Iteration {iteration}: Resolving {len(new_refs)} new references")
                
                # Resolve new references
                for ref_url in new_refs:
                    # Convert relative URIs to full URLs using the discovered registry root
                    full_ref_url = ref_url
                    if ref_url.startswith('/') and registry_root:
                        full_ref_url = urllib.parse.urljoin(registry_root, ref_url)
                        self.logger.debug(f"Resolved relative URI {ref_url} to {full_ref_url}")
                    
                    # Check if this is a reference to a resource within a group
                    # If so, we should also fetch the parent group instance
                    parser = XRegistryUrlParser(full_ref_url)
                    entry_type = parser.get_entry_type()
                    
                    if entry_type in ["resource", "version"]:
                        # This is a resource or version - we should fetch the parent group too
                        group_type = parser.get_group_type()
                        group_id = parser.get_group_id()
                        
                        if group_type and group_id:
                            # Check if the group instance is already in the document
                            if group_type not in composed_document or group_id not in composed_document.get(group_type, {}):
                                # Construct the parent group URL
                                # group_type already has 's' at the end (e.g., 'schemagroups')
                                group_path = f"/{group_type}/{group_id}"
                                
                                # Construct full URL if we have registry_root
                                if registry_root:
                                    group_url = urllib.parse.urljoin(registry_root, group_path)
                                else:
                                    group_url = group_path
                                
                                self.logger.debug(f"Fetching parent group for resource: {group_url}")
                                group_resource = self.dependency_resolver.resolve_reference(group_url, headers, registry_root)
                                if group_resource is not None:
                                    self.logger.debug(f"Successfully fetched parent group {group_id}, adding to document")
                                    self.dependency_resolver._add_resource_to_document(composed_document, group_url, group_resource)
                                    # Resolve collection URLs in the newly added group
                                    self.resource_resolver.resolve_collection_urls(composed_document, headers)
                                else:
                                    self.logger.debug(f"Failed to fetch parent group from {group_url}")
                    
                    resolved_resource = self.dependency_resolver.resolve_reference(full_ref_url, headers, registry_root)
                    if resolved_resource is not None:
                        self.dependency_resolver._add_resource_to_document(composed_document, full_ref_url, resolved_resource)
                
                # Resolve collection URLs again in case new groups were added
                self.resource_resolver.resolve_collection_urls(composed_document, headers)
            
            # Resolve all individual resource references (like schemaurl, resourceurl)
            self.resource_resolver.resolve_all_resources(composed_document, headers)
            
            # Resolve basemessage references
            if isinstance(composed_document, dict):
                self.message_resolver.resolve_all_basemessages(composed_document)
            
            # Normalize schema references from relative URIs to JSON pointers
            # This must be done after all dependencies are resolved to ensure
            # newly added resources have their references normalized
            self.dependency_resolver._normalize_schema_references(composed_document)
            
            # Apply message group filtering if needed
            if messagegroup_filter and isinstance(composed_document, dict):
                composed_document = self._apply_messagegroup_filter(composed_document, messagegroup_filter)
            
            # Apply endpoint filtering if needed
            if endpoint_filter and isinstance(composed_document, dict):
                composed_document = self._apply_endpoint_filter(composed_document, endpoint_filter)
            
            return resolved_uri, composed_document
            
        except Exception as e:
            self.logger.error(f"Failed to load document with dependencies from {uri}: {e}")
            return uri, None
    
    def _load_core(self, uri: str, headers: Dict[str, str], 
                   ignore_handled: bool = False) -> Tuple[str, Optional[JsonNode]]:
        """Core loading method for fetching and parsing documents.
        
        Args:
            uri: The URI to load from
            headers: HTTP headers for authentication
            ignore_handled: Internal flag for recursive loading
            
        Returns:
            Tuple of (resolved_uri, document) or (uri, None) on error
        """
        try:
            self.logger.debug(f"Loading document from: {uri}")
            
            if uri.startswith(('http://', 'https://')):
                # Load from HTTP/HTTPS
                return self._load_from_url(uri, headers)
            elif uri.startswith('file://'):
                # Load from file URI
                file_path = uri[7:]  # Remove 'file://' prefix
                return self._load_from_file(file_path)
            else:
                # Assume local file path
                return self._load_from_file(uri)
                
        except Exception as e:
            self.logger.error(f"Error loading from {uri}: {e}")
            return uri, None
    
    def _load_from_url(self, url: str, headers: Dict[str, str]) -> Tuple[str, Optional[JsonNode]]:
        """Load document from HTTP/HTTPS URL."""
        try:
            # Use the ?inline flag to fetch nested collections automatically
            # This avoids the need to make multiple HTTP requests
            parser = XRegistryUrlParser(url)
            entry_type = parser.get_entry_type()
            
            # Add ?inline parameter for group instances and resources to fetch their collections
            modified_url = url
            if entry_type in ["group_instance", "resource"]:
                # For group instances, inline all resource collections (messages, schemas, etc.)
                # For resources, inline versions
                separator = '&' if '?' in url else '?'
                inline_param = "inline=*"  # Inline all collections
                modified_url = f"{url}{separator}{inline_param}"
                self.logger.debug(f"Adding inline parameter to URL: {modified_url}")
            
            request = urllib.request.Request(modified_url)
            for key, value in headers.items():
                request.add_header(key, value)
            
            with urllib.request.urlopen(request) as response:
                content = response.read().decode('utf-8')
                document = self._parse_content(content)
                return url, document  # Return original URL for consistency
                
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP error loading {url}: {e.code} {e.reason}")
            return url, None
        except urllib.error.URLError as e:
            self.logger.error(f"URL error loading {url}: {e.reason}")
            return url, None
    
    def _load_from_file(self, file_path: str) -> Tuple[str, Optional[JsonNode]]:
        """Load document from local file."""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return file_path, None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                document = self._parse_content(content)
                return file_path, document
                
        except IOError as e:
            self.logger.error(f"IO error loading {file_path}: {e}")
            return file_path, None
    
    def _parse_content(self, content: str) -> Optional[JsonNode]:
        """Parse content as JSON or YAML."""
        try:
            # Try JSON first
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # Fall back to YAML
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                self.logger.error(f"Failed to parse content as JSON or YAML: {e}")
                return None
    
    def _apply_messagegroup_filter(self, document: Dict[str, Any], 
                                  messagegroup_filter: str) -> Dict[str, Any]:
        """Apply message group filtering to the document."""
        if not messagegroup_filter or "messagegroups" not in document:
            return document
        
        filtered_doc = dict(document)
        if isinstance(filtered_doc.get("messagegroups"), dict):
            filtered_messagegroups = {}
            for group_id, group_data in filtered_doc["messagegroups"].items():
                if messagegroup_filter in group_id:
                    filtered_messagegroups[group_id] = group_data
            filtered_doc["messagegroups"] = filtered_messagegroups
        
        # Also filter schemagroups to match the filtered messagegroups
        if isinstance(filtered_doc.get("schemagroups"), dict):
            filtered_schemagroups = {}
            for group_id, group_data in filtered_doc["schemagroups"].items():
                if messagegroup_filter in group_id:
                    filtered_schemagroups[group_id] = group_data
            filtered_doc["schemagroups"] = filtered_schemagroups
        
        return filtered_doc
    
    def _apply_endpoint_filter(self, document: Dict[str, Any], 
                              endpoint_filter: str) -> Dict[str, Any]:
        """Apply endpoint filtering to the document.
        
        This filters:
        1. The endpoints section to only include endpoints matching the filter
        2. The messagegroups section to only include messagegroups referenced by filtered endpoints
        3. The schemagroups section to match the filtered messagegroups
        """
        if not endpoint_filter or "endpoints" not in document:
            return document
        
        filtered_doc = dict(document)
        
        # Step 1: Filter endpoints by ID
        if isinstance(filtered_doc.get("endpoints"), dict):
            filtered_endpoints = {}
            for endpoint_id, endpoint_data in filtered_doc["endpoints"].items():
                if endpoint_filter in endpoint_id:
                    filtered_endpoints[endpoint_id] = endpoint_data
            filtered_doc["endpoints"] = filtered_endpoints
            
            # Step 2: Collect messagegroup IDs referenced by filtered endpoints
            referenced_messagegroups = set()
            for endpoint_data in filtered_endpoints.values():
                if isinstance(endpoint_data, dict):
                    # Check for messagegroups at top level
                    messagegroups = endpoint_data.get("messagegroups", [])
                    if isinstance(messagegroups, list):
                        for mg_ref in messagegroups:
                            if isinstance(mg_ref, str):
                                # Handle both direct IDs and #/messagegroups/... references
                                mg_id = mg_ref.split("/")[-1] if "/" in mg_ref else mg_ref
                                referenced_messagegroups.add(mg_id)
                    
                    # Also check for messagegroups in config (alternative structure)
                    config = endpoint_data.get("config", {})
                    if isinstance(config, dict):
                        config_messagegroups = config.get("messagegroups", [])
                        if isinstance(config_messagegroups, list):
                            for mg_ref in config_messagegroups:
                                if isinstance(mg_ref, str):
                                    mg_id = mg_ref.split("/")[-1] if "/" in mg_ref else mg_ref
                                    referenced_messagegroups.add(mg_id)
            
            # Step 3: Filter messagegroups to only those referenced by filtered endpoints
            if referenced_messagegroups and isinstance(filtered_doc.get("messagegroups"), dict):
                filtered_messagegroups = {}
                for group_id, group_data in filtered_doc["messagegroups"].items():
                    if group_id in referenced_messagegroups:
                        filtered_messagegroups[group_id] = group_data
                filtered_doc["messagegroups"] = filtered_messagegroups
            
            # Step 4: Filter schemagroups to match the filtered messagegroups
            if referenced_messagegroups and isinstance(filtered_doc.get("schemagroups"), dict):
                filtered_schemagroups = {}
                for group_id, group_data in filtered_doc["schemagroups"].items():
                    if group_id in referenced_messagegroups:
                        filtered_schemagroups[group_id] = group_data
                filtered_doc["schemagroups"] = filtered_schemagroups
        
        return filtered_doc
    
    # Schema handling methods for template rendering compatibility
    def reset_schemas_handled(self) -> None:
        """Reset the set of handled schemas."""
        self.schemas_handled.clear()
    
    def get_schemas_handled(self) -> Set[str]:
        """Get the set of handled schemas."""
        return self.schemas_handled
    
    def add_schema_to_handled(self, schema_ref: str) -> None:
        """Add a schema reference to the handled set."""
        self.schemas_handled.add(schema_ref)
    
    def set_current_url(self, url: Optional[str]) -> None:
        """Set the current URL being processed."""
        self.current_url = url
