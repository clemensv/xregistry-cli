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
#@pytest.mark.skip(reason="temporarily disabled")    
def test_http_end_to_end_proto():
    # clean the output directory
    if os.path.exists(os.path.join(project_root, 'tmp/test/cs/http_end_to_end_proto/')):
        shutil.rmtree(os.path.join(project_root, 'tmp/test/cs/http_end_to_end_proto/'))
    # generate the producer
    sys.argv = ['xregistry', 'generate',  
                '--style', 'httpproducer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'http_end_to_end_proto.xreg.json'),
                '--output', os.path.join(project_root, 'tmp/test/cs/http_end_to_end_proto/producer/'),
                '--projectname', 'Contoso.ERP.Producer']
    assert xregistry.cli() == 0
    # generate the consumer
    sys.argv = [ 'xregistry', 'generate', 
                '--style', 'httpconsumer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'http_end_to_end_proto.xreg.json'),
                '--output', os.path.join(project_root, 'tmp/test/cs/http_end_to_end_proto/consumer/'),
                '--projectname', 'Contoso.ERP.Consumer']
    assert xregistry.cli() == 0
    # run dotnet build on the csproj here that references the generated files already
    subprocess.check_call(['dotnet', 'run'], cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr)
    
