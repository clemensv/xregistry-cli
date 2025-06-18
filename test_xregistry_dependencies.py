#!/usr/bin/env python3
"""
Comprehensive xRegistry Dependency Resolution Test Suite

This test suite validates the xRegistry loader's dependency resolution functionality
across multiple test files, ensuring all fragment references are properly resolved.

Author: xRegistry CLI Team
License: SPDX-License-Identifier: MIT
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass

# Add the xregistry module to the path
sys.path.insert(0, '/workspaces/xregistry-cli')

try:
    from xregistry.generator.xregistry_loader import XRegistryLoader
except ImportError as e:
    print(f"❌ Failed to import XRegistryLoader: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.WARNING)


@dataclass
class DependencyReport:
    """Report of dependency resolution analysis."""
    file_name: str
    total_refs: int
    resolved_refs: int
    missing_refs: int
    resolved_list: List[Tuple[str, str]]
    missing_list: List[Tuple[str, str]]
    endpoints: int
    messagegroups: int
    schemagroups: int
    success: bool


class XRegistryDependencyTester:
    """Comprehensive tester for xRegistry dependency resolution."""
    
    def __init__(self, test_dir: str = "/workspaces/xregistry-cli/test/xreg"):
        self.test_dir = test_dir
        self.loader = XRegistryLoader()
        self.test_files = [
            "contoso-erp.xreg.json",
            "lightbulb.xreg.json", 
            "inkjet.xreg.json",
            "fabrikam-motorsports.xreg.json"
        ]
        self.reports: List[DependencyReport] = []
    
    def find_fragment_references(self, obj: Any, path: str = "") -> List[Tuple[str, str]]:
        """Recursively find all fragment references (#/...) in a JSON structure."""
        refs = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, str) and value.startswith('#/'):
                    refs.append((current_path, value))
                else:
                    refs.extend(self.find_fragment_references(value, current_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                refs.extend(self.find_fragment_references(item, f"{path}[{i}]"))
        
        return refs
    
    def validate_fragment_reference(self, document: Dict[str, Any], ref: str) -> bool:
        """Validate that a fragment reference can be resolved in the document."""
        if not ref.startswith('#/'):
            return False
            
        ref_parts = ref[2:].split('/')  # Remove '#/' and split
        current = document
        
        for part in ref_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        
        return True
    
    def analyze_document_structure(self, document: Dict[str, Any]) -> Tuple[int, int, int]:
        """Analyze document structure and return counts for endpoints, messagegroups, schemagroups."""
        endpoints = len(document.get('endpoints', {}))
        messagegroups = len(document.get('messagegroups', {}))
        schemagroups = len(document.get('schemagroups', {}))
        return endpoints, messagegroups, schemagroups
    
    def test_file_dependency_resolution(self, file_path: str) -> DependencyReport:
        """Test dependency resolution for a specific file."""
        file_name = os.path.basename(file_path)
        
        try:
            # Load document with dependency resolution
            resolved_uri, document = self.loader.load_with_dependencies(file_path)
            
            if document is None or not isinstance(document, dict):
                return DependencyReport(
                    file_name=file_name,
                    total_refs=0, resolved_refs=0, missing_refs=0,
                    resolved_list=[], missing_list=[],
                    endpoints=0, messagegroups=0, schemagroups=0,
                    success=False
                )
            
            # Find all fragment references
            all_refs = self.find_fragment_references(document)
            
            # Validate each reference
            resolved_refs = []
            missing_refs = []
            
            for path, ref in all_refs:
                if self.validate_fragment_reference(document, ref):
                    resolved_refs.append((path, ref))
                else:
                    missing_refs.append((path, ref))
            
            # Analyze document structure
            endpoints, messagegroups, schemagroups = self.analyze_document_structure(document)
            
            return DependencyReport(
                file_name=file_name,
                total_refs=len(all_refs),
                resolved_refs=len(resolved_refs),
                missing_refs=len(missing_refs),
                resolved_list=resolved_refs,
                missing_list=missing_refs,
                endpoints=endpoints,
                messagegroups=messagegroups,
                schemagroups=schemagroups,
                success=len(missing_refs) == 0
            )
            
        except Exception as e:
            print(f"❌ Error testing {file_name}: {e}")
            return DependencyReport(
                file_name=file_name,
                total_refs=0, resolved_refs=0, missing_refs=0,
                resolved_list=[], missing_list=[],
                endpoints=0, messagegroups=0, schemagroups=0,
                success=False
            )
    
    def test_specific_endpoint_dependencies(self, file_path: str, endpoint_name: str) -> bool:
        """Test dependency resolution for a specific endpoint."""
        try:
            resolved_uri, document = self.loader.load_with_dependencies(file_path)
            
            if document is None or not isinstance(document, dict):
                return False
            
            endpoints = document.get('endpoints', {})
            if endpoint_name not in endpoints:
                print(f"❌ Endpoint '{endpoint_name}' not found")
                return False
            
            endpoint_data = endpoints[endpoint_name]
            messagegroups = document.get('messagegroups', {})
            schemagroups = document.get('schemagroups', {})
            
            # Track dependencies
            mg_refs = endpoint_data.get('messagegroups', [])
            schema_deps: Set[str] = set()
            
            print(f"\n🎯 Endpoint Analysis: {endpoint_name}")
            print(f"📡 Protocol: {endpoint_data.get('protocol', 'N/A')}")
            print(f"🏷️  Usage: {endpoint_data.get('usage', 'N/A')}")
            print(f"📦 Envelope: {endpoint_data.get('envelope', 'N/A')}")
            print(f"🔗 Messagegroup references: {len(mg_refs)}")
            
            # Validate messagegroup dependencies
            for ref in mg_refs:
                if ref.startswith('#/messagegroups/'):
                    mg_name = ref.replace('#/messagegroups/', '')
                    if mg_name in messagegroups:
                        print(f"   ✅ {mg_name}")
                        
                        # Check schema dependencies in messages
                        mg_data = messagegroups[mg_name]
                        messages = mg_data.get('messages', {})
                        
                        for msg_name, msg_data in messages.items():
                            schema_ref = msg_data.get('dataschemauri', '')
                            if schema_ref and schema_ref.startswith('#/schemagroups/'):
                                schema_path = schema_ref.replace('#/schemagroups/', '')
                                schema_deps.add(schema_path)
                    else:
                        print(f"   ❌ {mg_name} (not resolved)")
                        return False
            
            # Validate schema dependencies
            print(f"📄 Schema dependencies: {len(schema_deps)}")
            for schema_path in sorted(schema_deps):
                parts = schema_path.split('/')
                if len(parts) >= 3 and parts[1] == 'schemas':
                    sg_name = parts[0]
                    schema_name = parts[2]
                    
                    if (sg_name in schemagroups and 
                        'schemas' in schemagroups[sg_name] and 
                        schema_name in schemagroups[sg_name]['schemas']):
                        format_info = schemagroups[sg_name]['schemas'][schema_name].get('format', 'unknown')
                        print(f"   ✅ {sg_name}/{schema_name} ({format_info})")
                    else:
                        print(f"   ❌ {schema_path} (not resolved)")
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error analyzing endpoint {endpoint_name}: {e}")
            return False
    
    def run_comprehensive_tests(self) -> bool:
        """Run comprehensive dependency resolution tests on all files."""
        print("🚀 xRegistry Dependency Resolution Test Suite")
        print("=" * 70)
        
        success_count = 0
        total_refs = 0
        total_resolved = 0
        
        # Test each file
        for test_file in self.test_files:
            file_path = os.path.join(self.test_dir, test_file)
            
            if not os.path.exists(file_path):
                print(f"⚠️  Test file not found: {test_file}")
                continue
            
            print(f"\n📋 Testing: {test_file}")
            print("-" * 50)
            
            report = self.test_file_dependency_resolution(file_path)
            self.reports.append(report)
            
            print(f"📊 Structure: {report.endpoints} endpoints, "
                  f"{report.messagegroups} messagegroups, {report.schemagroups} schemagroups")
            print(f"🔗 References: {report.total_refs} total, "
                  f"{report.resolved_refs} resolved, {report.missing_refs} missing")
            
            if report.success:
                print(f"✅ {test_file} - ALL DEPENDENCIES RESOLVED")
                success_count += 1
            else:
                print(f"❌ {test_file} - SOME DEPENDENCIES NOT RESOLVED")
                for path, ref in report.missing_list:
                    print(f"   • {path}: {ref}")
            
            total_refs += report.total_refs
            total_resolved += report.resolved_refs
        
        # Test specific endpoint (contoso-erp)
        print(f"\n🎯 Specific Endpoint Test")
        print("-" * 50)
        contoso_file = os.path.join(self.test_dir, "contoso-erp.xreg.json")
        if os.path.exists(contoso_file):
            endpoint_success = self.test_specific_endpoint_dependencies(
                contoso_file, "Contoso.ERP.Eventing.Http"
            )
            if endpoint_success:
                print("✅ Endpoint dependency resolution successful")
            else:
                print("❌ Endpoint dependency resolution failed")
        
        # Print summary
        print(f"\n📈 FINAL SUMMARY")
        print("=" * 70)
        print(f"Files tested: {len(self.reports)}")
        print(f"Files passed: {success_count}")
        print(f"Files failed: {len(self.reports) - success_count}")
        print(f"Total references: {total_refs}")
        print(f"Total resolved: {total_resolved}")
        print(f"Resolution rate: {(total_resolved/total_refs*100):.1f}%" if total_refs > 0 else "N/A")
        
        overall_success = success_count == len(self.reports)
        
        if overall_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ The xRegistry loader correctly resolves all dependencies.")
        else:
            print(f"\n❌ {len(self.reports) - success_count} TESTS FAILED!")
            print("Check the output above for details.")
        
        return overall_success
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """Get a detailed report of all test results."""
        return {
            'summary': {
                'total_files': len(self.reports),
                'passed_files': sum(1 for r in self.reports if r.success),
                'failed_files': sum(1 for r in self.reports if not r.success),
                'total_references': sum(r.total_refs for r in self.reports),
                'total_resolved': sum(r.resolved_refs for r in self.reports),
            },
            'file_reports': [
                {
                    'file_name': r.file_name,
                    'success': r.success,
                    'structure': {
                        'endpoints': r.endpoints,
                        'messagegroups': r.messagegroups,
                        'schemagroups': r.schemagroups
                    },
                    'references': {
                        'total': r.total_refs,
                        'resolved': r.resolved_refs,
                        'missing': r.missing_refs
                    },
                    'missing_references': r.missing_list
                }
                for r in self.reports
            ]
        }


def main() -> int:
    """Main entry point for the test suite."""
    tester = XRegistryDependencyTester()
    
    try:
        success = tester.run_comprehensive_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Test suite interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
