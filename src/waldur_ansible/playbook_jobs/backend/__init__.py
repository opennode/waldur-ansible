from waldur_core import _get_version

__version__ = _get_version('waldur_ansible')

default_app_config = 'waldur_ansible.playbook_jobs.apps.PlaybookJobsConfig'
