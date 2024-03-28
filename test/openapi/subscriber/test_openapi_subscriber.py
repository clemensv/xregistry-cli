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
def test_openapi_subscriber():
    # clean the output directory
    output_dir = os.path.join(project_root, 'tmp/test/openapi/openapi_subscriber/')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    # generate the subscriber
    sys.argv = ['xregistry', 'generate',  
                '--style', 'subscriber', 
                '--language', 'openapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'openapi_subscriber.xreg.json'),
                '--output', output_dir,
                '--projectname', 'ContosoErpSubscriber']
    xregistry.cli()
    # run dotnet build on the csproj here that references the generated files already
    cmd = 'openapi-generator-cli validate -i ' + os.path.join(output_dir, "ContosoErpSubscriber.yml")
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    
