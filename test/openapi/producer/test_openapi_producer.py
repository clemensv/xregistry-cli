"""Test the openapi producer generation."""

import platform
import sys
import os
import subprocess
import shutil

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root))

import xregistry

# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def test_openapi_producer():
    """Test the openapi producer generation."""
    # clean the output directory
    output_dir = os.path.join(project_root, 'tmp/test/openapi/openapi_producer/')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    # generate the producer
    sys.argv = ['xregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'openapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'openapi_producer.xreg.json'),
                '--output', output_dir,
                '--projectname', 'ContosoErpProducer']
    assert xregistry.cli() == 0
    cmd = 'openapi-generator-cli validate -i ' + os.path.join(output_dir, "ContosoErpProducer/ContosoErpProducer.yml".replace('/', os.path.sep))
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)