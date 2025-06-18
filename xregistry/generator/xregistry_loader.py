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
        
    def get_base_url(self) -> str:
        """Get the base registry URL."""
        return self.base_url
    
    def get_entry_type(self) -> str:
        """Determine the type of entry point."""
        # For URLs like https://example.com/registry, we want registry level
        # For URLs like https://example.com/registry/schemagroups, we want group_type
        # So we need to check for the registry root differently
        if not self.path_parts or (len(self.path_parts) == 1 and self.path_parts[0] in ['registry', '']):
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
        return self.path_parts[0] if self.path_parts else None
    
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
                nested_refs = self.find_xid_references(item, group_type)
                references.extend(nested_refs)
        
        return references
    
    def resolve_reference(self, ref_url: str, headers: Dict[str, str]) -> Optional[JsonNode]:
        """Resolve a single xid reference."""
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
                
                for nested_ref in nested_refs:
                    self.resolve_reference(nested_ref, headers)
                
                return resource_data
            
        except Exception as e:
            self.logger.error(f"Failed to resolve reference {ref_url}: {e}")
        
        finally:
            self.pending_resolution.discard(ref_url)        
        return None
    
    def build_composed_document(self, entry_url: str, entry_data: JsonNode, headers: Dict[str, str]) -> JsonNode:
        """Build a composed xRegistry document with all dependencies."""
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
        
        elif entry_type == "group_type":
            # Group type collection
            group_type = parser.get_group_type()
            if group_type and isinstance(entry_data, dict):
                composed_doc[group_type] = entry_data
        
        elif entry_type in ["group_instance", "resource_collection", "resource", "version"]:
            # Specific group, resource, or version
            group_type = parser.get_group_type()
            group_id = parser.get_group_id()
            
            if group_type and group_id:
                composed_doc[group_type] = {group_id: entry_data}
        
        # Find and resolve all dependencies
        group_type = parser.get_group_type() or "unknown"
        all_refs = self.find_xid_references(composed_doc, group_type)
        
        for ref_url in all_refs:
            resolved_resource = self.resolve_reference(ref_url, headers)
            if resolved_resource is not None:
                # Add resolved resource to composed document
                self._add_resource_to_document(composed_doc, ref_url, resolved_resource)
        
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
                # Add resource
                group_model = self.model.groups.get(group_type, {})
                resources_model = group_model.get("resources", {})
                resource_collection = resources_model.get("plural", "resources") if isinstance(resources_model, dict) else "resources"
                
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
    
    def resolve_all_resources(self, xreg_doc: JsonNode, headers: Dict[str, str]) -> None:
        """Recursively resolve all resource references in an xRegistry document."""
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


class XRegistryLoader:
    """Main loader class for xRegistry documents with dependency resolution."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = Model(model_path)
        self.dependency_resolver = DependencyResolver(self.model, self)
        self.resource_resolver = ResourceResolver(self)
        self.logger = logging.getLogger(__name__ + ".XRegistryLoader")
        
        # Schema handling state for template rendering compatibility
        self.schemas_handled: Set[str] = set()
        self.current_url: Optional[str] = None
    
    def load(self, uri: str, headers: Optional[Dict[str, str]] = None, 
             is_schema_style: bool = False, expand_refs: bool = False,
             messagegroup_filter: str = "") -> Tuple[str, Optional[JsonNode]]:
        """Load an xRegistry document with basic preprocessing.
        
        Args:
            uri: The URI to load from
            headers: HTTP headers for authentication
            is_schema_style: Whether to use schema-style loading
            expand_refs: Whether to expand references (legacy parameter)
            messagegroup_filter: Filter for message groups
            
        Returns:
            Tuple of (resolved_uri, document) or (uri, None) on error
        """
        if headers is None:
            headers = {}
        
        try:
            resolved_uri, document = self._load_core(uri, headers)
            if document is None:
                return uri, None
            
            # Apply basic resource resolution
            self.resource_resolver.resolve_all_resources(document, headers)
            
            # Apply message group filtering if needed
            if messagegroup_filter and isinstance(document, dict):
                document = self._apply_messagegroup_filter(document, messagegroup_filter)
            
            return resolved_uri, document
            
        except Exception as e:
            self.logger.error(f"Failed to load document from {uri}: {e}")
            return uri, None
    
    def load_with_dependencies(self, uri: str, headers: Optional[Dict[str, str]] = None,
                              messagegroup_filter: str = "") -> Tuple[str, Optional[JsonNode]]:
        """Load an xRegistry document with full dependency resolution.
        
        Args:
            uri: The URI to load from
            headers: HTTP headers for authentication
            messagegroup_filter: Filter for message groups
            
        Returns:
            Tuple of (resolved_uri, document) or (uri, None) on error
        """
        if headers is None:
            headers = {}
        
        try:
            # Load the entry point
            resolved_uri, entry_data = self._load_core(uri, headers)
            if entry_data is None:
                return uri, None
            
            # Build composed document with all dependencies
            composed_document = self.dependency_resolver.build_composed_document(
                resolved_uri, entry_data, headers)
            
            # Resolve all resource references in the composed document
            self.resource_resolver.resolve_all_resources(composed_document, headers)
            
            # Apply message group filtering if needed
            if messagegroup_filter and isinstance(composed_document, dict):
                composed_document = self._apply_messagegroup_filter(composed_document, messagegroup_filter)
            
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
            request = urllib.request.Request(url)
            for key, value in headers.items():
                request.add_header(key, value)
            
            with urllib.request.urlopen(request) as response:
                content = response.read().decode('utf-8')
                document = self._parse_content(content)
                return url, document
                
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
