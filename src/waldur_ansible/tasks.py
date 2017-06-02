import errno
import logging
import os

from celery import shared_task


logger = logging.getLogger(__name__)


@shared_task(name='waldur_ansible.tasks.delete_playbook')
def delete_playbook(name, playbook_path):
    try:
        os.remove(playbook_path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            logger.info('Playbook %s stored in %s does not exist.', name, playbook_path)
        else:
            logger.warning('Failed to delete playbook %s stored in %s.', name, playbook_path)
            raise
    else:
        logger.info('Playbook %s stored in %s has been deleted.', name, playbook_path)
