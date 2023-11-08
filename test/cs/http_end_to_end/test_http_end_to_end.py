import sys
import os
import subprocess
import shutil

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root))

import xregistry

# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def test_http_end_to_end():
    # clean the output directory
    if os.path.exists(os.path.join(project_root, 'tmp/test/cs/http_end_to_end/')):
        shutil.rmtree(os.path.join(project_root, 'tmp/test/cs/http_end_to_end/'))
    # generate the producer
    sys.argv = ['xregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'http_end_to_end.cereg'),
                '--output', os.path.join(project_root, 'tmp/test/cs/http_end_to_end/producer/'),
                '--projectname', 'Contoso.ERP.Producer']
    xregistry.cli()
    # generate the consumer
    sys.argv = [ 'xregistry', 'generate',  
                '--style', 'consumer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'http_end_to_end.cereg'),
                '--output', os.path.join(project_root, 'tmp/test/cs/http_end_to_end/consumer/'),
                '--projectname', 'Contoso.ERP.Consumer']
    xregistry.cli()
    # run dotnet build on the csproj here that references the generated files already
    subprocess.check_call(['dotnet', 'run'], cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr)
    
