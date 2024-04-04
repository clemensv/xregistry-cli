import random
import string
import sys
import os
import subprocess
import shutil
import time

import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

import xregistry

   
#@pytest.mark.skip(reason="temporarily disabled")    
def test_codegen_cs():
    input_dir = os.path.join(project_root, 'xregistry/templates/cs'.replace('/', os.path.sep))
    # loop through all dirs in the input directory that have no leading underscore in their name
    for dir_name in os.listdir(input_dir):
        if os.path.exists(os.path.join(project_root, f'tmp/test/cs/{dir_name}/'.replace('/', os.path.sep))):
            shutil.rmtree(os.path.join(project_root, f'tmp/test/cs/{dir_name}/'.replace('/', os.path.sep)))
        output_dir = os.path.join(project_root, f'tmp/test/cs/{dir_name}'.replace('/', os.path.sep))
        if not dir_name.startswith('_') and os.path.isdir(os.path.join(input_dir, dir_name)):
            # generate the code for each directory
            sys.argv = ['xregistry', 'generate',  
                        '--style', dir_name, 
                        '--language', 'cs',
                        '--definitions', os.path.join(project_root, 'samples/message-definitions/contoso-erp.xreg.json'.replace('/', os.path.sep)),
                        '--output', output_dir,
                        '--projectname', f'test.{dir_name}']
            assert xregistry.cli() == 0
            # run dotnet build on the csproj here that references the generated files already
            assert subprocess.check_call(['dotnet', 'build'], cwd=output_dir, stdout=sys.stdout, stderr=sys.stderr) == 0
            
#@pytest.mark.skip(reason="temporarily disabled")    
def test_codegen_py():
    input_dir = os.path.join(project_root, 'xregistry/templates/py'.replace('/', os.path.sep))
    # loop through all dirs in the input directory that have no leading underscore in their name
    for dir_name in os.listdir(input_dir):
        if os.path.exists(os.path.join(project_root, f'tmp/test/py/{dir_name}/'.replace('/', os.path.sep))):
            shutil.rmtree(os.path.join(project_root, f'tmp/test/py/{dir_name}/'.replace('/', os.path.sep)))
        output_dir = os.path.join(project_root, f'tmp/test/py/{dir_name}'.replace('/', os.path.sep))
        if not dir_name.startswith('_') and os.path.isdir(os.path.join(input_dir, dir_name)):
            # generate the code for each directory
            sys.argv = ['xregistry', 'generate',  
                        '--style', dir_name, 
                        '--language', 'py',
                        '--definitions', os.path.join(project_root, 'samples/message-definitions/contoso-erp.xreg.json'.replace('/', os.path.sep)),
                        '--output', output_dir,
                        '--projectname', f'test.{dir_name}']
            assert xregistry.cli() == 0
            
    