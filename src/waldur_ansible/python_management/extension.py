from waldur_core.core import WaldurExtension


class PythonManagementExtension(WaldurExtension):
    class Settings:
        WALDUR_PYTHON_MANAGEMENT = {
            'PYTHON_MANAGEMENT_PLAYBOOKS_DIRECTORY': '/usr/share/ansible-waldur/python_management/',
            'SYNC_PIP_PACKAGES_TASK_ENABLED': False,
            'SYNC_PIP_PACKAGES_BATCH_SIZE': 300,
            'PYTHON_MANAGEMENT_ENTRY_POINT_LOCK_TIMEOUT': 120,
            'PYTHON_MANAGEMENT_TIMEOUT': 3600,
        }

    @staticmethod
    def django_app():
        return 'waldur_ansible.python_management'

    @staticmethod
    def rest_urls():
        from .urls import register_in
        return register_in

    @staticmethod
    def is_assembly():
        return True

    @staticmethod
    def celery_tasks():
        from datetime import timedelta
        return {
            'waldur-ansible-sync-pip-packages': {
                'task': 'waldur_ansible.sync_pip_libraries',
                'schedule': timedelta(hours=48),
                'args': (),
            },
        }

    @staticmethod
    def get_public_settings():
        return ['PYTHON_MANAGEMENT_TIMEOUT']
