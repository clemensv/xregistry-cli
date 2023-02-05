import sys
import os
import subprocess
import shutil

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root, 'cedisco_codegen'))

import cedisco_codegen

# this test invokes the cedisco_codegen command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def test_openapi_producer():
    # clean the output directory
    output_dir = os.path.join(project_root, 'tmp/test/openapi/openapi_producer/')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    # generate the producer
    sys.argv = ['cedisco_codegen', 
                '--style', 'producer', 
                '--language', 'openapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'openapi_producer.disco'),
                '--output', output_dir,
                '--projectname', 'ContosoErpProducer']
    cedisco_codegen.main()
    # run dotnet build on the csproj here that references the generated files already
    subprocess.check_call(['openapi-generator-cli', 'validate', '-i', os.path.join(output_dir, "ContosoErpProducer.yml")], cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    
