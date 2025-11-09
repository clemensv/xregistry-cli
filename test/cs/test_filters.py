"""
Test the messagegroup and endpoint filter functionality.

Tests verify that:
1. --messagegroup filter correctly limits generation to specified messagegroups
2. --endpoint filter correctly limits generation to specified endpoints
3. Both filters work correctly when used together
"""

import os
import sys
import tempfile
import subprocess
import platform
import json
import pytest

# Get the project root directory (two levels up from this file)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Add the project root to the Python path so we can import xregistry
sys.path.insert(0, project_root)

import xregistry


def run_dotnet_test_with_filters(xreg_file: str, output_dir: str, projectname: str, 
                                  style: str, messagegroup: str = None, endpoint: str = None):
    """
    Generate C# code from an xRegistry file with optional filters, compile with dotnet, and run tests.
    
    Args:
        xreg_file: Path to the xRegistry definition file
        output_dir: Directory where generated code will be placed
        projectname: Name of the C# project
        style: Template style (ehproducer, ehconsumer, etc.)
        messagegroup: Optional messagegroup filter
        endpoint: Optional endpoint filter
    """
    try:
        # Build the xregistry command arguments
        sys.argv = [
            'xregistry',
            'generate',
            '--definitions', xreg_file,
            '--output', output_dir,
            '--projectname', projectname,
            '--style', style,
            '--language', 'cs'
        ]
        
        if messagegroup:
            sys.argv.extend(['--messagegroup', messagegroup])
        
        if endpoint:
            sys.argv.extend(['--endpoint', endpoint])
        
        print(f"\n=== Running xregistry with args: {sys.argv} ===")
        result = xregistry.cli()
        assert result == 0, f"xregistry.cli() returned {result}"
        
        # Find the generated .sln file
        sln_files = []
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.sln'):
                    sln_files.append(os.path.join(root, file))
        
        assert len(sln_files) > 0, f"No .sln files found in {output_dir}"
        
        # Use the first solution file found
        sln_file = sln_files[0]
        project_dir = os.path.dirname(sln_file)
        
        print(f"\n=== Found solution file: {sln_file} ===")
        
        # Use shell=True on Windows to find .cmd files in PATH
        use_shell = platform.system() == 'Windows'
        
        # Compile the generated code with dotnet
        print(f"\n=== Building generated C# code: {sln_file} ===")
        subprocess.check_call(
            ['dotnet', 'build', sln_file],
            shell=use_shell
        )
        
        print(f"[PASS] Test passed: {style} with filters messagegroup={messagegroup}, endpoint={endpoint}")
        
        return output_dir
        
    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] Test failed: {style} with filters messagegroup={messagegroup}, endpoint={endpoint}")
        print(f"Exit code: {e.returncode}")
        raise
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        raise


def check_generated_files_contain(project_dir: str, expected_strings: list, 
                                   not_expected_strings: list | None = None):
    """
    Check that generated C# files contain (or don't contain) expected strings.
    
    Args:
        project_dir: Directory containing generated code
        expected_strings: Strings that should appear in generated files
        not_expected_strings: Strings that should NOT appear in generated files
    """
    if not_expected_strings is None:
        not_expected_strings = []
    
    # Find all .cs files
    cs_files = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.cs'):
                cs_files.append(os.path.join(root, file))
    
    all_content = ""
    for cs_file in cs_files:
        with open(cs_file, 'r', encoding='utf-8') as f:
            all_content += f.read() + "\n"
    
    # Check expected strings are present
    for expected in expected_strings:
        assert expected in all_content, f"Expected string '{expected}' not found in generated code"
        print(f"  [OK] Found expected: {expected}")
    
    # Check not-expected strings are absent
    for not_expected in not_expected_strings:
        assert not_expected not in all_content, f"Unexpected string '{not_expected}' found in generated code"
        print(f"  [OK] Confirmed absent: {not_expected}")


def test_messagegroup_filter_telemetry():
    """Test that --messagegroup filter limits to Telemetry messagegroups only."""
    tmpdirname = tempfile.mkdtemp()
    xreg_file = os.path.join(project_root, "test/xreg/test-filters.xreg.json")
    
    print("\n" + "="*80)
    print("TEST: Messagegroup filter for 'Telemetry'")
    print("="*80)
    
    project_dir = run_dotnet_test_with_filters(
        xreg_file, tmpdirname, "FilterTest", "ehproducer",
        messagegroup="Telemetry"
    )
    
    # Verify generated code includes Telemetry classes but not Diagnostics
    check_generated_files_contain(
        project_dir,
        expected_strings=[
            "Telemetry.Metrics",  # Should have Telemetry.Metrics messagegroup
            "Telemetry.Logs",     # Should have Telemetry.Logs messagegroup
            "CpuUsage",           # Should have message from Telemetry.Metrics
            "ErrorLog"            # Should have message from Telemetry.Logs
        ],
        not_expected_strings=[
            "Diagnostics.Debug",  # Should NOT have Diagnostics.Debug messagegroup
            "Diagnostics.Trace",  # Should NOT have Diagnostics.Trace messagegroup
            "DebugInfo",          # Should NOT have message from Diagnostics.Debug
            "TraceEvent"          # Should NOT have message from Diagnostics.Trace
        ]
    )


def test_messagegroup_filter_diagnostics():
    """Test that --messagegroup filter limits to Diagnostics messagegroups only."""
    tmpdirname = tempfile.mkdtemp()
    xreg_file = os.path.join(project_root, "test/xreg/test-filters.xreg.json")
    
    print("\n" + "="*80)
    print("TEST: Messagegroup filter for 'Diagnostics'")
    print("="*80)
    
    project_dir = run_dotnet_test_with_filters(
        xreg_file, tmpdirname, "FilterTest", "ehproducer",
        messagegroup="Diagnostics"
    )
    
    # Verify generated code includes Diagnostics classes but not Telemetry
    check_generated_files_contain(
        project_dir,
        expected_strings=[
            "Diagnostics.Debug",  # Should have Diagnostics.Debug messagegroup
            "Diagnostics.Trace",  # Should have Diagnostics.Trace messagegroup
            "DebugInfo",          # Should have message from Diagnostics.Debug
            "TraceEvent"          # Should have message from Diagnostics.Trace
        ],
        not_expected_strings=[
            "Telemetry.Metrics",  # Should NOT have Telemetry.Metrics messagegroup
            "Telemetry.Logs",     # Should NOT have Telemetry.Logs messagegroup
            "CpuUsage",           # Should NOT have message from Telemetry.Metrics
            "ErrorLog"            # Should NOT have message from Telemetry.Logs
        ]
    )


def test_endpoint_filter_production():
    """Test that --endpoint filter limits to ProductionEndpoint only."""
    tmpdirname = tempfile.mkdtemp()
    xreg_file = os.path.join(project_root, "test/xreg/test-filters.xreg.json")
    
    print("\n" + "="*80)
    print("TEST: Endpoint filter for 'Production'")
    print("="*80)
    
    project_dir = run_dotnet_test_with_filters(
        xreg_file, tmpdirname, "FilterTest", "ehproducer",
        endpoint="Production"
    )
    
    # ProductionEndpoint references Telemetry messagegroups, so only those should be generated
    check_generated_files_contain(
        project_dir,
        expected_strings=[
            "Telemetry.Metrics",  # ProductionEndpoint uses this
            "Telemetry.Logs",     # ProductionEndpoint uses this
        ],
        not_expected_strings=[
            "Diagnostics.Debug",  # ProductionEndpoint doesn't use this
            "Diagnostics.Trace",  # ProductionEndpoint doesn't use this
        ]
    )


def test_endpoint_filter_development():
    """Test that --endpoint filter limits to DevelopmentEndpoint only."""
    tmpdirname = tempfile.mkdtemp()
    xreg_file = os.path.join(project_root, "test/xreg/test-filters.xreg.json")
    
    print("\n" + "="*80)
    print("TEST: Endpoint filter for 'Development'")
    print("="*80)
    
    project_dir = run_dotnet_test_with_filters(
        xreg_file, tmpdirname, "FilterTest", "ehproducer",
        endpoint="Development"
    )
    
    # DevelopmentEndpoint references Diagnostics messagegroups, so only those should be generated
    check_generated_files_contain(
        project_dir,
        expected_strings=[
            "Diagnostics.Debug",  # DevelopmentEndpoint uses this
            "Diagnostics.Trace",  # DevelopmentEndpoint uses this
        ],
        not_expected_strings=[
            "Telemetry.Metrics",  # DevelopmentEndpoint doesn't use this
            "Telemetry.Logs",     # DevelopmentEndpoint doesn't use this
        ]
    )


def test_combined_filters_telemetry_production():
    """Test that both filters work together: Telemetry messagegroup + Production endpoint."""
    tmpdirname = tempfile.mkdtemp()
    xreg_file = os.path.join(project_root, "test/xreg/test-filters.xreg.json")
    
    print("\n" + "="*80)
    print("TEST: Combined filters - messagegroup='Telemetry' + endpoint='Production'")
    print("="*80)
    
    project_dir = run_dotnet_test_with_filters(
        xreg_file, tmpdirname, "FilterTest", "ehproducer",
        messagegroup="Telemetry",
        endpoint="Production"
    )
    
    # Should only have Telemetry messagegroups (intersection of both filters)
    check_generated_files_contain(
        project_dir,
        expected_strings=[
            "Telemetry.Metrics",    # Should have this messagegroup
            "Telemetry.Logs",       # Should have this messagegroup
        ],
        not_expected_strings=[
            "Diagnostics.Debug",    # Should NOT have Diagnostics messagegroups
            "Diagnostics.Trace",    # Should NOT have Diagnostics messagegroups
        ]
    )


def test_combined_filters_diagnostics_development():
    """Test that both filters work together: Diagnostics messagegroup + Development endpoint."""
    tmpdirname = tempfile.mkdtemp()
    xreg_file = os.path.join(project_root, "test/xreg/test-filters.xreg.json")
    
    print("\n" + "="*80)
    print("TEST: Combined filters - messagegroup='Diagnostics' + endpoint='Development'")
    print("="*80)
    
    project_dir = run_dotnet_test_with_filters(
        xreg_file, tmpdirname, "FilterTest", "ehproducer",
        messagegroup="Diagnostics",
        endpoint="Development"
    )
    
    # Should only have Diagnostics messagegroups (intersection of both filters)
    check_generated_files_contain(
        project_dir,
        expected_strings=[
            "Diagnostics.Debug",    # Should have this messagegroup
            "Diagnostics.Trace",    # Should have this messagegroup
        ],
        not_expected_strings=[
            "Telemetry.Metrics",    # Should NOT have Telemetry messagegroups
            "Telemetry.Logs",       # Should NOT have Telemetry messagegroups
        ]
    )


def test_no_filters_includes_all():
    """Test that without filters, all messagegroups and endpoints are included."""
    tmpdirname = tempfile.mkdtemp()
    xreg_file = os.path.join(project_root, "test/xreg/test-filters.xreg.json")
    
    print("\n" + "="*80)
    print("TEST: No filters - should include everything")
    print("="*80)
    
    project_dir = run_dotnet_test_with_filters(
        xreg_file, tmpdirname, "FilterTest", "ehproducer"
    )
    
    # Without filters, all messagegroups should be included
    check_generated_files_contain(
        project_dir,
        expected_strings=[
            "Telemetry.Metrics",
            "Telemetry.Logs",
            "Diagnostics.Debug",
            "Diagnostics.Trace",
        ]
    )


if __name__ == "__main__":
    # Allow running individual tests from command line
    pytest.main([__file__, "-v", "-s"])
