"""Test the C# code generation and integration with the generated code."""

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
    cmd = ['dotnet', 'test', output_dir] if platform.system() == "Windows" else f'dotnet test {output_dir}'
    
    # Run the dotnet test with stdout and stderr redirected
    with subprocess.Popen(
            cmd, cwd=os.path.dirname(__file__), 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            shell=False, text=True) as proc:
        stdout, stderr = proc.communicate()

    # Output stdout and stderr to the test log
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)

    # Check the return code and raise an error if the command failed
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def test_ehproducer_contoso_erp_cs():
    """ Test the EventHub producer for Contoso ERP. """
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_fabrikam_motorsports_cs():
    """ Test the EventHub producer for Fabrikam Motorsports."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_inkjet_cs():
    """ Test the EventHub producer for Inkjet."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehproducer")


def test_ehproducer_lightbulb_cs():
    """ Test the EventHub producer for Lightbulb. """
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "ehproducer")


def test_ehconsumer_contoso_erp_cs():
    """ Test the EventHub consumer for Contoso ERP."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_fabrikam_motorsports_cs():
    """ Test the EventHub consumer for Fabrikam Motorsports."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_inkjet_cs():
    """ Test the EventHub consumer for Inkjet."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "ehconsumer")


def test_ehconsumer_lightbulb_cs():
    """ Test the EventHub consumer for Lightbulb."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "ehconsumer")


def test_kafkaproducer_contoso_erp_cs():
    """ Test the Kafka producer for Contoso ERP."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_fabrikam_motorsports_cs():
    """ Test the Kafka producer for Fabrikam Motorsports."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_inkjet_cs():
    """ Test the Kafka producer for Inkjet."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaproducer_lightbulb_cs():
    """ Test the Kafka producer for Lightbulb."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "kafkaproducer")


def test_kafkaconsumer_contoso_erp_cs():
    """ Test the Kafka consumer for Contoso ERP."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_fabrikam_motorsports_cs():
    """ Test the Kafka consumer for Fabrikam Motorsports."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_inkjet_cs():
    """ Test the Kafka consumer for Inkjet."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")


def test_kafkaconsumer_lightbulb_cs():
    """ Test the Kafka consumer for Lightbulb."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"),
                        tmpdirname, "TestProject", "kafkaconsumer")


def test_mqttclient_contoso_erp_cs():
    """ Test the MQTT client for Contoso ERP."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_fabrikam_motorsports_cs():
    """ Test the MQTT client for Fabrikam Motorsports."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_inkjet_cs():
    """ Test the MQTT client for Inkjet."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "mqttclient")


def test_mqttclient_lightbulb_cs():
    """ Test the MQTT client for Lightbulb."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "mqttclient")


def test_sbproducer_contoso_erp_cs():
    """ Test the Service Bus producer for Contoso ERP."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


def test_sbproducer_fabrikam_motorsports_cs():
    """ Test the Service Bus producer for Fabrikam Motorsports."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


def test_sbproducer_inkjet_cs():
    """ Test the Service Bus producer for Inkjet."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbproducer")


def test_sbproducer_lightbulb_cs():
    """ Test the Service Bus producer for Lightbulb."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "sbproducer")


def test_sbconsumer_contoso_erp_cs():
    """ Test the Service Bus consumer for Contoso ERP."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


def test_sbconsumer_fabrikam_motorsports_cs():
    """ Test the Service Bus consumer for Fabrikam Motorsports."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


def test_sbconsumer_inkjet_cs():
    """ Test the Service Bus consumer for Inkjet."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace(
            '/', os.sep)), tmpdirname, "TestProject", "sbconsumer")


def test_sbconsumer_lightbulb_cs():
    """ Test the Service Bus consumer for Lightbulb."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(
            project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "sbconsumer")
