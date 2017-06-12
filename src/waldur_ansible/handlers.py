from django.conf import settings

from . import tasks


def delete_playbook_workspace(sender, instance, **kwargs):
    if not settings.WALDUR_ANSIBLE.get('PRESERVE_PLAYBOOK_WORKSPACE_AFTER_DELETION', False):
        tasks.delete_playbook_workspace.delay(instance.workspace)
