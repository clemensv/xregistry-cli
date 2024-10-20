"""Test the Python code generation and integration with the generated code."""

import platform
import subprocess
import sys
import os
import tempfile
import xregistry

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))


# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both

def run_python_test(xreg_file: str, output_dir: str, projectname: str, style: str):
    """
    Run python test via make

    Args:
        xreg_file (str): The path to the xregistry file.
        output_dir (str): The output directory for the generated files.
        projectname (str): The name of the project.
        style (str): The style of the generated code.

    Returns:
        None
    """

    sys.argv = ['xregistry', 'generate',
                '--definitions', xreg_file,
                '--output', output_dir,
                '--projectname', projectname,
                '--style', style,
                '--language', "py"]
    print(f"sys.argv: {sys.argv}")
    assert xregistry.cli() == 0
    cmd = ['make', 'test', '-C', output_dir] if platform.system() == "Windows" else f'make test -C {output_dir}'

    # Run the python test with stdout and stderr redirected
    subprocess.check_call(
            cmd, cwd=os.path.dirname(__file__), 
            stdout=sys.stdout, stderr=sys.stderr,  shell=True, text=True)


def test_ehproducer_contoso_erp_py():
    """ Test the EventHub producer for Contoso ERP. """
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_fabrikam_motorsports_py():
    """ Test the EventHub producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_inkjet_py():
    """ Test the EventHub producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_lightbulb_py():
    """ Test the EventHub producer for Lightbulb. """
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "ehproducer")
        
def test_ehproducer_lightbulb_amqp_py():
    """ Test the EventHub producer for Lightbulb. """
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(
            project_root, "test/xreg/lightbulb-amqp.xreg.json"), tmpdirname, "TestProject", "ehproducer")

def test_ehconsumer_contoso_erp_py():
    """ Test the EventHub consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_fabrikam_motorsports_py():
    """ Test the EventHub consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_inkjet_py():
    """ Test the EventHub consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_lightbulb_py():
    """ Test the EventHub consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "ehconsumer")


def test_kafkaproducer_contoso_erp_py():
    """ Test the Kafka producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_fabrikam_motorsports_py():
    """ Test the Kafka producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_inkjet_py():
    """ Test the Kafka producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_lightbulb_py():
    """ Test the Kafka producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaconsumer_contoso_erp_py():
    """ Test the Kafka consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_fabrikam_motorsports_py():
    """ Test the Kafka consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_inkjet_py():
    """ Test the Kafka consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_lightbulb_py():
    """ Test the Kafka consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "kafkaconsumer")