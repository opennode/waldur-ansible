from django.conf import settings

from . import tasks


def cleanup_playbook_archive(sender, instance, **kwargs):
    if not settings.WALDUR_ANSIBLE.get('PRESERVE_PLAYBOOK_ARCHIVE_AFTER_DELETION', False):
        tasks.delete_playbook_archive.delay(instance.archive.path)
