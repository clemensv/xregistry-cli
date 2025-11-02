import platform
import sys
import os
import subprocess
import shutil

import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root))

import xregistry

# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
#@pytest.mark.skip(reason="Some issue with the CLI tool for verifying the generated code")
def test_asyncapi_producer():
    # clean the output directory
    output_dir = os.path.join(project_root, 'tmp/test/asyncapi/asyncapi_producer'.replace('/', os.path.sep))
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    # generate the producer
    sys.argv = ['xregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'asyncapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'asyncapi_producer.xreg.json'),
                '--output', output_dir,
                '--projectname', 'ContosoErpProducerBinary',
                '--template-args', 'ce_content_mode=binary']
    assert xregistry.cli() == 0
    # run dotnet build on the csproj here that references the generated files already
    cmd = 'asyncapi validate ' + os.path.join(output_dir, "ContosoErpProducerBinary/ContosoErpProducerBinary.yml".replace('/', os.path.sep))
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)

    # generate the producer
    sys.argv = ['xregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'asyncapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'asyncapi_producer.xreg.json'),
                '--output', output_dir,
                '--projectname', 'ContosoErpProducerStructured',
                '--template-args', 'ce_content_mode=structured']
    assert xregistry.cli() == 0
    # run dotnet build on the csproj here that references the generated files already
    cmd = 'asyncapi validate ' + os.path.join(output_dir, "ContosoErpProducerStructured/ContosoErpProducerStructured.yml".replace('/', os.path.sep))
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)


@pytest.mark.parametrize("xreg_file,project_name", [
    ("contoso-erp.xreg.json", "ContosoErp"),
    ("fabrikam-motorsports.xreg.json", "FabrikamMotorsports"),
    ("inkjet.xreg.json", "Inkjet"),
    ("lightbulb-amqp.xreg.json", "LightbulbAmqp"),
    ("lightbulb.xreg.json", "Lightbulb"),
])
def test_asyncapi_producer_xreg_files(xreg_file, project_name):
    """Test AsyncAPI producer generation for all xreg test files"""
    # clean the output directory
    output_dir = os.path.join(project_root, f'tmp/test/asyncapi/producer_{project_name}'.replace('/', os.path.sep))
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    
    xreg_path = os.path.join(project_root, 'test', 'xreg', xreg_file)
    
    # generate the producer with binary content mode
    sys.argv = ['xregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'asyncapi',
                '--definitions', xreg_path,
                '--output', output_dir,
                '--projectname', f'{project_name}ProducerBinary',
                '--template-args', 'ce_content_mode=binary']
    assert xregistry.cli() == 0
    
    # Check if output file was generated
    output_file = os.path.join(output_dir, f"{project_name}ProducerBinary/{project_name}ProducerBinary.yml".replace('/', os.path.sep))
    assert os.path.exists(output_file), f"Expected output file {output_file} was not generated"
    
    # Validate with asyncapi CLI
    cmd = 'asyncapi validate ' + output_file
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=project_root, stdout=sys.stdout, stderr=sys.stderr, shell=True)

    # generate the producer with structured content mode
    sys.argv = ['xregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'asyncapi',
                '--definitions', xreg_path,
                '--output', output_dir,
                '--projectname', f'{project_name}ProducerStructured',
                '--template-args', 'ce_content_mode=structured']
    assert xregistry.cli() == 0
    
    # Check if output file was generated
    output_file = os.path.join(output_dir, f"{project_name}ProducerStructured/{project_name}ProducerStructured.yml".replace('/', os.path.sep))
    assert os.path.exists(output_file), f"Expected output file {output_file} was not generated"
    
    # Validate with asyncapi CLI
    cmd = 'asyncapi validate ' + output_file
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=project_root, stdout=sys.stdout, stderr=sys.stderr, shell=True)
