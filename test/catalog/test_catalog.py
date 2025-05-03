import os
import sys
import time
import pytest
import json
import requests

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

from xregistry.commands.catalog import CatalogSubcommands
# pylint: disable=import-error
# mypy: ignore-errors
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
# pylint: enable=import-error
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


CATALOG_PORT = 8080
CATALOG_URL = "http://localhost:8080"
IMAGE_NAME = "ghcr.io/xregistry/xrserver-all:latest" # Corrected image name
CONTAINER_NAME = "xregistry-catalog-test"
STARTUP_TIMEOUT = 180 # Increased timeout

@pytest.fixture(scope="module")
def catalog_container():
    with DockerContainer(IMAGE_NAME) \
        .with_command("--recreatedb") \
        .with_bind_ports(CATALOG_PORT, CATALOG_PORT) as container:
        wait_for_logs(container, "/xrserver")
        # wait for the server to be available
        timeout = time.time() + STARTUP_TIMEOUT
        while True:
            try:
                response = requests.get(CATALOG_URL)
                if response.status_code == 200:
                    break
            except Exception:
                pass
            if time.time() > timeout:
                raise Exception("Catalog container did not start in time: HTTP service not available on port 8080")
            time.sleep(1)
        # load /xregistry/schemas/_model.json, GET /model from the server, merge the local model with the remote model, and PUT the merged model back to the server
        local_model_path = os.path.join(project_root, "xregistry", "schemas", "_model.json")
        with open(local_model_path, "r") as local_model_file:
            local_model = json.load(local_model_file)
        remote_model = None
        try:
            # Fetch the current model from the catalog
            get_response = requests.get(f"{CATALOG_URL}/model")
            get_response.raise_for_status()
            remote_model = get_response.json()

            # Merge the remote model with the local model (local takes precedence)
            merged_model = {**remote_model, **local_model}

            # Update the catalog with the merged model via PUT
            put_response = requests.put(f"{CATALOG_URL}/model", json=merged_model)
            put_response.raise_for_status()
            print("Model merged and updated successfully.")
        except Exception as e:
            print(f"Error during model merge: {e}")
            # Try to get logs if container exists
            if container:
                try:
                    logs = container.get_logs()
                    print("Container logs:\n", logs[0].decode() if logs[0] else "", logs[1].decode() if logs[1] else "")
                except Exception as log_e:
                    print(f"Could not retrieve container logs: {log_e}")
            pytest.fail(f"Failed to start catalog container: {e}")
        
        yield container


""" this file tests the catalog subcommands in #file: """

@pytest.mark.usefixtures("catalog_container")
def test_catalog_endpoint_operations():
    # Add endpoint via CLI
    add_endpoint_args = [
        'xregistry',
        'catalog',
        'endpoint',
        'add',
        '--catalog', 'http://localhost:8080',
        '--endpointid', 'test-endpoint',
        '--usage', 'producer',
        '--protocol', 'AMQP/1.0',
        '--endpoints', 'amqp://localhost:5672',
        '--messagegroups', 'test-group',
        '--description', 'Test endpoint',
        '--documentation', 'http://docs',
        '--labels', 'env=test', # key=value format for labels
        '--name', 'Test Endpoint'
    ]
    with patch.object(sys, 'argv', add_endpoint_args):
        result = cli()
        assert result == 0

    # Verify endpoint was added
    response = requests.get("http://localhost:8080/endpoints/test-endpoint")
    assert response.status_code == 200
    endpoint = response.json()
    assert endpoint["endpointid"] == "test-endpoint"
    assert endpoint["usage"] == "producer"
    assert endpoint["protocol"] == "AMQP/1.0"
    # protocoloptions should include endpoints and other options
    proto_opts = endpoint["protocoloptions"]
    assert proto_opts["endpoints"] == [{"url": "amqp://localhost:5672"}]
    assert endpoint["messagegroups"] == ["test-group"]
    assert endpoint["description"] == "Test endpoint"
    assert endpoint["documentation"] == "http://docs"
    assert endpoint["labels"] == {"env": "test"}
    assert endpoint["name"] == "Test Endpoint"

    # Edit endpoint via CLI
    edit_endpoint_args = [
        'xregistry',
        'catalog',
        'endpoint',
        'edit',
        '--catalog', 'http://localhost:8080',
        '--endpointid', 'test-endpoint',
        '--description', 'Updated endpoint',
        '--labels', 'env=prod' # key=value format for labels
    ]
    with patch.object(sys, 'argv', edit_endpoint_args):
        result = cli()
        assert result == 0

    # Verify endpoint was updated
    response = requests.get("http://localhost:8080/endpoints/test-endpoint")
    assert response.status_code == 200
    endpoint = response.json()
    assert endpoint["description"] == "Updated endpoint"
    assert endpoint["labels"]["env"] == "prod"

    # Add message group via CLI
    add_group_args = [
        'xregistry',
        'catalog',
        'messagegroup',
        'add',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'test-group',
        '--envelope', 'CloudEvents/1.0',
        '--protocol', 'amqp',
        '--description', 'Test message group',
        '--documentation', 'http://docs',
        '--labels', 'env=test', # key=value format for labels
        '--name', 'Test Group'
    ]
    with patch.object(sys, 'argv', add_group_args):
        result = cli()
        assert result == 0

    # Verify message group was added
    response = requests.get("http://localhost:8080/messagegroups/test-group")
    assert response.status_code == 200
    group = response.json()
    assert group["messagegroupid"] == "test-group"
    assert group["envelope"] == "CloudEvents/1.0"
    assert group["protocol"] == "amqp"

    # Add message to group via CLI
    add_message_args = [
        'xregistry',
        'catalog',
        'message',
        'add',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'test-group',
        '--messageid', 'test-message',
        '--envelope', 'CloudEvents/1.0',
        '--protocol', 'AMQP/1.0',
        '--description', 'Test message',
        '--documentation', 'http://docs',
        '--labels', 'type=event', # key=value format for labels
        '--name', 'Test Message'
    ]
    with patch.object(sys, 'argv', add_message_args):
        result = cli()
        assert result == 0

    # Verify message was added
    response = requests.get("http://localhost:8080/messagegroups/test-group/messages/test-message")
    assert response.status_code == 200
    message = response.json()
    assert message["messageid"] == "test-message"
    assert message["envelope"] == "CloudEvents/1.0"

    # Add schema group via CLI
    add_schemagroup_args = [
        'xregistry',
        'catalog',
        'schemagroup',
        'add',
        '--catalog', 'http://localhost:8080',
        '--schemagroupid', 'test-schemas',
        '--format', 'avro',
        '--description', 'Test schema group',
        '--documentation', 'http://docs',
        '--labels', 'type=schemas', # key=value format for labels
        '--name', 'Test Schemas'
    ]
    with patch.object(sys, 'argv', add_schemagroup_args):
        result = cli()
        assert result == 0

    # Verify schema group was added
    response = requests.get("http://localhost:8080/schemagroups/test-schemas")
    assert response.status_code == 200
    schemas = response.json()
    assert schemas["schemagroupid"] == "test-schemas"

    # Add schema version via CLI
    add_schemaversion_args = [
        'xregistry',
        'catalog',
        'schemaversion',
        'add',
        '--catalog', 'http://localhost:8080',
        '--schemagroupid', 'test-schemas',
        '--schemaid', 'test-schema',
        '--format', 'avro',
        '--schema', '{\"type\": \"string\"}', # JSON string for schema
        '--versionid', '1.0',
        '--description', 'Test schema',
        '--documentation', 'http://docs',
        '--labels', 'type=schema', # key=value format for labels
        '--name', 'Test Schema'
    ]
    with patch.object(sys, 'argv', add_schemaversion_args):
        result = cli()
        assert result == 0

    # Verify schema was added
    response = requests.get("http://localhost:8080/schemagroups/test-schemas?inline=schemas,schemas.versions,schemas.versions.schema")
    assert response.status_code == 200
    schemas = response.json()
    assert "test-schema" in schemas["schemas"]
    assert schemas["schemas"]["test-schema"]["versions"]["1.0"]["schema"]["type"] == "string"

    # Clean up via CLI
    remove_schemaversion_args = [
        'xregistry',
        'catalog',
        'schemaversion',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--schemagroupid', 'test-schemas',
        '--schemaid', 'test-schema',
        '--versionid', '1.0'
    ]
    with patch.object(sys, 'argv', remove_schemaversion_args):
        cli() # Ignore result for cleanup

    remove_schemagroup_args = [
        'xregistry',
        'catalog',
        'schemagroup',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--schemagroupid', 'test-schemas'
    ]
    with patch.object(sys, 'argv', remove_schemagroup_args):
        cli() # Ignore result for cleanup

    remove_message_args = [
        'xregistry',
        'catalog',
        'message',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'test-group',
        '--messageid', 'test-message'
    ]
    with patch.object(sys, 'argv', remove_message_args):
        cli() # Ignore result for cleanup

    remove_messagegroup_args = [
        'xregistry',
        'catalog',
        'messagegroup',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--messagegroupid', 'test-group'
    ]
    with patch.object(sys, 'argv', remove_messagegroup_args):
        cli() # Ignore result for cleanup

    remove_endpoint_args = [
        'xregistry',
        'catalog',
        'endpoint',
        'remove',
        '--catalog', 'http://localhost:8080',
        '--endpointid', 'test-endpoint'
    ]
    with patch.object(sys, 'argv', remove_endpoint_args):
        cli() # Ignore result for cleanup

    # Verify cleanup
    response = requests.get("http://localhost:8080/endpoints/test-endpoint")
    assert response.status_code == 404
    response = requests.get("http://localhost:8080/messagegroups/test-group")
    assert response.status_code == 404
    response = requests.get("http://localhost:8080/schemagroups/test-schemas")
    assert response.status_code == 404

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
        'schemaversion',
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
        'schemaversion',
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
