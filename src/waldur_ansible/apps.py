from django.apps import AppConfig
from django.db.models import signals

from . import handlers


class AnsibleConfig(AppConfig):
    name = 'waldur_ansible'
    verbose_name = 'Waldur Ansible'

    def ready(self):
        Playbook = self.get_model('Playbook')

        signals.pre_delete.connect(
            handlers.delete_playbook_workspace,
            sender=Playbook,
            dispatch_uid='waldur_ansible.handlers.delete_playbook_workspace',
        )

        signals.pre_save.connect(
            handlers.resize_playbook_image,
            sender=Playbook,
            dispatch_uid='waldur_ansible.handlers.resize_playbook_image',
        )
