"""
Go template tests for xRegistry CLI code generation.

Tests generate Go code from xRegistry files, compile with go build, and verify the code compiles.
"""

import os
import sys
import tempfile
import subprocess
import platform
import pytest

# Get the project root directory (two levels up from this file)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Add the project root to the Python path so we can import xregistry
sys.path.insert(0, project_root)

import xregistry

# Environment variable check for CI/CD
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


def run_go_test(xreg_file: str, output_dir: str, projectname: str, style: str):
    """
    Generate Go code from an xRegistry file and verify it compiles.
    
    Args:
        xreg_file: Path to the xRegistry definition file
        output_dir: Directory where generated code will be placed
        projectname: Name of the Go project
        style: Template style (kafkaproducer, kafkaconsumer, etc.)
    """
    try:
        # Generate Go code using xregistry CLI
        sys.argv = [
            'xregistry',
            'generate',
            '--definitions', xreg_file,
            '--output', output_dir,
            '--projectname', projectname,
            '--style', style,
            '--language', 'go'
        ]
        xregistry.cli()
        
        # The code is generated in a subdirectory with the project name
        project_dir = os.path.join(output_dir, projectname)
        assert os.path.exists(project_dir), f"Project directory not found: {project_dir}"
        
        # Check if go.mod exists
        go_mod_path = os.path.join(project_dir, "go.mod")
        assert os.path.exists(go_mod_path), f"go.mod not found: {go_mod_path}"
        
        # Initialize Go modules and download dependencies
        print(f"Initializing Go modules in {project_dir}")
        result = subprocess.run(
            ['go', 'mod', 'tidy'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            print(f"go mod tidy stdout: {result.stdout}")
            print(f"go mod tidy stderr: {result.stderr}")
            pytest.fail(f"go mod tidy failed with return code {result.returncode}")
        
        # Try to build the Go code
        print(f"Building Go code in {project_dir}")
        result = subprocess.run(
            ['go', 'build', './...'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"go build stdout: {result.stdout}")
            print(f"go build stderr: {result.stderr}")
            pytest.fail(f"go build failed with return code {result.returncode}")
        
        print(f"Go code compiled successfully: {project_dir}")
        
    except subprocess.TimeoutExpired:
        pytest.fail("Go build timed out after 300 seconds")
    except Exception as e:
        pytest.fail(f"Test failed with exception: {str(e)}")


# Kafka Producer Tests

def test_kafkaproducer_contoso_erp_go():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_go_test(os.path.join(project_root, 'samples', 'message-definitions', 'contoso-erp.xreg.json').replace(
            '/', os.sep), tmpdirname, "test_kafkaproducer_contoso_erp_go", "kafkaproducer")

def test_kafkaproducer_fabrikam_motorsports_go():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_go_test(os.path.join(project_root, 'samples', 'message-definitions', 'fabrikam-motorsports.xreg.json').replace(
            '/', os.sep), tmpdirname, "test_kafkaproducer_fabrikam_motorsports_go", "kafkaproducer")

def test_kafkaproducer_inkjet_go():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_go_test(os.path.join(project_root, 'samples', 'message-definitions', 'inkjet.xreg.json').replace(
            '/', os.sep), tmpdirname, "test_kafkaproducer_inkjet_go", "kafkaproducer")

def test_kafkaproducer_lightbulb_go():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_go_test(os.path.join(project_root, 'samples', 'message-definitions', 'lightbulb.xreg.json').replace(
            '/', os.sep), tmpdirname, "test_kafkaproducer_lightbulb_go", "kafkaproducer")


# Kafka Consumer Tests

def test_kafkaconsumer_contoso_erp_go():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_go_test(os.path.join(project_root, 'samples', 'message-definitions', 'contoso-erp.xreg.json').replace(
            '/', os.sep), tmpdirname, "test_kafkaconsumer_contoso_erp_go", "kafkaconsumer")

def test_kafkaconsumer_fabrikam_motorsports_go():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_go_test(os.path.join(project_root, 'samples', 'message-definitions', 'fabrikam-motorsports.xreg.json').replace(
            '/', os.sep), tmpdirname, "test_kafkaconsumer_fabrikam_motorsports_go", "kafkaconsumer")

def test_kafkaconsumer_inkjet_go():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_go_test(os.path.join(project_root, 'samples', 'message-definitions', 'inkjet.xreg.json').replace(
            '/', os.sep), tmpdirname, "test_kafkaconsumer_inkjet_go", "kafkaconsumer")

def test_kafkaconsumer_lightbulb_go():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_go_test(os.path.join(project_root, 'samples', 'message-definitions', 'lightbulb.xreg.json').replace(
            '/', os.sep), tmpdirname, "test_kafkaconsumer_lightbulb_go", "kafkaconsumer")


if __name__ == '__main__':
    # Allow running individual tests
    pytest.main([__file__, '-v'])
