import os

from waldur_ansible.common.tests.integration.container import DockerContainer
from waldur_ansible.common.utils import subprocess_output_iterator

CONTAINER_SSH_PORT_ON_HOST = '2222'


class Ubuntu1604Container(DockerContainer):
    def __init__(self):
        super(Ubuntu1604Container, self).__init__("integration-test-ubuntu1604-container", "integration-test-image:ubuntu1604")
        self.bind_port('22/tcp', CONTAINER_SSH_PORT_ON_HOST)

    @staticmethod
    def build_image():
        for output_line in subprocess_output_iterator(["./build_ubuntu_integration_test_image"], os.environ, cwd=os.path.dirname(os.path.abspath(__file__)) + "/ubuntu1604_image"):
            print(output_line)

    @staticmethod
    def get_private_key_path():
        return os.path.dirname(os.path.abspath(__file__)) + "/ubuntu1604_image/waldur_integration_test_ssh_key"
