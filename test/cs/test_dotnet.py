import platform
import subprocess
import sys
import os
import glob
import tempfile

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

import xregistry

# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def run_dotnet_test(xreg_file: str, output_dir: str, projectname: str, style: str):
    # generate the producer
    sys.argv = ['xregistry', 'generate',  
            '--definitions', xreg_file,
            '--output', output_dir,
            '--projectname', projectname,
            '--style', style,
            '--language', "cs"]
    print(f"sys.argv: {sys.argv}")
    assert xregistry.cli() == 0
    # run dotnet test on the csproj here that references the generated files already
    cmd = 'dotnet test ' + output_dir
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)

def test_ehproducer_contoso_erp_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "ehproducer")

def test_ehproducer_fabrikam_motorsports_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "ehproducer")

def test_ehproducer_inkjet_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "ehproducer")

def test_ehproducer_lightbulb_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "ehproducer")

def test_ehconsumer_contoso_erp_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "ehconsumer")

def test_ehconsumer_fabrikam_motorsports_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "ehconsumer")

def test_ehconsumer_inkjet_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "ehconsumer")

def test_ehconsumer_lightbulb_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "ehconsumer")

def test_kafkaproducer_contoso_erp_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")

def test_kafkaproducer_fabrikam_motorsports_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")

def test_kafkaproducer_inkjet_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "kafkaproducer")

def test_kafkaproducer_lightbulb_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "kafkaproducer")

def test_kafkaconsumer_contoso_erp_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")

def test_kafkaconsumer_fabrikam_motorsports_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")

def test_kafkaconsumer_inkjet_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "kafkaconsumer")

def test_kafkaconsumer_lightbulb_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "kafkaconsumer")

def test_mqttclient_contoso_erp_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/contoso-erp.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "mqttclient")

def test_mqttclient_fabrikam_motorsports_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/fabrikam-motorsports.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "mqttclient")

def test_mqttclient_inkjet_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/inkjet.xreg.json".replace('/', os.sep)), tmpdirname, "TestProject", "mqttclient")

def test_mqttclient_lightbulb_cs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        run_dotnet_test(os.path.join(project_root, "test/xreg/lightbulb.xreg.json"), tmpdirname, "TestProject", "mqttclient")