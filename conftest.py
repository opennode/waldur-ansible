from waldur_ansible.common.tests.integration import integration_tests_config


def pytest_addoption(parser):
    parser.addoption(integration_tests_config.TEST_TAG_FLAG, action="append", help="specify what type of tests to run")
