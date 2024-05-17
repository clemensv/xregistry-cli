""" This test invokes the xregistry command line tool to generate a Python producer and a consumer for Kafka """


import random
import string
import sys
import os
import subprocess
import shutil
import time
import kafka
import pytest
from testcontainers.kafka import KafkaContainer

import xregistry

project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../..'.replace('/', os.path.sep)))
sys.path.append(os.path.join(project_root))


# this test invokes the xregistry command line tool to generate a C# proxy and a consumer
# and then builds the proxy and the consumer and runs a prepared test that integrates both

class TestPyKafkaEndToEnd:
    """ Test Kafka end to end """
    

    @pytest.fixture(scope="class", autouse=True)
    def kafka_container(self):
        """Kafka container fixture."""
        container = KafkaContainer()
        container.start()
        yield container
        container.stop()
    
    def test_kafka_end_to_end(self, kafka_container: KafkaContainer):
        """ Run test """
        if os.path.exists(os.path.join(project_root, 'tmp/test/py_kafka/'.replace('/', os.path.sep))):
            shutil.rmtree(os.path.join(
                project_root, 'tmp/test/py_kafka/'.replace('/', os.path.sep)), ignore_errors=True)
            
        output_path = os.path.join(project_root, 'tmp/test/py_kafka/'.replace('/', os.path.sep))
        # generate the producer
        sys.argv = ['xregistry', 'generate',
                    '--style', 'kafkaproducer',
                    '--language', 'py',
                    '--definitions', os.path.join(os.path.dirname(__file__), 'lightbulb.xreg.json'),
                    '--output', output_path,
                    '--projectname', 'kafka_producer']
        assert xregistry.cli() == 0
        # subprocess.check_call(['mvn', '--quiet', 'install'], cwd=os.path.join(project_root, 'tmp/test/java/mqtt_end_to_end/producer/'.replace('/', os.path.sep)), stdout=sys.stdout, stderr=sys.stderr)
        output_path += 'kafka_producer/'
        new_env = os.environ.copy()
        new_env['PYTHONPATH'] = output_path        
        assert subprocess.check_call(
                ['python', '-m', 'pylint', '-E', '.'], cwd=output_path, env=new_env, stdout=sys.stdout, stderr=sys.stderr, shell=True) == 0
        
        output_path = os.path.join(project_root, 'tmp/test/py_kafka/'.replace('/', os.path.sep))
        # generate the consumer
        sys.argv = ['xregistry', 'generate',
                    '--style', 'kafkaconsumer',
                    '--language', 'py',
                    '--definitions', os.path.join(os.path.dirname(__file__), 'lightbulb.xreg.json'),
                    '--output', output_path,
                    '--projectname', 'kafka_consumer']
        assert xregistry.cli() == 0
        output_path += 'kafka_consumer/'
        new_env = os.environ.copy()
        new_env['PYTHONPATH'] = output_path
        assert subprocess.check_call(
                ['python', '-m', 'pylint', '-E', '.'], cwd=output_path, env=new_env, stdout=sys.stdout, stderr=sys.stderr, shell=True) == 0
        
        # file copy py_kafka_end_to_end.py.txt to py_kafka_end_to_end.py in (project_root, 'tmp/test/py_kafka)
        shutil.copyfile(os.path.join(os.path.dirname(__file__), 'py_kafka_end_to_end.py.txt'),
                        os.path.join(project_root, 'tmp/test/py_kafka/py_kafka_end_to_end.py'))
        
        # pylint: disable=import-outside-toplevel
        from tmp.test.py_kafka.py_kafka_end_to_end import TestFabrikamLumenEvents
        
        test = TestFabrikamLumenEvents(kafka_container.get_bootstrap_server(), 'test-topic', 'mygroup')
        test.test_send_and_receive_events()
