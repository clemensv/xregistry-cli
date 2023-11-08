import random
import string
import sys
import os
import subprocess
import shutil
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root))

import xregistry

# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def run_test():
    # clean the output directory
    if os.path.exists(os.path.join(project_root, 'tmp/test/cs/mqtt_end_to_end/')):
        shutil.rmtree(os.path.join(project_root, 'tmp/test/cs/mqtt_end_to_end/'))
    # generate the producer
    sys.argv = ['xregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'mqtt_end_to_end.cereg'),
                '--output', os.path.join(project_root, 'tmp/test/cs/mqtt_end_to_end/producer/'),
                '--projectname', 'Contoso.ERP.Producer']
    xregistry.cli()
    # generate the consumer
    sys.argv = [ 'xregistry', 'generate', 
                '--style', 'consumer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'mqtt_end_to_end.cereg'),
                '--output', os.path.join(project_root, 'tmp/test/cs/mqtt_end_to_end/consumer/'),
                '--projectname', 'Contoso.ERP.Consumer']
    xregistry.cli()
    # run dotnet build on the csproj here that references the generated files already
    subprocess.check_call(['dotnet', 'run'], cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr)
    
def test_mqtt_end_to_end():
    container_name = ''.join(random.choices(string.ascii_lowercase, k=10))
    start_command = "docker run --name {} -p 127.11.0.1:1883:1883 -v {}:/mosquitto/config/ -v {}:/mosquitto/log -d eclipse-mosquitto".\
                          format(container_name, os.path.join(os.path.dirname(__file__), 'mosquitto', 'config'), os.path.join(os.path.dirname(__file__), 'mosquitto', 'logs'))
    subprocess.run(start_command, shell=True, check=True)
    # give the broker a chance to start. wait 20 seconds
    time.sleep(30)
    
    try:
        run_test()
    finally:
        stop_command = "docker stop {}".format(container_name)
        subprocess.run(stop_command, shell=True, check=True)
        delete_command = "docker rm {}".format(container_name)
        subprocess.run(delete_command, shell=True, check=True)