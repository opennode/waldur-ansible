import errno
import logging
import os

from celery import shared_task


logger = logging.getLogger(__name__)


@shared_task(name='waldur_ansible.tasks.delete_playbook_archive')
def delete_playbook_archive(archive_path):
    try:
        os.remove(archive_path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            logger.info('Playbook stored in %s does not exist.', archive_path)
        else:
            logger.warning('Failed to delete playbook stored in %s.', archive_path)
            raise
    else:
        logger.info('Playbook stored in %s has been deleted.', archive_path)
