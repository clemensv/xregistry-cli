import random
import string
import sys
import os
import subprocess
import shutil
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root))

import ceregistry

# this test invokes the ceregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both
def run_test():
    # clean the output directory
    if os.path.exists(os.path.join(project_root, 'tmp/test/cs/amqp_end_to_end/')):
        shutil.rmtree(os.path.join(project_root, 'tmp/test/cs/amqp_end_to_end/'))
    # generate the producer
    sys.argv = ['ceregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'amqp_end_to_end.cereg'),
                '--output', os.path.join(project_root, 'tmp/test/cs/amqp_end_to_end/producer/'),
                '--projectname', 'Contoso.ERP.Producer']
    ceregistry.cli()
    # generate the consumer
    sys.argv = [ 'ceregistry', 'generate',  
                '--style', 'consumer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'amqp_end_to_end.cereg'),
                '--output', os.path.join(project_root, 'tmp/test/cs/amqp_end_to_end/consumer/'),
                '--projectname', 'Contoso.ERP.Consumer']
    ceregistry.cli()
    # run dotnet build on the csproj here that references the generated files already
    subprocess.check_call(['dotnet', 'run'], cwd=os.path.dirname(__file__), stdout=sys.stdout, stderr=sys.stderr)
    
def test_amqp_end_to_end():
    container_name = ''.join(random.choices(string.ascii_lowercase, k=10))
    start_command = "docker run --name {} -d -p 127.11.0.2:5672:5672 -e AMQ_USER=test -e AMQ_PASSWORD=password quay.io/artemiscloud/activemq-artemis-broker".\
                      format(container_name)
    subprocess.run(start_command, shell=True, check=True, stdout=sys.stdout, stderr=sys.stderr)
    # give the broker a chance to start. wait 20 seconds
    time.sleep(15)
    try:
        run_test()
    finally:
        stop_command = "docker stop {}".format(container_name)
        subprocess.run(stop_command, shell=True, check=True, stdout=sys.stdout, stderr=sys.stderr)
        delete_command = "docker rm {}".format(container_name)
        subprocess.run(delete_command, shell=True, check=True, stdout=sys.stdout, stderr=sys.stderr)