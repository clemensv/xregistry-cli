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
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)

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
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)
