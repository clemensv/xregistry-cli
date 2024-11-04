import os
import sys
import pytest
import json
import requests

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

from xregistry.commands.catalog import CatalogSubcommands
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import logging
import os
import sys
import pytest
import requests
from unittest.mock import patch
from xregistry.cli import main as cli 

# Enable HTTP request tracing
logging.basicConfig(level=logging.DEBUG)
http_client_logger = logging.getLogger("http.client")
http_client_logger.setLevel(logging.DEBUG)
http_client_logger.propagate = True
# log to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


@pytest.fixture(scope="module")
def catalog_container():
    with DockerContainer("duglin/xreg-server-all") \
        .with_bind_ports(8080, 8080) as container:
        wait_for_logs(container, "Listening on 8080")
        yield container

""" this file tests the catalog subcommands in #file: """

@pytest.mark.usefixtures("catalog_container")
def test_catalog_endpoint_operations():
    catalog = CatalogSubcommands("http://localhost:8080")
    
    # Add endpoint
    catalog.add_endpoint(
        "test-endpoint",
        "producer", 
        "AMQP/1.0",
        endpoints=["amqp://localhost:5672"],
        options={"key": "value"},
        messagegroups=["test-group"],
        description="Test endpoint",
        documentation="http://docs",
        labels={"env": "test"},
        name="Test Endpoint"
    )

    # Verify endpoint was added
    response = requests.get("http://localhost:8080/endpoints/test-endpoint")
    assert response.status_code == 200
    endpoint = response.json()
    assert endpoint["endpointid"] == "test-endpoint"
    assert endpoint["usage"] == "producer"
    assert endpoint["protocol"] == "AMQP/1.0"

    # Edit endpoint
    catalog.edit_endpoint(
        "test-endpoint",
        description="Updated endpoint",
        labels={"env": "prod"}
    )

    # Verify endpoint was updated
    response = requests.get("http://localhost:8080/endpoints/test-endpoint")
    assert response.status_code == 200
    endpoint = response.json()
    assert endpoint["description"] == "Updated endpoint"
    assert endpoint["labels"]["env"] == "prod"

    # Add message group
    catalog.add_messagegroup(
        "test-group",
        "CloudEvents/1.0",
        "amqp",
        description="Test message group",
        documentation="http://docs",
        labels={"env": "test"},
        name="Test Group"
    )

    # Verify message group was added
    response = requests.get("http://localhost:8080/messagegroups/test-group")
    assert response.status_code == 200
    group = response.json()
    assert group["messagegroupid"] == "test-group"
    assert group["envelope"] == "CloudEvents/1.0"

    # Add message to group
    catalog.add_message(
        "test-group",
        "test-message",
        "CloudEvents/1.0",
        "AMQP/1.0",
        description="Test message",
        documentation="http://docs",
        labels={"type": "event"},
        name="Test Message"
    )

    # Verify message was added
    response = requests.get("http://localhost:8080/messagegroups/test-group/messages/test-message") 
    assert response.status_code == 200
    message = response.json()
    assert message["messageid"] == "test-message"
    assert message["envelope"] == "CloudEvents/1.0"

    # Add schema group
    catalog.add_schemagroup(
        "test-schemas",
        "avro",
        description="Test schema group",
        documentation="http://docs",
        labels={"type": "schemas"},
        name="Test Schemas"
    )

    # Verify schema group was added
    response = requests.get("http://localhost:8080/schemagroups/test-schemas")
    assert response.status_code == 200
    schemas = response.json()
    assert schemas["schemagroupid"] == "test-schemas"

    # Add schema version
    catalog.add_schemaversion(
        "test-schemas",
        "test-schema",
        "avro",
        schema='{"type": "string"}',
        versionid="1.0",
        description="Test schema",
        documentation="http://docs",
        labels={"type": "schema"},
        name="Test Schema"
    )

    # Verify schema was added
    response = requests.get("http://localhost:8080/schemagroups/test-schemas?inline=schemas,schemas.versions,schemas.versions.schema") 
    assert response.status_code == 200
    schemas = response.json()
    assert "test-schema" in schemas["schemas"]
    assert schemas["schemas"]["test-schema"]["versions"]["1.0"]["schema"]["type"] == "string"

    # Clean up
    catalog.remove_schemagroup("test-schemas")
    catalog.remove_messagegroup("test-group") 
    catalog.remove_endpoint("test-endpoint")

    # Verify cleanup
    response = requests.get("http://localhost:8080/endpoints/test-endpoint")
    assert response.status_code == 404
    response = requests.get("http://localhost:8080/messagegroups/test-group")
    assert response.status_code == 404
    response = requests.get("http://localhost:8080/schemagroups/test-schemas")
    assert response.status_code == 404
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    sys.path.append(os.path.join(project_root))


@pytest.mark.usefixtures("catalog_container")
def test_cli_add_endpoint():
    test_args = [
        'xregistry',
        'catalog',
        'endpoint',
        'add',
        '--catalog', 'http://localhost:8080',
        '--endpointid', 'cli-endpoint',
        '--usage', 'producer',
        '--protocol', 'AMQP/1.0',
        '--endpoints', 'amqp://localhost:5672',
        '--description', '"CLI Test endpoint"',
    ]
    with patch.object(sys, 'argv', test_args):
        result = cli()
        assert result == 0

    response = requests.get('http://localhost:8080/endpoints/cli-endpoint')
    assert response.status_code == 200
    endpoint = response.json()
    assert endpoint['endpointid'] == 'cli-endpoint'
    assert endpoint['usage'] == 'producer'
    assert endpoint['protocol'] == 'AMQP/1.0'

    test_args = [
        'xregistry',
        'catalog',
        'endpoint',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--endpointid', 'cli-endpoint',
    ]
    with patch.object(sys, 'argv', test_args):
        result = cli()
        assert result == 0

    response = requests.get('http://localhost:8080/endpoints/cli-endpoint')
    assert response.status_code == 404

@pytest.mark.usefixtures("catalog_container")
def test_cli_add_messagegroup():
    test_args = [
        'xregistry',
        'catalog',
        'messagegroup',
        'add',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'cli-messagegroup',
        '--envelope', 'CloudEvents/1.0',
        '--protocol', 'AMQP/1.0',
        '--description', '"CLI Test message group"',
    ]
    with patch.object(sys, 'argv', test_args):
        result = cli()
        assert result == 0

    response = requests.get('http://localhost:8080/messagegroups/cli-messagegroup')
    assert response.status_code == 200
    group = response.json()
    assert group['messagegroupid'] == 'cli-messagegroup'
    assert group['envelope'] == 'CloudEvents/1.0'

    test_args = [
        'xregistry',
        'catalog',
        'messagegroup',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'cli-messagegroup',
    ]
    with patch.object(sys, 'argv', test_args):
        result = cli()
        assert result == 0

    response = requests.get('http://localhost:8080/messagegroups/cli-messagegroup')
    assert response.status_code == 404

@pytest.mark.usefixtures("catalog_container")
def test_cli_add_message():
    test_args = [
        'xregistry',
        'catalog',
        'messagegroup',
        'add',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'cli-messagegroup',
        '--envelope', 'CloudEvents/1.0',
        '--protocol', 'AMQP/1.0',
    ]
    with patch.object(sys, 'argv', test_args):
        cli()

    test_args = [
        'xregistry',
        'catalog',
        'message',
        'add',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'cli-messagegroup',
        '--messageid', 'cli-message',
        '--envelope', 'CloudEvents/1.0',
        '--protocol', 'AMQP/1.0',
        '--description', '"CLI Test message"',
    ]
    with patch.object(sys, 'argv', test_args):
        result = cli()
        assert result == 0

    response = requests.get('http://localhost:8080/messagegroups/cli-messagegroup/messages/cli-message')
    assert response.status_code == 200
    message = response.json()
    assert message['messageid'] == 'cli-message'
    assert message['envelope'] == 'CloudEvents/1.0'

    test_args = [
        'xregistry',
        'catalog',
        'message',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'cli-messagegroup',
        '--messageid', 'cli-message',
    ]
    with patch.object(sys, 'argv', test_args):
        cli()

    test_args = [
        'xregistry',
        'catalog',
        'messagegroup',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'cli-messagegroup',
    ]
    with patch.object(sys, 'argv', test_args):
        cli()

    response = requests.get('http://localhost:8080/messagegroups/cli-messagegroup')
    assert response.status_code == 404

@pytest.mark.usefixtures("catalog_container")
def test_cli_add_schemagroup_and_schema():
    test_args = [
        'xregistry',
        'catalog',
        'schemagroup',
        'add',
        '--catalog', 'http://localhost:8080',
        '--schemagroupid', 'cli-schemagroup',
        '--format', 'avro',
        '--description', '"CLI Test schema group"',
    ]
    with patch.object(sys, 'argv', test_args):
        result = cli()
        assert result == 0

    response = requests.get('http://localhost:8080/schemagroups/cli-schemagroup')
    assert response.status_code == 200
    schemagroup = response.json()
    assert schemagroup['schemagroupid'] == 'cli-schemagroup'

    test_args = [
        'xregistry',
        'catalog',
        'schema',
        'add',
        '--catalog', 'http://localhost:8080',
        '--schemagroupid', 'cli-schemagroup',
        '--schemaid', 'cli-schema',
        '--format', 'avro',
        '--versionid', '1.0',
        '--schema', '{"type": "string"}',
        '--description', 'CLI Test schema',
    ]
    with patch.object(sys, 'argv', test_args):
        result = cli()
        assert result == 0

    response = requests.get('http://localhost:8080/schemagroups/cli-schemagroup?inline=schemas,schemas.versions,schemas.versions.schema')
    assert response.status_code == 200
    schemas = response.json()
    assert 'cli-schema' in schemas['schemas']
    assert schemas['schemas']['cli-schema']['versions']['1.0']['schema']['type'] == 'string'

    test_args = [
        'xregistry',
        'catalog',
        'schema',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--schemagroupid', 'cli-schemagroup',
        '--schemaid', 'cli-schema',
        '--versionid', '1.0',
    ]
    with patch.object(sys, 'argv', test_args):
        cli()

    test_args = [
        'xregistry',
        'catalog',
        'schemagroup',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--schemagroupid', 'cli-schemagroup',
    ]
    with patch.object(sys, 'argv', test_args):
        cli()

    response = requests.get('http://localhost:8080/schemagroups/cli-schemagroup')
    assert response.status_code == 404
