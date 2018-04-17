import pytest

INTEGRATION_TEST_FLAG = "--integration"


def pytest_addoption(parser):
    parser.addoption(INTEGRATION_TEST_FLAG, action="store_true", default=False, help="run integration tests")


# Integration tests are marked with @pytest.mark.integration
# Integration tests are skipped if no --integration flag is provided to pytest
def pytest_collection_modifyitems(config, items):
    if config.getoption(INTEGRATION_TEST_FLAG):
        # --integration given in cli: do not skip integration tests
        return
    reason = "need %s flag to run" % INTEGRATION_TEST_FLAG
    skip_integration = pytest.mark.skip(reason=reason)
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
