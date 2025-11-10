"""Test the C# code generation and integration with the generated code."""

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



# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both

def run_dotnet_test(xreg_file: str, output_dir: str, projectname: str, style: str):
    """
    Run dotnet test on the csproj that references the generated files.

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
                '--language', "cs"]
    print(f"sys.argv: {sys.argv}")
    assert xregistry.cli() == 0
    
    # Use shell=True on Windows for .cmd files, direct execution on Linux
    use_shell = platform.system() == 'Windows'
    subprocess.check_call(['dotnet', 'test', output_dir], cwd=os.path.dirname(__file__), shell=use_shell)

def test_ehproducer_contoso_erp_cs():
    """ Test the EventHub producer for Contoso ERP. """
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_fabrikam_motorsports_cs():
    """ Test the EventHub producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_inkjet_cs():
    """ Test the EventHub producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_lightbulb_cs():
    """ Test the EventHub producer for Lightbulb. """
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "ehproducer")
        
def test_ehproducer_lightbulb_amqp_cs():
    """ Test the EventHub producer for Lightbulb. """
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb-amqp.xreg.json"), tmpdirname, "TestProject", "ehproducer")

def test_ehconsumer_contoso_erp_cs():
    """ Test the EventHub consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_fabrikam_motorsports_cs():
    """ Test the EventHub consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_inkjet_cs():
    """ Test the EventHub consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_lightbulb_cs():
    """ Test the EventHub consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "ehconsumer")


def test_kafkaproducer_contoso_erp_cs():
    """ Test the Kafka producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_fabrikam_motorsports_cs():
    """ Test the Kafka producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_inkjet_cs():
    """ Test the Kafka producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_lightbulb_cs():
    """ Test the Kafka producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "kafkaproducer")


# Skipped: inkjet-protocol-variants contains MQTT-specific metadata (URI template topics)
# that is incompatible with Kafka producer templates which expect literal topic names
# def test_kafkaproducer_inkjet_protocol_variants_cs():
#     """ Test the Kafka producer for Inkjet Protocol Variants with basemessage inheritance."""
#     tmpdirname = tempfile.mkdtemp()
#     run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet-protocol-variants.xreg.json".replace(
#             '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaconsumer_contoso_erp_cs():
    """ Test the Kafka consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_fabrikam_motorsports_cs():
    """ Test the Kafka consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_inkjet_cs():
    """ Test the Kafka consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_lightbulb_cs():
    """ Test the Kafka consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_inkjet_protocol_variants_cs():
    """ Test the Kafka consumer for Inkjet Protocol Variants with basemessage inheritance."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet-protocol-variants.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_mqttclient_contoso_erp_cs():
    """ Test the MQTT client for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_fabrikam_motorsports_cs():
    """ Test the MQTT client for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_inkjet_cs():
    """ Test the MQTT client for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_lightbulb_cs():
    """ Test the MQTT client for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_inkjet_protocol_variants_cs():
    """ Test the MQTT client for Inkjet Protocol Variants with basemessage inheritance."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet-protocol-variants.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Service Bus emulator startup exceeds TestContainers 60s timeout in CI")
def test_sbproducer_contoso_erp_cs():
    """ Test the Service Bus producer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Service Bus emulator startup exceeds TestContainers 60s timeout in CI")
def test_sbproducer_fabrikam_motorsports_cs():
    """ Test the Service Bus producer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Service Bus emulator startup exceeds TestContainers 60s timeout in CI")
def test_sbproducer_inkjet_cs():
    """ Test the Service Bus producer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Service Bus emulator startup exceeds TestContainers 60s timeout in CI")
def test_sbproducer_lightbulb_cs():
    """ Test the Service Bus producer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "sbproducer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Service Bus emulator startup exceeds TestContainers 60s timeout in CI")
def test_sbconsumer_contoso_erp_cs():
    """ Test the Service Bus consumer for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Service Bus emulator startup exceeds TestContainers 60s timeout in CI")
def test_sbconsumer_fabrikam_motorsports_cs():
    """ Test the Service Bus consumer for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Service Bus emulator startup exceeds TestContainers 60s timeout in CI")
def test_sbconsumer_inkjet_cs():
    """ Test the Service Bus consumer for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Service Bus emulator startup exceeds TestContainers 60s timeout in CI")
def test_sbconsumer_lightbulb_cs():
    """ Test the Service Bus consumer for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "sbconsumer")

def test_sbazfn_contoso_erp_cs():
    """ Test the Azure Function for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbazfn")
        
def test_sbazfn_fabrikam_motorsports_cs():
    """ Test the Azure Function for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbazfn")
        
def test_sbazfn_inkjet_cs():
    """ Test the Azure Function for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbazfn")
        
def test_sbazfn_lightbulb_cs():
    """ Test the Azure Function for Lightbulb."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "sbazfn")
        
def test_ehazfn_contoso_erp_cs():
    """ Test the Azure Function for Contoso ERP."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehazfn")
        
def test_ehazfn_fabrikam_motorsports_cs():
    """ Test the Azure Function for Fabrikam Motorsports."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehazfn")
        
def test_ehazfn_inkjet_cs():
    """ Test the Azure Function for Inkjet."""
    tmpdirname = tempfile.mkdtemp()
    run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehazfn")