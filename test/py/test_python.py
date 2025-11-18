"""Test the Python code generation and integration with the generated code."""

import platform
import subprocess
import sys
import os
import tempfile
import pytest

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)  # Prioritize local xregistry over installed version

import xregistry


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
    use_shell = platform.system() == 'Windows'
    subprocess.check_call(['make', 'test', '-C', output_dir], cwd=os.path.dirname(__file__), shell=use_shell)


def test_ehproducer_contoso_erp_py():
    """ Test the EventHub producer for Contoso ERP. """
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_ehproducer_contoso_erp_py", "ehproducer")


def test_ehproducer_fabrikam_motorsports_py():
    """ Test the EventHub producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_ehproducer_fabrikam_motorsports_py", "ehproducer")


def test_ehproducer_inkjet_py():
    """ Test the EventHub producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_ehproducer_inkjet_py", "ehproducer")


def test_ehproducer_lightbulb_py():
    """ Test the EventHub producer for Lightbulb. """
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "test_ehproducer_lightbulb_py", "ehproducer")
        
def test_ehproducer_lightbulb_amqp_py():
    """ Test the EventHub producer for Lightbulb. """
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(
            project_root, "test/xreg/lightbulb-amqp.xreg.json"), tmpdirname, "test_ehproducer_lightbulb_amqp_py", "ehproducer")

def test_ehconsumer_contoso_erp_py():
    """ Test the EventHub consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_ehconsumer_contoso_erp_py", "ehconsumer")


def test_ehconsumer_fabrikam_motorsports_py():
    """ Test the EventHub consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_ehconsumer_fabrikam_motorsports_py", "ehconsumer")


def test_ehconsumer_inkjet_py():
    """ Test the EventHub consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_ehconsumer_inkjet_py", "ehconsumer")


def test_ehconsumer_lightbulb_py():
    """ Test the EventHub consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "test_ehconsumer_lightbulb_py", "ehconsumer")


def test_kafkaproducer_contoso_erp_py():
    """ Test the Kafka producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_kafkaproducer_contoso_erp_py", "kafkaproducer")


def test_kafkaproducer_fabrikam_motorsports_py():
    """ Test the Kafka producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_kafkaproducer_fabrikam_motorsports_py", "kafkaproducer")


def test_kafkaproducer_inkjet_py():
    """ Test the Kafka producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_kafkaproducer_inkjet_py", "kafkaproducer")


def test_kafkaproducer_lightbulb_py():
    """ Test the Kafka producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "test_kafkaproducer_lightbulb_py", "kafkaproducer")


def test_kafkaconsumer_contoso_erp_py():
    """ Test the Kafka consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_kafkaconsumer_contoso_erp_py", "kafkaconsumer")


def test_kafkaconsumer_fabrikam_motorsports_py():
    """ Test the Kafka consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_kafkaconsumer_fabrikam_motorsports_py", "kafkaconsumer")


def test_kafkaconsumer_inkjet_py():
    """ Test the Kafka consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_kafkaconsumer_inkjet_py", "kafkaconsumer")


def test_kafkaconsumer_lightbulb_py():
    """ Test the Kafka consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "test_kafkaconsumer_lightbulb_py", "kafkaconsumer")


def test_amqpproducer_lightbulb_py():
    """ Test the AMQP producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb-amqp.xreg.json"),
                        tmpdirname, "test_amqpproducer_lightbulb_py", "amqpproducer")


def test_amqpproducer_contoso_erp_py():
    """ Test the AMQP producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_amqpproducer_contoso_erp_py", "amqpproducer")


def test_amqpconsumer_lightbulb_py():
    """ Test the AMQP consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb-amqp.xreg.json"),
                        tmpdirname, "test_amqpconsumer_lightbulb_py", "amqpconsumer")


def test_amqpconsumer_contoso_erp_py():
    """ Test the AMQP consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_amqpconsumer_contoso_erp_py", "amqpconsumer")


def test_mqttclient_lightbulb_py():
    """ Test the MQTT client for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "test_mqttclient_lightbulb_py", "mqttclient")


def test_mqttclient_contoso_erp_py():
    """ Test the MQTT client for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_mqttclient_contoso_erp_py", "mqttclient")


def test_mqttclient_fabrikam_motorsports_py():
    """ Test the MQTT client for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_mqttclient_fabrikam_motorsports_py", "mqttclient")


def test_mqttclient_inkjet_py():
    """ Test the MQTT client for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_mqttclient_inkjet_py", "mqttclient")


def test_sbproducer_lightbulb_py():
    """ Test the Service Bus producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "test_sbproducer_lightbulb_py", "sbproducer")


def test_sbproducer_contoso_erp_py():
    """ Test the Service Bus producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_sbproducer_contoso_erp_py", "sbproducer")


def test_sbproducer_fabrikam_motorsports_py():
    """ Test the Service Bus producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_sbproducer_fabrikam_motorsports_py", "sbproducer")


def test_sbproducer_inkjet_py():
    """ Test the Service Bus producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_sbproducer_inkjet_py", "sbproducer")


@pytest.mark.skip(reason="Flaky test: Service Bus consumer dispatcher times out intermittently")
def test_sbconsumer_lightbulb_py():
    """ Test the Service Bus consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "test_sbconsumer_lightbulb_py", "sbconsumer")


@pytest.mark.skip(reason="Flaky test: Service Bus consumer dispatcher times out intermittently in CI")
def test_sbconsumer_contoso_erp_py():
    """ Test the Service Bus consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_sbconsumer_contoso_erp_py", "sbconsumer")


@pytest.mark.skip(reason="Flaky test: Service Bus consumer dispatcher times out intermittently in CI")
def test_sbconsumer_fabrikam_motorsports_py():
    """ Test the Service Bus consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_sbconsumer_fabrikam_motorsports_py", "sbconsumer")


@pytest.mark.skip(reason="Flaky test: Service Bus consumer dispatcher times out intermittently in CI")
def test_sbconsumer_inkjet_py():
    """ Test the Service Bus consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_python_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "test_sbconsumer_inkjet_py", "sbconsumer")