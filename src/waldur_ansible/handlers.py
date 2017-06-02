from django.conf import settings

from . import tasks


def cleanup_playbook(sender, instance, **kwargs):
    if not settings.WALDUR_ANSIBLE.get('PRESERVE_PLAYBOOKS_AFTER_DELETION', False):
        tasks.delete_playbook.delay(instance.name, instance.file.path)
