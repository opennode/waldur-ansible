import json
import logging
import os
import pickle  # nosec
import six
import subprocess  # nosec

from django.conf import settings


logger = logging.getLogger(__name__)


class AnsibleBackendError(Exception):
    def __init__(self, *args, **kwargs):
        if not args:
            super(AnsibleBackendError, self).__init__(*args, **kwargs)

        # CalledProcessError is not serializable by Celery, because it uses custom arguments *args
        # and define __init__ method, but don't call Exception.__init__ method
        # http://docs.celeryproject.org/en/latest/userguide/tasks.html#creating-pickleable-exceptions
        # That's why when Celery worker tries to deserialize AnsibleBackendError,
        # it uses empty invalid *args. It leads to unrecoverable error and worker dies.
        # When all workers are dead, all tasks are stuck in pending state forever.
        # In order to fix this issue we serialize exception to text type explicitly.
        args = list(args)
        for i, arg in enumerate(args):
            try:
                # pickle is used to check celery internal errors serialization,
                # it is safe from security point of view
                pickle.loads(pickle.dumps(arg))  # nosec
            except (pickle.PickleError, TypeError):
                args[i] = six.text_type(arg)

        super(AnsibleBackendError, self).__init__(*args, **kwargs)


class AnsibleBackend(object):
    def __init__(self, playbook):
        self.playbook = playbook

    def _get_command(self, job):
        playbook_path = os.path.join(self.playbook.workspace, self.playbook.entrypoint)
        if not os.path.exists(playbook_path):
            raise AnsibleBackendError('Playbook %s does not exist.' % playbook_path)

        command = [settings.WALDUR_ANSIBLE.get('PLAYBOOK_EXECUTION_COMMAND', 'ansible-playbook')]
        if settings.WALDUR_ANSIBLE.get('PLAYBOOK_ARGUMENTS'):
            command.extend(settings.WALDUR_ANSIBLE.get('PLAYBOOK_ARGUMENTS'))
        if job.arguments:
            # XXX: Passing arguments in following way is supported in Ansible>=1.2
            command.extend(['--extra-vars', json.dumps(job.arguments)])

        command.extend(['--ssh-common-args', '-o UserKnownHostsFile=/dev/null'])
        return command + [playbook_path]

    def run_job(self, job):
        command = self._get_command(job)
        command_str = ' '.join(command)

        logger.debug('Executing command "%s".', command_str)
        env = dict(
            os.environ,
            ANSIBLE_LIBRARY=settings.WALDUR_ANSIBLE['ANSIBLE_LIBRARY'],
            ANSIBLE_HOST_KEY_CHECKING='False',
        )
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, env=env)  # nosec
        except subprocess.CalledProcessError as e:
            logger.info('Failed to execute command "%s".', command_str)
            job.output = e.output
            job.save(update_fields=['output'])
            six.reraise(AnsibleBackendError, e)
        else:
            logger.info('Command "%s" was successfully executed.', command_str)
            job.output = output
            job.save(update_fields=['output'])
