"""
Unit tests for the xRegistry loader refactoring components.

Tests cover URL parsing, dependency resolution, resource resolution,
and the main loader functionality with various scenarios including
edge cases and error conditions.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, mock_open
import base64
from typing import Dict, Any

from xregistry.generator.xregistry_loader import (
    XRegistryUrlParser, 
    DependencyResolver, 
    ResourceResolver, 
    XRegistryLoader
)
from xregistry.common.model import Model


class TestXRegistryUrlParser(unittest.TestCase):
    """Test URL parsing functionality."""
    
    def test_registry_level_url(self):
        """Test parsing registry-level URLs."""
        parser = XRegistryUrlParser("https://example.com/registry")
        self.assertEqual(parser.get_entry_type(), "registry")
        self.assertIsNone(parser.get_group_type())
        self.assertIsNone(parser.get_group_id())
        self.assertIsNone(parser.get_resource_id())
        self.assertIsNone(parser.get_version_id())
    
    def test_group_type_url(self):
        """Test parsing group type URLs."""
        parser = XRegistryUrlParser("https://example.com/registry/schemagroups")
        self.assertEqual(parser.get_entry_type(), "group_type")
        self.assertEqual(parser.get_group_type(), "schemagroups")
        self.assertIsNone(parser.get_group_id())
        self.assertIsNone(parser.get_resource_id())
        self.assertIsNone(parser.get_version_id())
    
    def test_group_instance_url(self):
        """Test parsing group instance URLs."""
        parser = XRegistryUrlParser("https://example.com/registry/schemagroups/mygroup")
        self.assertEqual(parser.get_entry_type(), "group_instance")
        self.assertEqual(parser.get_group_type(), "schemagroups")
        self.assertEqual(parser.get_group_id(), "mygroup")
        self.assertIsNone(parser.get_resource_id())
        self.assertIsNone(parser.get_version_id())
    
    def test_resource_collection_url(self):
        """Test parsing resource collection URLs."""
        parser = XRegistryUrlParser("https://example.com/registry/schemagroups/mygroup/schemas")
        self.assertEqual(parser.get_entry_type(), "resource_collection")
        self.assertEqual(parser.get_group_type(), "schemagroups")
        self.assertEqual(parser.get_group_id(), "mygroup")
        self.assertIsNone(parser.get_resource_id())
        self.assertIsNone(parser.get_version_id())
    
    def test_resource_url(self):
        """Test parsing resource URLs."""
        parser = XRegistryUrlParser("https://example.com/registry/schemagroups/mygroup/schemas/myschema")
        self.assertEqual(parser.get_entry_type(), "resource")
        self.assertEqual(parser.get_group_type(), "schemagroups")
        self.assertEqual(parser.get_group_id(), "mygroup")
        self.assertEqual(parser.get_resource_id(), "myschema")
        self.assertIsNone(parser.get_version_id())
    
    def test_version_collection_url(self):
        """Test parsing version collection URLs."""
        parser = XRegistryUrlParser("https://example.com/registry/schemagroups/mygroup/schemas/myschema/versions")
        self.assertEqual(parser.get_entry_type(), "version_collection")
        self.assertEqual(parser.get_group_type(), "schemagroups")
        self.assertEqual(parser.get_group_id(), "mygroup")
        self.assertEqual(parser.get_resource_id(), "myschema")
        self.assertIsNone(parser.get_version_id())
    
    def test_version_url(self):
        """Test parsing version URLs."""
        parser = XRegistryUrlParser("https://example.com/registry/schemagroups/mygroup/schemas/myschema/versions/v1")
        self.assertEqual(parser.get_entry_type(), "version")
        self.assertEqual(parser.get_group_type(), "schemagroups")
        self.assertEqual(parser.get_group_id(), "mygroup")
        self.assertEqual(parser.get_resource_id(), "myschema")
        self.assertEqual(parser.get_version_id(), "v1")
    
    def test_file_path_handling(self):
        """Test handling of local file paths."""
        parser = XRegistryUrlParser("/path/to/file.json")
        self.assertEqual(parser.get_entry_type(), "registry")  # File paths default to registry
    
    def test_base_url_extraction(self):
        """Test base URL extraction."""
        parser = XRegistryUrlParser("https://example.com:8080/registry/path")
        self.assertEqual(parser.get_base_url(), "https://example.com:8080")


class TestDependencyResolver(unittest.TestCase):
    """Test dependency resolution functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_model = Mock(spec=Model)
        self.mock_model.groups = {
            "schemagroups": {"resources": {"schemas": {"singular": "schema"}}},
            "messagegroups": {"resources": {"messages": {"singular": "message"}}}
        }
        
        self.mock_loader = Mock(spec=XRegistryLoader)
        self.mock_loader.model = self.mock_model
        
        self.resolver = DependencyResolver(self.mock_model, self.mock_loader)
    
    def test_find_xid_references_in_dict(self):
        """Test finding xid references in dictionary structures."""
        data = {
            "schema": {
                "schemauri": "https://example.com/schemagroups/test/schemas/ref1"
            },
            "message": {
                "messageurl": "https://example.com/messagegroups/test/messages/ref2"
            },
            "other": {
                "someref": "https://example.com/schemagroups/test/schemas/ref3"
            }
        }
        
        refs = self.resolver.find_xid_references(data, "schemagroups")
        self.assertEqual(len(refs), 3)
        self.assertIn("https://example.com/schemagroups/test/schemas/ref1", refs)
        self.assertIn("https://example.com/messagegroups/test/messages/ref2", refs)
        self.assertIn("https://example.com/schemagroups/test/schemas/ref3", refs)
    
    def test_find_xid_references_filters_fragments(self):
        """Test that fragment references are filtered out."""
        data = {
            "internal_ref": "#/definitions/something",
            "external_ref": "https://example.com/schemagroups/test/schemas/external",
            "mixed": ["#/local", "https://example.com/schemagroups/test/schemas/external2"]
        }
        
        refs = self.resolver.find_xid_references(data, "schemagroups")
        self.assertEqual(len(refs), 2)
        self.assertNotIn("#/definitions/something", refs)
        self.assertNotIn("#/local", refs)
        self.assertIn("https://example.com/schemagroups/test/schemas/external", refs)
        self.assertIn("https://example.com/schemagroups/test/schemas/external2", refs)
    
    def test_find_xid_references_in_list(self):
        """Test finding xid references in list structures."""
        data = [
            {"refuri": "https://example.com/schemagroups/test/schemas/ref1"},
            {"refurl": "https://example.com/messagegroups/test/messages/ref2"}
        ]
        
        refs = self.resolver.find_xid_references(data, "schemagroups")
        self.assertEqual(len(refs), 2)
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        # Mock a circular dependency scenario
        self.resolver.pending_resolution.add("https://example.com/test")
        
        result = self.resolver.resolve_reference("https://example.com/test", {})
        self.assertIsNone(result)
    
    @patch('xregistry.generator.xregistry_loader.XRegistryUrlParser')
    def test_build_composed_document_registry_level(self, mock_parser_class):
        """Test building composed document from registry level."""
        mock_parser = Mock()
        mock_parser.get_entry_type.return_value = "registry"
        mock_parser.get_group_type.return_value = None
        mock_parser_class.return_value = mock_parser
        
        entry_data = {"schemagroups": {"test": {}}}
        result = self.resolver.build_composed_document(
            "https://example.com/registry", entry_data, {})
        
        self.assertIsInstance(result, dict)
        self.assertIn("schemagroups", result)


class TestResourceResolver(unittest.TestCase):
    """Test resource resolution functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_loader = Mock(spec=XRegistryLoader)
        self.resolver = ResourceResolver(self.mock_loader)
    
    def test_resolve_inline_resource(self):
        """Test resolving inline resources."""
        entity = {"schema": {"type": "object", "properties": {}}}
        
        self.resolver.resolve_resource(entity, {}, "schema")
        
        # Should already be resolved
        self.assertIn("schema", entity)
        self.assertEqual(entity["schema"]["type"], "object")
    
    def test_resolve_legacy_inline_resource(self):
        """Test resolving legacy inline resource field."""
        entity = {"resource": {"type": "object", "properties": {}}}
        
        self.resolver.resolve_resource(entity, {}, "schema")
        
        # Should copy from resource to schema field
        self.assertIn("schema", entity)
        self.assertEqual(entity["schema"]["type"], "object")
    
    def test_resolve_url_resource(self):
        """Test resolving resource from URL."""
        entity = {"schemaurl": "https://example.com/schema.json"}
        headers = {"Authorization": "Bearer token"}
        
        # Mock the loader response
        mock_schema_data = {"type": "object", "properties": {"name": {"type": "string"}}}
        self.mock_loader._load_core.return_value = ("https://example.com/schema.json", mock_schema_data)
        
        self.resolver.resolve_resource(entity, headers, "schema")
        
        # Verify loader was called correctly
        self.mock_loader._load_core.assert_called_once_with(
            "https://example.com/schema.json", headers, ignore_handled=True)
        
        # Verify resource was resolved
        self.assertIn("schema", entity)
        self.assertEqual(entity["schema"], mock_schema_data)
    
    def test_resolve_legacy_url_resource(self):
        """Test resolving resource from legacy resourceurl field."""
        entity = {"resourceurl": "https://example.com/schema.json"}
        headers = {}
        
        # Mock the loader response
        mock_schema_data = {"type": "object"}
        self.mock_loader._load_core.return_value = ("https://example.com/schema.json", mock_schema_data)
        
        self.resolver.resolve_resource(entity, headers, "schema")
        
        # Verify resource was resolved
        self.assertIn("schema", entity)
        self.assertEqual(entity["schema"], mock_schema_data)
    
    def test_resolve_base64_resource(self):
        """Test resolving resource from base64 field."""
        schema_json = '{"type": "object", "properties": {"name": {"type": "string"}}}'
        schema_b64 = base64.b64encode(schema_json.encode('utf-8')).decode('utf-8')
        
        entity = {"schemabase64": schema_b64}
        
        self.resolver.resolve_resource(entity, {}, "schema")
        
        # Verify resource was decoded and resolved
        self.assertIn("schema", entity)
        self.assertEqual(entity["schema"]["type"], "object")
        self.assertEqual(entity["schema"]["properties"]["name"]["type"], "string")
    
    def test_resolve_legacy_base64_resource(self):
        """Test resolving resource from legacy resourcebase64 field."""
        schema_json = '{"type": "object"}'
        schema_b64 = base64.b64encode(schema_json.encode('utf-8')).decode('utf-8')
        
        entity = {"resourcebase64": schema_b64}
        
        self.resolver.resolve_resource(entity, {}, "schema")
        
        # Verify resource was decoded and resolved
        self.assertIn("schema", entity)
        self.assertEqual(entity["schema"]["type"], "object")
    
    def test_resolve_yaml_base64_resource(self):
        """Test resolving YAML resource from base64 field."""
        schema_yaml = "type: object\nproperties:\n  name:\n    type: string"
        schema_b64 = base64.b64encode(schema_yaml.encode('utf-8')).decode('utf-8')
        
        entity = {"schemabase64": schema_b64}
        
        self.resolver.resolve_resource(entity, {}, "schema")
        
        # Verify YAML was parsed correctly
        self.assertIn("schema", entity)
        self.assertEqual(entity["schema"]["type"], "object")
        self.assertEqual(entity["schema"]["properties"]["name"]["type"], "string")
    
    def test_resolve_text_base64_resource(self):
        """Test resolving non-JSON/YAML base64 resource as text."""
        text_content = "This is plain text content"
        text_b64 = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        
        entity = {"schemabase64": text_b64}
        
        self.resolver.resolve_resource(entity, {}, "schema")
        
        # Verify text was stored as-is
        self.assertIn("schema", entity)
        self.assertEqual(entity["schema"], text_content)
    
    def test_resolve_url_fetch_error(self):
        """Test handling URL fetch errors."""
        entity = {"schemaurl": "https://example.com/nonexistent.json"}
        headers = {}
        
        # Mock loader to return None (error case)
        self.mock_loader._load_core.return_value = ("https://example.com/nonexistent.json", None)
        
        self.resolver.resolve_resource(entity, headers, "schema")
        
        # Should not add schema field on error
        self.assertNotIn("schema", entity)
    
    def test_resolve_invalid_base64(self):
        """Test handling invalid base64 data."""
        entity = {"schemabase64": "invalid-base64-data!!!"}
        
        self.resolver.resolve_resource(entity, {}, "schema")
        
        # Should not add schema field on decode error
        self.assertNotIn("schema", entity)


class TestXRegistryLoader(unittest.TestCase):
    """Test main loader functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('xregistry.generator.xregistry_loader.Model'):
            self.loader = XRegistryLoader()
    
    def test_load_basic_functionality(self):
        """Test basic load functionality."""
        test_data = {"schemagroups": {"test": {"schemas": {"myschema": {"type": "object"}}}}}
        
        with patch.object(self.loader, '_load_core') as mock_load_core:
            with patch.object(self.loader.resource_resolver, 'resolve_all_resources') as mock_resolve:
                mock_load_core.return_value = ("test.json", test_data)
                
                result_uri, result_data = self.loader.load("test.json")
                
                self.assertEqual(result_uri, "test.json")
                self.assertEqual(result_data, test_data)
                mock_load_core.assert_called_once()
                mock_resolve.assert_called_once()
    
    def test_load_with_dependencies(self):
        """Test load with full dependency resolution."""
        test_data = {"schemagroups": {"test": {"schemas": {"myschema": {"type": "object"}}}}}
        composed_data = {"schemagroups": {"test": {"schemas": {"myschema": {"type": "object"}}}}}
        
        with patch.object(self.loader, '_load_core') as mock_load_core:
            with patch.object(self.loader.dependency_resolver, 'build_composed_document') as mock_compose:
                with patch.object(self.loader.resource_resolver, 'resolve_all_resources') as mock_resolve:
                    mock_load_core.return_value = ("test.json", test_data)
                    mock_compose.return_value = composed_data
                    
                    result_uri, result_data = self.loader.load_with_dependencies("test.json")
                    
                    self.assertEqual(result_uri, "test.json")
                    self.assertEqual(result_data, composed_data)
                    mock_load_core.assert_called_once()
                    mock_compose.assert_called_once()
                    mock_resolve.assert_called_once()
    
    def test_load_from_file(self):
        """Test loading from local file."""
        test_data = {"test": "data"}
        test_json = json.dumps(test_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(test_json)
            temp_path = f.name
        
        try:
            result_uri, result_data = self.loader._load_from_file(temp_path)
            
            self.assertEqual(result_uri, temp_path)
            self.assertEqual(result_data, test_data)
        finally:
            os.unlink(temp_path)
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file."""
        result_uri, result_data = self.loader._load_from_file("/nonexistent/file.json")
        
        self.assertEqual(result_uri, "/nonexistent/file.json")
        self.assertIsNone(result_data)
    
    @patch('urllib.request.urlopen')
    def test_load_from_url(self, mock_urlopen):
        """Test loading from HTTP URL."""
        from unittest.mock import MagicMock
        test_data = {"test": "data"}
        test_json = json.dumps(test_data)
        
        # Mock HTTP response - use MagicMock to support context manager protocol
        mock_response = MagicMock()
        mock_response.read.return_value = test_json.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response
        
        result_uri, result_data = self.loader._load_from_url("https://example.com/test.json", {})
        
        self.assertEqual(result_uri, "https://example.com/test.json")
        self.assertEqual(result_data, test_data)
    
    @patch('urllib.request.urlopen')
    def test_load_from_url_with_headers(self, mock_urlopen):
        """Test loading from HTTP URL with custom headers."""
        from unittest.mock import MagicMock
        test_data = {"test": "data"}
        test_json = json.dumps(test_data)
        
        # Mock HTTP response - use MagicMock to support context manager protocol
        mock_response = MagicMock()
        mock_response.read.return_value = test_json.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response
        
        headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        
        with patch('urllib.request.Request') as mock_request:
            result_uri, result_data = self.loader._load_from_url("https://example.com/test.json", headers)
            
            # Verify headers were added to request
            mock_request_instance = mock_request.return_value
            self.assertEqual(mock_request_instance.add_header.call_count, 2)
    
    def test_parse_json_content(self):
        """Test parsing JSON content."""
        test_data = {"test": "data", "number": 42}
        test_json = json.dumps(test_data)
        
        result = self.loader._parse_content(test_json)
        
        self.assertEqual(result, test_data)
    
    def test_parse_yaml_content(self):
        """Test parsing YAML content."""
        test_yaml = """
        test: data
        number: 42
        list:
          - item1
          - item2
        """
        
        result = self.loader._parse_content(test_yaml)
        
        self.assertEqual(result["test"], "data")
        self.assertEqual(result["number"], 42)
        self.assertEqual(result["list"], ["item1", "item2"])
    
    def test_parse_invalid_content(self):
        """Test parsing invalid content."""
        invalid_content = "{ invalid json content"
        
        result = self.loader._parse_content(invalid_content)
        
        self.assertIsNone(result)
    
    def test_messagegroup_filter(self):
        """Test message group filtering."""
        test_data = {
            "messagegroups": {
                "prod.orders": {"messages": {"order": {}}},
                "test.orders": {"messages": {"order": {}}},
                "prod.users": {"messages": {"user": {}}}
            }
        }
        
        filtered = self.loader._apply_messagegroup_filter(test_data, "prod")
        
        self.assertIn("messagegroups", filtered)
        self.assertIn("prod.orders", filtered["messagegroups"])
        self.assertIn("prod.users", filtered["messagegroups"])
        self.assertNotIn("test.orders", filtered["messagegroups"])
    
    def test_schema_handling_state(self):
        """Test schema handling state management."""
        # Test initial state
        self.assertEqual(len(self.loader.get_schemas_handled()), 0)
        
        # Test adding schemas
        self.loader.add_schema_to_handled("schema1")
        self.loader.add_schema_to_handled("schema2")
        
        handled = self.loader.get_schemas_handled()
        self.assertIn("schema1", handled)
        self.assertIn("schema2", handled)
        self.assertEqual(len(handled), 2)
        
        # Test reset
        self.loader.reset_schemas_handled()
        self.assertEqual(len(self.loader.get_schemas_handled()), 0)
    
    def test_current_url_state(self):
        """Test current URL state management."""
        # Test initial state
        self.assertIsNone(self.loader.current_url)
        
        # Test setting URL
        self.loader.set_current_url("https://example.com/test.json")
        self.assertEqual(self.loader.current_url, "https://example.com/test.json")
        
        # Test clearing URL
        self.loader.set_current_url(None)
        self.assertIsNone(self.loader.current_url)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete loader system."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test xRegistry documents
        self.main_doc = {
            "schemagroups": {
                "test": {
                    "schemas": {
                        "user": {
                            "versions": {
                                "v1": {
                                    "schemaurl": f"file://{self.temp_dir}/user-schema.json"
                                }
                            }
                        },
                        "order": {
                            "versions": {
                                "v1": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "amount": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        self.user_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string"}
            }
        }
        
        # Write test files
        with open(f"{self.temp_dir}/main.json", 'w') as f:
            json.dump(self.main_doc, f)
        
        with open(f"{self.temp_dir}/user-schema.json", 'w') as f:
            json.dump(self.user_schema, f)
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_loading_with_resource_resolution(self):
        """Test end-to-end loading with resource resolution."""
        with patch('xregistry.generator.xregistry_loader.Model'):
            loader = XRegistryLoader()
            
            # Mock the model to have the expected structure
            loader.model.groups = {
                "schemagroups": {
                    "resources": {
                        "schemas": {"singular": "schema"}
                    }
                }
            }
            
            main_file = f"{self.temp_dir}/main.json"
            result_uri, result_data = loader.load(main_file)
            
            self.assertEqual(result_uri, main_file)
            self.assertIsNotNone(result_data)
            
            # Verify resource resolution worked
            user_version = result_data["schemagroups"]["test"]["schemas"]["user"]["versions"]["v1"]
            self.assertIn("schema", user_version)
            self.assertEqual(user_version["schema"]["type"], "object")
            self.assertIn("name", user_version["schema"]["properties"])
            
            # Verify inline schema remains unchanged
            order_version = result_data["schemagroups"]["test"]["schemas"]["order"]["versions"]["v1"]
            self.assertIn("schema", order_version)
            self.assertEqual(order_version["schema"]["type"], "object")


if __name__ == '__main__':
    unittest.main()
