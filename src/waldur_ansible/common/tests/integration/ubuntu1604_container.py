import docker
from waldur_ansible.common.tests.integration.container import DockerContainer


class Ubuntu1604Container(DockerContainer):

    def __init__(self):
        super(Ubuntu1604Container, self).__init__("integration-test-ubuntu1604-container", "integration-test-image:ubuntu1604")
        self.bind_port('22/tcp', '2222')

    def container_started_condition_function(self):
        return docker.APIClient().inspect_container(self.container.id)["State"]["Running"]

    def wait_to_start(self):
        super(Ubuntu1604Container, self).wait_to_start_internal(self.container_started_condition_function)
