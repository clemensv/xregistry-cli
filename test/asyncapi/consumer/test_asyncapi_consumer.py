import platform
import sys
import os
import subprocess
import shutil

import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root))

import xregistry

# this test invokes the xregistry command line tool to generate AsyncAPI consumer documents
# and validates them with the AsyncAPI CLI tool
def test_asyncapi_consumer():
    # clean the output directory
    output_dir = os.path.join(project_root, 'tmp/test/asyncapi/asyncapi_consumer'.replace('/', os.path.sep))
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    # generate the consumer with binary content mode
    sys.argv = ['xregistry', 'generate',  
                '--style', 'consumer', 
                '--language', 'asyncapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'asyncapi_consumer.xreg.json'),
                '--output', output_dir,
                '--projectname', 'ContosoErpConsumerBinary',
                '--template-args', 'ce_content_mode=binary']
    assert xregistry.cli() == 0
    # validate with asyncapi CLI
    cmd = 'asyncapi validate ' + os.path.join(output_dir, "ContosoErpConsumerBinary/ContosoErpConsumerBinary.yml".replace('/', os.path.sep))
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), shell=True)

    # generate the consumer with structured content mode
    sys.argv = ['xregistry', 'generate',  
                '--style', 'consumer', 
                '--language', 'asyncapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'asyncapi_consumer.xreg.json'),
                '--output', output_dir,
                '--projectname', 'ContosoErpConsumerStructured',
                '--template-args', 'ce_content_mode=structured']
    assert xregistry.cli() == 0
    # validate with asyncapi CLI
    cmd = 'asyncapi validate ' + os.path.join(output_dir, "ContosoErpConsumerStructured/ContosoErpConsumerStructured.yml".replace('/', os.path.sep))
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), shell=True)


@pytest.mark.parametrize("xreg_file,project_name", [
    ("contoso-erp.xreg.json", "ContosoErp"),
    ("fabrikam-motorsports.xreg.json", "FabrikamMotorsports"),
    ("inkjet.xreg.json", "Inkjet"),
    ("lightbulb-amqp.xreg.json", "LightbulbAmqp"),
    ("lightbulb.xreg.json", "Lightbulb"),
])
def test_asyncapi_consumer_xreg_files(xreg_file, project_name):
    """Test AsyncAPI consumer generation for all xreg test files"""
    # clean the output directory
    output_dir = os.path.join(project_root, f'tmp/test/asyncapi/consumer_{project_name}'.replace('/', os.path.sep))
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    
    xreg_path = os.path.join(project_root, 'test', 'xreg', xreg_file)
    
    # generate the consumer with binary content mode
    sys.argv = ['xregistry', 'generate',  
                '--style', 'consumer', 
                '--language', 'asyncapi',
                '--definitions', xreg_path,
                '--output', output_dir,
                '--projectname', f'{project_name}ConsumerBinary',
                '--template-args', 'ce_content_mode=binary']
    assert xregistry.cli() == 0
    
    # Check if output file was generated
    output_file = os.path.join(output_dir, f"{project_name}ConsumerBinary/{project_name}ConsumerBinary.yml".replace('/', os.path.sep))
    assert os.path.exists(output_file), f"Expected output file {output_file} was not generated"
    
    # Validate with asyncapi CLI
    cmd = 'asyncapi validate ' + output_file
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=project_root, shell=True)

    # generate the consumer with structured content mode
    sys.argv = ['xregistry', 'generate',  
                '--style', 'consumer', 
                '--language', 'asyncapi',
                '--definitions', xreg_path,
                '--output', output_dir,
                '--projectname', f'{project_name}ConsumerStructured',
                '--template-args', 'ce_content_mode=structured']
    assert xregistry.cli() == 0
    
    # Check if output file was generated
    output_file = os.path.join(output_dir, f"{project_name}ConsumerStructured/{project_name}ConsumerStructured.yml".replace('/', os.path.sep))
    assert os.path.exists(output_file), f"Expected output file {output_file} was not generated"
    
    # Validate with asyncapi CLI
    cmd = 'asyncapi validate ' + output_file
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=project_root, shell=True)
