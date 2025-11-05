"""
Integration-tests for the model-driven catalog CLI.

All original scenarios preserved; flags adapted to the new structure:
  • protocol choices = slug (amqp10, http, …)
  • endpoints array  = --protocoloptions-endpoints url=…
  • envelope slug    = cloudevents10
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from xregistry.cli import main as cli

# --------------------------------------------------------------------------- #
# constants / tracing                                                         #
# --------------------------------------------------------------------------- #

CATALOG_PORT = 3900
CATALOG_URL = "http://localhost:3900"
IMAGE_NAME = "ghcr.io/xregistry/xrserver-all:latest"
STARTUP_TIMEOUT = 180

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("http.client").setLevel(logging.DEBUG)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))


# --------------------------------------------------------------------------- #
# fixture: launch real xrserver in Docker                                     #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def catalog_container():
    with DockerContainer(IMAGE_NAME) \
        .with_command("--recreatedb") \
        .with_bind_ports(CATALOG_PORT, 8080) as container:
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
                raise Exception(f"Catalog container did not start in time: HTTP service not available on port {CATALOG_PORT}")
            time.sleep(1)
        # load /xregistry/schemas/model.json (full model with group definitions), GET /modelsource from the server, merge the local model with the remote model, and PUT the merged model back to the server
        local_model_path = os.path.join(project_root, "xregistry", "schemas", "model.json")
        with open(local_model_path, "r") as local_model_file:
            local_model = json.load(local_model_file)
        remote_model = None
        try:
            # Fetch the current model from the catalog
            get_response = requests.get(f"{CATALOG_URL}/modelsource")
            get_response.raise_for_status()
            remote_model = get_response.json()

            # Merge the remote model with the local model (local takes precedence)
            merged_model = {**remote_model, **local_model}

            # Update the catalog with the merged model via PUT
            put_response = requests.put(f"{CATALOG_URL}/modelsource", json=merged_model)
            if put_response.status_code != 200:
                print(f"PUT /model failed with status {put_response.status_code}")
                print(f"Response body: {put_response.text}")
            put_response.raise_for_status()
            print("Model merged and updated successfully.")
        except Exception as e:
            print(f"Error during model merge: {e}")
            # Print response details if available
            if 'put_response' in locals():
                print(f"Response status: {put_response.status_code}")
                print(f"Response body: {put_response.text}")
            # Try to get logs if container exists
            if container:
                try:
                    logs = container.get_logs()
                    print("Container logs:\n", logs[0].decode() if logs[0] else "", logs[1].decode() if logs[1] else "")
                except Exception as log_e:
                    print(f"Could not retrieve container logs: {log_e}")
            pytest.fail(f"Failed to start catalog container: {e}")
        
        yield container


# --------------------------------------------------------------------------- #
# helper to run CLI silently                                                  #
# --------------------------------------------------------------------------- #

def _run(argv: list[str], expect: int = 0) -> None:
    with patch.object(sys, "argv", argv):
        assert cli() == expect

# --------------------------------------------------------------------------- #
# 1. full CRUD covering endpoint → msg-group/msg → schema-group/schema/vers.  #
# --------------------------------------------------------------------------- #

# ─────────── full CRUD workflow ───────────
@pytest.mark.usefixtures("catalog_container")
def test_full_workflow():
    # endpoint -------------------------------------------------------------
    _run([
        "xregistry", "catalog", "endpoint", "add",
        "--catalog", CATALOG_URL,
        "--endpointid", "e1",
        "--usage", "producer",
        "--protocol", "amqp10",
        "--protocoloptions-endpoints", "url=amqp://broker:5672",
    ])
    ep = requests.get(f"{CATALOG_URL}/endpoints/e1").json()
    assert ep["protocoloptions"]["endpoints"][0]["url"] == "amqp://broker:5672"

    # message group --------------------------------------------------------
    _run([
        "xregistry", "catalog", "messagegroup", "add",
        "--catalog", CATALOG_URL,
        "--messagegroupid", "mg1",
        "--envelope", "cloudevents10",
        "--protocol", "amqp10",
    ])

    # message --------------------------------------------------------------
    _run([
        "xregistry", "catalog", "messagegroup", "message", "add",
        "--catalog", CATALOG_URL,
        "--messagegroupid", "mg1",
        "--messageid", "m1",
        "--envelope", "cloudevents10",
        "--protocol", "amqp10",
    ])
    assert requests.get(
        f"{CATALOG_URL}/messagegroups/mg1/messages/m1"
    ).status_code == 200

    # schemagroup ----------------------------------------------------------
    _run([
        "xregistry", "catalog", "schemagroup", "add",
        "--catalog", CATALOG_URL,
        "--schemagroupid", "sg1",
        "--format", "avro",
    ])

    # schema (+ version) ---------------------------------------------------
    _run([
        "xregistry", "catalog", "schemagroup", "schema", "add",
        "--catalog", CATALOG_URL,
        "--schemagroupid", "sg1",
        "--schemaid", "s1",
        "--versionid", "1.0",
        "--format", "avro",
        "--schema", '{"type":"string"}',
    ])
    assert "s1" in requests.get(
        f"{CATALOG_URL}/schemagroups/sg1?inline=schemas"
    ).json()["schemas"]

    # ---------- cleanup (reverse order) ----------------------------------
    _run(["xregistry", "catalog", "schemagroup", "schema", "remove",
          "--catalog", CATALOG_URL,
          "--schemagroupid", "sg1",
          "--schemaid", "s1",
          "--versionid", "1.0"])
    _run(["xregistry", "catalog", "schemagroup", "remove",
          "--catalog", CATALOG_URL,
          "--schemagroupid", "sg1"])
    _run(["xregistry", "catalog", "messagegroup", "message", "remove",
          "--catalog", CATALOG_URL,
          "--messagegroupid", "mg1",
          "--messageid", "m1"])
    _run(["xregistry", "catalog", "messagegroup", "remove",
          "--catalog", CATALOG_URL,
          "--messagegroupid", "mg1"])
    _run(["xregistry", "catalog", "endpoint", "remove",
          "--catalog", CATALOG_URL,
          "--endpointid", "e1"])

    # objects gone?
    assert requests.get(f"{CATALOG_URL}/endpoints/e1").status_code == 404
    assert requests.get(f"{CATALOG_URL}/messagegroups/mg1").status_code == 404
    assert requests.get(f"{CATALOG_URL}/schemagroups/sg1").status_code == 404

# ─────────── smoke tests ───────────
@pytest.mark.usefixtures("catalog_container")
def test_smoke_endpoint():
    _run(["xregistry", "catalog", "endpoint", "add",
          "--catalog", CATALOG_URL,
          "--endpointid", "quick-ep",
          "--usage", "consumer",
          "--protocol", "http",
          "--protocoloptions-endpoints", "url=http://svc"])
    _run(["xregistry", "catalog", "endpoint", "remove",
          "--catalog", CATALOG_URL, "--endpointid", "quick-ep"])
    assert requests.get(f"{CATALOG_URL}/endpoints/quick-ep").status_code == 404

@pytest.mark.usefixtures("catalog_container")
def test_smoke_messagegroup_and_message():
    _run(["xregistry", "catalog", "messagegroup", "add",
          "--catalog", CATALOG_URL,
          "--messagegroupid", "quick-mg",
          "--envelope", "cloudevents10",
          "--protocol", "kafka"])
    _run(["xregistry", "catalog", "messagegroup", "message", "add",
          "--catalog", CATALOG_URL,
          "--messagegroupid", "quick-mg",
          "--messageid", "quick-msg",
          "--envelope", "cloudevents10",
          "--protocol", "kafka"])
    _run(["xregistry", "catalog", "messagegroup", "message", "remove",
          "--catalog", CATALOG_URL,
          "--messagegroupid", "quick-mg",
          "--messageid", "quick-msg"])
    _run(["xregistry", "catalog", "messagegroup", "remove",
          "--catalog", CATALOG_URL,
          "--messagegroupid", "quick-mg"])
    assert requests.get(f"{CATALOG_URL}/messagegroups/quick-mg").status_code == 404

@pytest.mark.usefixtures("catalog_container")
def test_smoke_schema():
    _run(["xregistry", "catalog", "schemagroup", "add",
          "--catalog", CATALOG_URL,
          "--schemagroupid", "quick-sg"])
    _run(["xregistry", "catalog", "schemagroup", "schema", "add",
          "--catalog", CATALOG_URL,
          "--schemagroupid", "quick-sg",
          "--schemaid", "quick-schema",
          "--versionid", "1",
          "--format", "avro",
          "--schema", '{"type":"int"}'])
    _run(["xregistry", "catalog", "schemagroup", "schema", "remove",
          "--catalog", CATALOG_URL,
          "--schemagroupid", "quick-sg",
          "--schemaid", "quick-schema",
          "--versionid", "1"])
    _run(["xregistry", "catalog", "schemagroup", "remove",
          "--catalog", CATALOG_URL,
          "--schemagroupid", "quick-sg"])
    assert requests.get(f"{CATALOG_URL}/schemagroups/quick-sg").status_code == 404
    


@pytest.fixture
def manifest_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "manifest.json"
    # initialize with an empty manifest structure
    file_path.write_text(json.dumps({}))
    return file_path


def test_full_workflow_manifest(manifest_file: Path) -> None:
    # endpoint addition
    _run([
        "xregistry", "manifest", "endpoint", "add",
        "--catalog", str(manifest_file),
        "--endpointid", "e1",
        "--usage", "producer",
        "--protocol", "amqp10",
        "--protocoloptions-endpoints", "url=amqp://broker:5672",
    ])
    data = json.loads(manifest_file.read_text())
    assert data.get("endpoints", {}).get("e1", {}) \
        .get("protocoloptions", {}) \
        .get("endpoints", [])[0]["url"] == "amqp://broker:5672"

    # message group addition
    _run([
        "xregistry", "manifest", "messagegroup", "add",
        "--catalog", str(manifest_file),
        "--messagegroupid", "mg1",
        "--envelope", "cloudevents10",
        "--protocol", "amqp10",
    ])

    # message addition
    _run([
        "xregistry", "manifest", "messagegroup", "message", "add",
        "--catalog", str(manifest_file),
        "--messagegroupid", "mg1",
        "--messageid", "m1",
        "--envelope", "cloudevents10",
        "--protocol", "amqp10",
    ])
    data = json.loads(manifest_file.read_text())
    assert "m1" in data.get("messagegroups", {}).get("mg1", {}) \
        .get("messages", {})

    # schemagroup addition
    _run([
        "xregistry", "manifest", "schemagroup", "add",
        "--catalog", str(manifest_file),
        "--schemagroupid", "sg1",
        "--format", "avro",
    ])

    # schema (and version) addition
    _run([
        "xregistry", "manifest", "schemagroup", "schema", "add",
        "--catalog", str(manifest_file),
        "--schemagroupid", "sg1",
        "--schemaid", "s1",
        "--versionid", "1.0",
        "--format", "avro",
        "--schema", '{"type":"string"}',
    ])
    data = json.loads(manifest_file.read_text())
    assert "s1" in data.get("schemagroups", {}).get("sg1", {}) \
        .get("schemas", {})

    # Cleanup in reverse order
    _run([
        "xregistry", "manifest", "schemagroup", "schema", "remove",
        "--catalog", str(manifest_file),
        "--schemagroupid", "sg1",
        "--schemaid", "s1",
        "--versionid", "1.0",
    ])
    _run([
        "xregistry", "manifest", "schemagroup", "remove",
        "--catalog", str(manifest_file),
        "--schemagroupid", "sg1",
    ])
    _run([
        "xregistry", "manifest", "messagegroup", "message", "remove",
        "--catalog", str(manifest_file),
        "--messagegroupid", "mg1",
        "--messageid", "m1",
    ])
    _run([
        "xregistry", "manifest", "messagegroup", "remove",
        "--catalog", str(manifest_file),
        "--messagegroupid", "mg1",
    ])
    _run([
        "xregistry", "manifest", "endpoint", "remove",
        "--catalog", str(manifest_file),
        "--endpointid", "e1",
    ])
    data = json.loads(manifest_file.read_text())
    assert "e1" not in data.get("endpoints", {})
    assert "mg1" not in data.get("messagegroups", {})
    assert "sg1" not in data.get("schemagroups", {})


def test_smoke_endpoint_manifest(manifest_file: Path) -> None:
    _run([
        "xregistry", "manifest", "endpoint", "add",
        "--catalog", str(manifest_file),
        "--endpointid", "quick-ep",
        "--usage", "consumer",
        "--protocol", "http",
        "--protocoloptions-endpoints", "url=http://svc",
    ])
    _run([
        "xregistry", "manifest", "endpoint", "remove",
        "--catalog", str(manifest_file),
        "--endpointid", "quick-ep",
    ])
    data = json.loads(manifest_file.read_text())
    assert "quick-ep" not in data.get("endpoints", {})


def test_smoke_messagegroup_and_message_manifest(manifest_file: Path) -> None:
    _run([
        "xregistry", "manifest", "messagegroup", "add",
        "--catalog", str(manifest_file),
        "--messagegroupid", "quick-mg",
        "--envelope", "cloudevents10",
        "--protocol", "kafka",
    ])
    _run([
        "xregistry", "manifest", "messagegroup", "message", "add",
        "--catalog", str(manifest_file),
        "--messagegroupid", "quick-mg",
        "--messageid", "quick-msg",
        "--envelope", "cloudevents10",
        "--protocol", "kafka",
    ])
    _run([
        "xregistry", "manifest", "messagegroup", "message", "remove",
        "--catalog", str(manifest_file),
        "--messagegroupid", "quick-mg",
        "--messageid", "quick-msg",
    ])
    _run([
        "xregistry", "manifest", "messagegroup", "remove",
        "--catalog", str(manifest_file),
        "--messagegroupid", "quick-mg",
    ])
    data = json.loads(manifest_file.read_text())
    assert "quick-mg" not in data.get("messagegroups", {})


def test_smoke_schema_manifest(manifest_file: Path) -> None:
    _run([
        "xregistry", "manifest", "schemagroup", "add",
        "--catalog", str(manifest_file),
        "--schemagroupid", "quick-sg",
    ])
    _run([
        "xregistry", "manifest", "schemagroup", "schema", "add",
        "--catalog", str(manifest_file),
        "--schemagroupid", "quick-sg",
        "--schemaid", "quick-schema",
        "--versionid", "1",
        "--format", "avro",
        "--schema", '{"type":"int"}',
    ])
    _run([
        "xregistry", "manifest", "schemagroup", "schema", "remove",
        "--catalog", str(manifest_file),
        "--schemagroupid", "quick-sg",
        "--schemaid", "quick-schema",
        "--versionid", "1",
    ])
    _run([
        "xregistry", "manifest", "schemagroup", "remove",
        "--catalog", str(manifest_file),
        "--schemagroupid", "quick-sg",
    ])
    data = json.loads(manifest_file.read_text())
    assert "quick-sg" not in data.get("schemagroups", {})