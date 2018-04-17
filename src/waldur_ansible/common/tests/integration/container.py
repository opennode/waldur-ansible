from time import sleep

import docker
from waldur_ansible.common.tests.integration.exceptions import TimeoutException

MAX_TRIES = 4
SLEEP_TIME = 1


class DockerContainer(object):
    def __init__(self, container_name, image):
        self.ports = {}
        self.image = image
        self.container = None
        self.container_name = container_name

    def start(self):
        print("Starting container %s" % self.image)
        self.container = docker.from_env().containers.run(self.image,
                                                          detach=True,
                                                          stdin_open=True,
                                                          remove=True,
                                                          tty=True,
                                                          ports=self.ports,
                                                          name=self.container_name,
                                                          # these are for systemd
                                                          security_opt=["seccomp=unconfined"],
                                                          tmpfs={"/run": "", "/run/lock": ""},
                                                          volumes=["/sys/fs/cgroup:/sys/fs/cgroup:ro"], )
        print("Container started: %s" % self.container.short_id)
        return self

    def stop(self, force=True, delete_volume=True):
        self.get_contaner().remove(force=force, v=delete_volume)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def get_container_host_ip(self):
        return "0.0.0.0"

    def bind_port(self, container_port, host_port):
        self.ports[container_port] = host_port
        return self

    def get_contaner(self):
        return self.container

    def wait_to_start_internal(self, container_started_condition_function):
        exception = None
        print("Waiting for container to start...")
        for i in range(0, MAX_TRIES):
            try:
                if container_started_condition_function():
                    return
                else:
                    continue
            except Exception as e:
                exception = e
            sleep(SLEEP_TIME)
        raise TimeoutException(
            "Wait time exceeded %s sec. Exception %s" % (MAX_TRIES * SLEEP_TIME, exception))
