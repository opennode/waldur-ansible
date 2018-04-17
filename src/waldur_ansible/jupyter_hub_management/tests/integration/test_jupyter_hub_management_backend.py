import django
import os

import pytest
import requests
import urllib3
from waldur_ansible.common.tests.integration.ubuntu1604_container import Ubuntu1604Container
from waldur_ansible.common.utils import subprocess_output_iterator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "waldur_core.server.test_settings")
django.setup()

from mock import patch
from django.conf import settings
from django.test import override_settings
from django.test import TestCase
from waldur_ansible.jupyter_hub_management.tests import factories as jupyter_hub_factories, fixtures as jupyter_hub_fixtures
from waldur_ansible.python_management.tests import factories
from waldur_openstack.openstack_tenant import models as openstack_tenant_models


class PythonManagementIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(PythonManagementIntegrationTest, cls).setUpClass()
        cls.build_image()

    @classmethod
    def build_image(cls):
        for output_line in subprocess_output_iterator(["./build_ubuntu_integration_test_image"], os.environ, cwd=os.path.dirname(os.path.abspath(__file__))+"/init"):
            print(output_line)

    def setUp(self):
        self.fixture = jupyter_hub_fixtures.JupyterHubManagementLinuxPamFixture()
        self.create_users()
        self.module_path = "waldur_ansible.python_management.backend.python_management_backend."

    @pytest.mark.integration
    @override_settings()
    def test_jupyter_hub_initialization(self):
        self.prepare_environment()
        
        ubuntu_container = Ubuntu1604Container()
        ubuntu_container.bind_port("443/tcp", "4444")

        with ubuntu_container:
            ubuntu_container.wait_to_start()
            container_ip = ubuntu_container.get_container_host_ip()
            python_management = self.fixture.jupyter_hub_management_linux_pam.python_management
            openstack_tenant_models.FloatingIP.objects.filter(id=python_management.instance.floating_ips[0].id).update(address=container_ip, name=container_ip)

            init_request = factories.PythonManagementInitializeRequestFactory(python_management=python_management, output="")

            with patch(self.module_path + "locking_service.PythonManagementBackendLockingService") as locking_service:
                locking_service.is_processing_allowed.return_value = True
                init_request.get_backend().process_python_management_request(init_request)
                jup_init_request = jupyter_hub_factories.JupyterHubManagementSyncConfigurationRequestFactory(
                    jupyter_hub_management=self.fixture.jupyter_hub_management_linux_pam, output="")
                jup_init_request.get_backend().process_jupyter_hub_management_request(jup_init_request)

            jupyter_hub_request = requests.get("https://%s:%s" % (ubuntu_container.get_container_host_ip(), ubuntu_container.ports["443/tcp"]), verify=False)
            self.assertEquals(jupyter_hub_request.status_code, 200)

    def prepare_environment(self):
        settings.WALDUR_ANSIBLE_COMMON["REMOTE_VM_SSH_PORT"] = "2222"
        settings.WALDUR_ANSIBLE_COMMON["PRIVATE_KEY_PATH"] = os.path.dirname(os.path.abspath(__file__)) + "/init/waldur_integration_test_ssh_key"
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def create_users(self):
        self.fixture.jupyter_hub_admin_user
