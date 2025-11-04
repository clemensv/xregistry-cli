"""Test the TypeScript code generation and integration with the generated code."""

import platform
import subprocess
import sys
import os
import tempfile
import xregistry
import pytest

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


def run_typescript_test(xreg_file: str, output_dir: str, projectname: str, style: str):
    """
    Run npm test on the generated TypeScript project.

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
                '--language', "ts"]
    print(f"sys.argv: {sys.argv}")
    assert xregistry.cli() == 0
    
    # The generated TypeScript project is in a subdirectory based on the style
    # Map style to directory name (e.g., kafkaproducer -> TestProjectKafkaProducer)
    style_map = {
        'kafkaproducer': 'KafkaProducer',
        'kafkaconsumer': 'KafkaConsumer',
        'ehproducer': 'EventHubsProducer',
        'ehconsumer': 'EventHubsConsumer',
        'sbproducer': 'ServiceBusProducer',
        'sbconsumer': 'ServiceBusConsumer',
        'amqpproducer': 'AmqpProducer',
        'amqpconsumer': 'AmqpConsumer',
        'mqttclient': 'MqttClient',
        'egproducer': 'EventGridProducer'
    }
    
    style_suffix = style_map.get(style, style.capitalize())
    project_dir = os.path.join(output_dir, f"{projectname}{style_suffix}")
    data_project_dir = os.path.join(output_dir, f"{projectname}Data")
    
    if not os.path.exists(project_dir):
        raise FileNotFoundError(f"Generated project directory not found: {project_dir}")
    
    # First, install and build the data project if it exists
    if os.path.exists(data_project_dir):
        print(f"\n=== Installing data project in {data_project_dir} ===")
        subprocess.check_call(['npm', 'install'], cwd=data_project_dir, stdout=sys.stdout, stderr=sys.stderr)
        
        print(f"\n=== Building data project in {data_project_dir} ===")
        subprocess.check_call(['npm', 'run', 'build'], cwd=data_project_dir, stdout=sys.stdout, stderr=sys.stderr)
    
    # Run npm install in main project
    subprocess.check_call(['npm', 'install'], cwd=project_dir, stdout=sys.stdout, stderr=sys.stderr)
    
    # Run npm test
    subprocess.check_call(['npm', 'test'], cwd=project_dir, stdout=sys.stdout, stderr=sys.stderr)


def test_kafkaproducer_contoso_erp_ts():
    """ Test the Kafka producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_fabrikam_motorsports_ts():
    """ Test the Kafka producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_inkjet_ts():
    """ Test the Kafka producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_lightbulb_ts():
    """ Test the Kafka producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaconsumer_contoso_erp_ts():
    """ Test the Kafka consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_fabrikam_motorsports_ts():
    """ Test the Kafka consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_inkjet_ts():
    """ Test the Kafka consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_lightbulb_ts():
    """ Test the Kafka consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "kafkaconsumer")


def test_ehproducer_contoso_erp_ts():
    """ Test the Event Hubs producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_fabrikam_motorsports_ts():
    """ Test the Event Hubs producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_inkjet_ts():
    """ Test the Event Hubs producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_lightbulb_ts():
    """ Test the Event Hubs producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_lightbulb_amqp_ts():
    """ Test the Event Hubs producer for Lightbulb with AMQP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb-amqp.xreg.json"),
                        tmpdirname, "TestProject", "ehproducer")


def test_ehconsumer_contoso_erp_ts():
    """ Test the Event Hubs consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_fabrikam_motorsports_ts():
    """ Test the Event Hubs consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_inkjet_ts():
    """ Test the Event Hubs consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_lightbulb_ts():
    """ Test the Event Hubs consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "ehconsumer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_sbproducer_contoso_erp_ts():
    """ Test the Service Bus producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_sbproducer_fabrikam_motorsports_ts():
    """ Test the Service Bus producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_sbproducer_inkjet_ts():
    """ Test the Service Bus producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_sbproducer_lightbulb_ts():
    """ Test the Service Bus producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "sbproducer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_sbconsumer_contoso_erp_ts():
    """ Test the Service Bus consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_sbconsumer_fabrikam_motorsports_ts():
    """ Test the Service Bus consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_sbconsumer_inkjet_ts():
    """ Test the Service Bus consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_sbconsumer_lightbulb_ts():
    """ Test the Service Bus consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "sbconsumer")


def test_amqpproducer_contoso_erp_ts():
    """ Test the AMQP producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "amqpproducer")


def test_amqpproducer_fabrikam_motorsports_ts():
    """ Test the AMQP producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "amqpproducer")


def test_amqpproducer_inkjet_ts():
    """ Test the AMQP producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "amqpproducer")


def test_amqpproducer_lightbulb_ts():
    """ Test the AMQP producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "amqpproducer")


def test_amqpconsumer_contoso_erp_ts():
    """ Test the AMQP consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "amqpconsumer")


def test_amqpconsumer_fabrikam_motorsports_ts():
    """ Test the AMQP consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "amqpconsumer")


def test_amqpconsumer_inkjet_ts():
    """ Test the AMQP consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "amqpconsumer")


def test_amqpconsumer_lightbulb_ts():
    """ Test the AMQP consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "amqpconsumer")


def test_mqttclient_contoso_erp_ts():
    """ Test the MQTT client for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_fabrikam_motorsports_ts():
    """ Test the MQTT client for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_inkjet_ts():
    """ Test the MQTT client for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_lightbulb_ts():
    """ Test the MQTT client for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "mqttclient")


def test_egproducer_contoso_erp_ts():
    """ Test the Event Grid producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "egproducer")


def test_egproducer_fabrikam_motorsports_ts():
    """ Test the Event Grid producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "egproducer")


def test_egproducer_inkjet_ts():
    """ Test the Event Grid producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "egproducer")


def test_egproducer_lightbulb_ts():
    """ Test the Event Grid producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_typescript_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "egproducer")
