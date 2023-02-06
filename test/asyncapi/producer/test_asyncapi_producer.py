import platform
import sys
import os
import subprocess
import shutil

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root))

from ceregistry import cli

# this test invokes the ceregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def test_asyncapi_producer():
    # clean the output directory
    output_dir = os.path.join(project_root, 'tmp/test/asyncapi/asyncapi_producer'.replace('/', os.path.sep))
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    # generate the producer
    sys.argv = ['ceregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'asyncapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'asyncapi_producer.disco'),
                '--output', output_dir,
                '--projectname', 'ContosoErpProducerBinary',
                '--template-args', 'ce_content_mode=binary']
    if cli.main() != 0:
        raise Exception("ceregistry failed")
    # run dotnet build on the csproj here that references the generated files already
    cmd = 'asyncapi validate ' + os.path.join(output_dir, "ContosoErpProducerBinary.yml")
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)

    # generate the producer
    sys.argv = ['ceregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'asyncapi',
                '--definitions', os.path.join(os.path.dirname(__file__), 'asyncapi_producer.disco'),
                '--output', output_dir,
                '--projectname', 'ContosoErpProducerStructured',
                '--template-args', 'ce_content_mode=structured']
    if cli.main() != 0:
        raise Exception("ceregistry failed")
    # run dotnet build on the csproj here that references the generated files already
    cmd = 'asyncapi validate ' + os.path.join(output_dir, "ContosoErpProducerStructured.yml")
    subprocess.check_call(cmd.split(" ") if platform.system() == "Windows" else cmd, cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr, shell=True)

