"""
Java template tests for xRegistry CLI code generation.

Tests generate Java code from xRegistry files, compile with Maven, and run JUnit tests.
This mirrors the C# test pattern in test/cs/test_dotnet.py.
"""

import os
import sys
import tempfile
import subprocess
import pytest

# Get the project root directory (two levels up from this file)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Add the project root to the Python path so we can import xregistry
sys.path.insert(0, project_root)

import xregistry

# Environment variable check for CI/CD
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


def run_java_test(xreg_file: str, output_dir: str, projectname: str, style: str):
    """
    Generate Java code from an xRegistry file, compile with Maven, and run tests.
    
    Args:
        xreg_file: Path to the xRegistry definition file
        output_dir: Directory where generated code will be placed
        projectname: Name of the Java project
        style: Template style (amqpproducer, amqpconsumer, kafkaproducer, etc.)
    """
    try:
        # Generate Java code using xregistry CLI
        sys.argv = [
            'xregistry',
            'generate',
            '--definitions', xreg_file,
            '--output', output_dir,
            '--projectname', projectname,
            '--style', style,
            '--language', 'java'
        ]
        xregistry.cli()
        
        # The code is generated in a subdirectory with the project name
        project_dir = os.path.join(output_dir, projectname)
        data_project_dir = os.path.join(output_dir, f"{projectname}Data")
        
        # First, install the data project if it exists
        if os.path.exists(data_project_dir):
            print(f"\n=== Installing data project in {data_project_dir} ===")
            subprocess.check_call(
                ['mvn', 'clean', 'install', '-DskipTests'],
                cwd=data_project_dir
            )
        
        # Compile the generated code with Maven
        print(f"\n=== Compiling generated Java code in {project_dir} ===")
        subprocess.check_call(
            ['mvn', 'clean', 'compile'],
            cwd=project_dir
        )
        
        # Run JUnit tests with Maven
        print(f"\n=== Running JUnit tests in {project_dir} ===")
        subprocess.check_call(
            ['mvn', 'test'],
            cwd=project_dir
        )
        
        print(f"[PASS] Test passed: {style} with {os.path.basename(xreg_file)}")
        
    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] Test failed: {style} with {os.path.basename(xreg_file)}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout.decode('utf-8')}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr.decode('utf-8')}")
        raise
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        raise


# AMQP Producer Tests

def test_amqpproducer_lightbulb_amqp_java():
    """Test the AMQP (Proton-J) producer for Lightbulb AMQP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb-amqp.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpproducer"
    )


def test_amqpproducer_contoso_erp_java():
    """Test the AMQP (Proton-J) producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/contoso-erp.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpproducer"
    )


def test_amqpproducer_fabrikam_motorsports_java():
    """Test the AMQP (Proton-J) producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpproducer"
    )


def test_amqpproducer_inkjet_java():
    """Test the AMQP (Proton-J) producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/inkjet.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpproducer"
    )


def test_amqpproducer_lightbulb_java():
    """Test the AMQP (Proton-J) producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpproducer"
    )


# AMQP JMS Producer Tests

def test_amqpjmsproducer_lightbulb_amqp_java():
    """Test the AMQP JMS producer for Lightbulb AMQP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb-amqp.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpjmsproducer"
    )


def test_amqpjmsproducer_contoso_erp_java():
    """Test the AMQP JMS producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/contoso-erp.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpjmsproducer"
    )


def test_amqpjmsproducer_fabrikam_motorsports_java():
    """Test the AMQP JMS producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpjmsproducer"
    )


def test_amqpjmsproducer_inkjet_java():
    """Test the AMQP JMS producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/inkjet.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpjmsproducer"
    )


def test_amqpjmsproducer_lightbulb_java():
    """Test the AMQP JMS producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpjmsproducer"
    )


# AMQP Consumer Tests

def test_amqpconsumer_lightbulb_amqp_java():
    """Test the AMQP (Proton-J) consumer for Lightbulb AMQP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb-amqp.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpconsumer"
    )


def test_amqpconsumer_contoso_erp_java():
    """Test the AMQP (Proton-J) consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/contoso-erp.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpconsumer"
    )


def test_amqpconsumer_fabrikam_motorsports_java():
    """Test the AMQP (Proton-J) consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpconsumer"
    )


def test_amqpconsumer_inkjet_java():
    """Test the AMQP (Proton-J) consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/inkjet.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpconsumer"
    )


def test_amqpconsumer_lightbulb_java():
    """Test the AMQP (Proton-J) consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
        tmpdirname,
        "TestProject",
        "amqpconsumer"
    )


# Kafka Producer Tests

def test_kafkaproducer_lightbulb_amqp_java():
    """Test the Kafka producer for Lightbulb AMQP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb-amqp.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaproducer"
    )


def test_kafkaproducer_contoso_erp_java():
    """Test the Kafka producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/contoso-erp.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaproducer"
    )


def test_kafkaproducer_fabrikam_motorsports_java():
    """Test the Kafka producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaproducer"
    )


def test_kafkaproducer_inkjet_java():
    """Test the Kafka producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/inkjet.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaproducer"
    )


def test_kafkaproducer_lightbulb_java():
    """Test the Kafka producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaproducer"
    )


# Kafka Consumer Tests

def test_kafkaconsumer_lightbulb_amqp_java():
    """Test the Kafka consumer for Lightbulb AMQP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb-amqp.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaconsumer"
    )


def test_kafkaconsumer_contoso_erp_java():
    """Test the Kafka consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/contoso-erp.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaconsumer"
    )


def test_kafkaconsumer_fabrikam_motorsports_java():
    """Test the Kafka consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaconsumer"
    )


def test_kafkaconsumer_inkjet_java():
    """Test the Kafka consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/inkjet.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaconsumer"
    )


def test_kafkaconsumer_lightbulb_java():
    """Test the Kafka consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
        tmpdirname,
        "TestProject",
        "kafkaconsumer"
    )


# MQTT Client Tests

def test_mqttclient_contoso_erp_java():
    """Test the MQTT client for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/contoso-erp.xreg.json"),
        tmpdirname,
        "TestProject",
        "mqttclient"
    )


def test_mqttclient_fabrikam_motorsports_java():
    """Test the MQTT client for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json"),
        tmpdirname,
        "TestProject",
        "mqttclient"
    )


def test_mqttclient_inkjet_java():
    """Test the MQTT client for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/inkjet.xreg.json"),
        tmpdirname,
        "TestProject",
        "mqttclient"
    )


def test_mqttclient_lightbulb_java():
    """Test the MQTT client for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_java_test(
        os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
        tmpdirname,
        "TestProject",
        "mqttclient"
    )


if __name__ == "__main__":
    # Allow running individual tests from command line
    pytest.main([__file__, "-v"])
