import sys
import os
import glob

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

import ceregistry

# this test invokes the ceregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def test_validate():
    # clean the output directory
    input_dir = os.path.join(project_root, 'samples'.replace('/', os.path.sep))
    disco_files = glob.glob("**/*.disco", root_dir=input_dir, recursive=True)
    for disco_file in disco_files:
        # generate the producer
        sys.argv = ['ceregistry', 'validate',  
                    '--definitions', os.path.join(input_dir, disco_file)]
        if ceregistry.cli() != 0:
            raise Exception("validation failed")
    disco_files = glob.glob("**/*.disco.yaml", root_dir=input_dir, recursive=True)
    for disco_file in disco_files:
        # generate the producer
        sys.argv = ['ceregistry', 'validate',  
                    '--definitions', os.path.join(input_dir, disco_file)]
        if ceregistry.cli() != 0:
            raise Exception("validation failed")
