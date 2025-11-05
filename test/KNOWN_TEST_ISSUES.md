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

## Python EventHubs Tests (8 tests) - Build Issue

**Status:** Skipped  
**Issue:** Make test command fails with non-zero exit status 2  
**Affected Tests:**
- `test/py/test_python.py::test_ehproducer_contoso_erp_py`
- `test/py/test_python.py::test_ehproducer_fabrikam_motorsports_py`
- `test/py/test_python.py::test_ehproducer_inkjet_py`
- `test/py/test_python.py::test_ehproducer_lightbulb_py`
- `test/py/test_python.py::test_ehconsumer_contoso_erp_py`
- `test/py/test_python.py::test_ehconsumer_fabrikam_motorsports_py`
- `test/py/test_python.py::test_ehconsumer_inkjet_py`
- `test/py/test_python.py::test_ehconsumer_lightbulb_py`

**Root Cause:** Generated Python EventHubs producer/consumer code fails during `make test` execution. The generated Makefile or test code has issues.

**Resolution:** 
- Debug the Python EventHubs template generation
- Fix the generated Makefile or test setup
- Investigate missing dependencies or incorrect test configuration

---

## Python Kafka Tests (8 tests) - Build Issue

**Status:** Skipped  
**Issue:** Make test command fails with non-zero exit status 2  
**Affected Tests:**
- `test/py/test_python.py::test_kafkaproducer_contoso_erp_py`
- `test/py/test_python.py::test_kafkaproducer_fabrikam_motorsports_py`
- `test/py/test_python.py::test_kafkaproducer_inkjet_py`
- `test/py/test_python.py::test_kafkaproducer_lightbulb_py`
- `test/py/test_python.py::test_kafkaconsumer_contoso_erp_py`
- `test/py/test_python.py::test_kafkaconsumer_fabrikam_motorsports_py`
- `test/py/test_python.py::test_kafkaconsumer_inkjet_py`
- `test/py/test_python.py::test_kafkaconsumer_lightbulb_py`

**Root Cause:** Generated Python Kafka producer/consumer code fails during `make test` execution. The generated Makefile or test code has issues.

**Resolution:**
- Debug the Python Kafka template generation
- Fix the generated Makefile or test setup
- Investigate missing dependencies or incorrect test configuration

---

## Summary

**Total Tests:** 193  
**Passing:** 156  
**Skipped:** 37 (17 pre-existing + 20 new)  
**Last Updated:** 2025-11-05  
**CI Run:** https://github.com/clemensv/xregistry-cli/actions/runs/19109631212
