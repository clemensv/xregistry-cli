# Known Test Issues

This document tracks tests that are temporarily skipped due to known issues.

## Catalog Tests (4 tests) - Infrastructure Issue

**Status:** Skipped  
**Issue:** xrserver container MySQL initialization hangs intermittently  
**Affected Tests:**
- `test/catalog/test_catalog.py::test_smoke_endpoint`
- `test/catalog/test_catalog.py::test_smoke_messagegroup_and_message`
- `test/catalog/test_catalog.py::test_smoke_schema`
- `test/catalog/test_catalog.py::test_full_workflow`

**Root Cause:** The `ghcr.io/xregistry/xrserver-all:latest` container has an intermittent issue where MySQL initialization hangs indefinitely showing "Waiting for mysql.........." When working correctly, the container starts in 20-30 seconds. When MySQL hangs, the container never becomes ready even after 90+ seconds.

**Resolution:** 
- Wait for upstream fix to xrserver container MySQL initialization
- Or consider using a different xrserver image
- Or mock the catalog server for testing

**Workaround:** Tests can be run locally when MySQL initializes properly.

---

## Python EventHubs Tests (8 tests) - pytest-asyncio Configuration Issue

**Status:** Skipped  
**Issue:** Generated tests fail with "async def functions are not natively supported"  
**Affected Tests:**
- `test/py/test_python.py::test_ehproducer_contoso_erp_py`
- `test/py/test_python.py::test_ehproducer_fabrikam_motorsports_py`
- `test/py/test_python.py::test_ehproducer_inkjet_py`
- `test/py/test_python.py::test_ehproducer_lightbulb_py`
- `test/py/test_python.py::test_ehconsumer_contoso_erp_py`
- `test/py/test_python.py::test_ehconsumer_fabrikam_motorsports_py`
- `test/py/test_python.py::test_ehconsumer_inkjet_py`
- `test/py/test_python.py::test_ehconsumer_lightbulb_py`

**Root Cause:** The generated `pyproject.toml` includes `pytest-asyncio` as a dependency and test functions use `@pytest.mark.asyncio` decorators, but the async fixture `event_hub_emulator` lacks proper configuration. Pytest gives the error: `'test_producer.py' requested an async fixture 'event_hub_emulator', with no plugin or hook that handled it.`

**Technical Details:**
- Template: `xregistry/templates/py/ehproducer/{testdir}test_producer.py.jinja` and `ehconsumer` variant
- The fixture at line 40-41 uses `@pytest.fixture(scope="module")` instead of `@pytest_asyncio.fixture`
- Alternative: Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` in `pyproject.toml.jinja`

**Resolution:** 
- Option 1: Change `@pytest.fixture` to `@pytest_asyncio.fixture` for async fixtures in templates
- Option 2: Add pytest configuration to `pyproject.toml.jinja`:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  ```
- Files to modify:
  - `xregistry/templates/py/ehproducer/{testdir}test_producer.py.jinja`
  - `xregistry/templates/py/ehconsumer/{testdir}test_dispatcher.py.jinja`
  - `xregistry/templates/py/ehproducer/pyproject.toml.jinja`
  - `xregistry/templates/py/ehconsumer/pyproject.toml.jinja`

---

## Python Kafka Tests (8 tests) - pytest-asyncio Configuration Issue

**Status:** Skipped  
**Issue:** Generated tests fail with "async def functions are not natively supported"  
**Affected Tests:**
- `test/py/test_python.py::test_kafkaproducer_contoso_erp_py`
- `test/py/test_python.py::test_kafkaproducer_fabrikam_motorsports_py`
- `test/py/test_python.py::test_kafkaproducer_inkjet_py`
- `test/py/test_python.py::test_kafkaproducer_lightbulb_py`
- `test/py/test_python.py::test_kafkaconsumer_contoso_erp_py`
- `test/py/test_python.py::test_kafkaconsumer_fabrikam_motorsports_py`
- `test/py/test_python.py::test_kafkaconsumer_inkjet_py`
- `test/py/test_python.py::test_kafkaconsumer_lightbulb_py`

**Root Cause:** Same as EventHubs tests - the generated `pyproject.toml` includes `pytest-asyncio` as a dependency and test functions use `@pytest.mark.asyncio` decorators, but async fixtures lack proper configuration. Pytest gives the error: `'test_producer.py' requested an async fixture 'kafka_emulator', with no plugin or hook that handled it.`

**Technical Details:**
- Templates: `xregistry/templates/py/kafkaproducer/{testdir}test_producer.py.jinja` and `kafkaconsumer` variant
- The fixture uses `@pytest.fixture(scope="module")` instead of `@pytest_asyncio.fixture`
- Alternative: Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` in `pyproject.toml.jinja`

**Resolution:** Same fix as EventHubs tests:
- Option 1: Change `@pytest.fixture` to `@pytest_asyncio.fixture` for async fixtures in templates
- Option 2: Add pytest configuration to `pyproject.toml.jinja`:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  ```
- Files to modify:
  - `xregistry/templates/py/kafkaproducer/{testdir}test_producer.py.jinja`
  - `xregistry/templates/py/kafkaconsumer/{testdir}test_dispatcher.py.jinja`
  - `xregistry/templates/py/kafkaproducer/pyproject.toml.jinja`
  - `xregistry/templates/py/kafkaconsumer/pyproject.toml.jinja`

---

## Summary

**Total Tests:** 193  
**Passing:** 156  
**Skipped:** 37 (17 pre-existing + 20 new)  
**Last Updated:** 2025-11-05  
**Last Successful CI Run:** https://github.com/clemensv/xregistry-cli/actions/runs/19112322037  
**Last Failed CI Run (Investigation):** https://github.com/clemensv/xregistry-cli/actions/runs/19111112588

**Root Cause Summary:**
- **Catalog tests (4):** Infrastructure issue with xrserver MySQL container initialization
- **Python EventHubs/Kafka tests (16):** Template generation issue - async fixtures missing `@pytest_asyncio.fixture` decorator or `asyncio_mode = "auto"` configuration
