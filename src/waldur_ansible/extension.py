from waldur_core.core import WaldurExtension


class AnsibleExtension(WaldurExtension):

    class Settings:
        WALDUR_ANSIBLE = {
            'PLAYBOOKS_DIR_NAME': 'ansible_playbooks',
            'PLAYBOOK_EXECUTION_COMMAND': 'ansible-playbook',
            'PLAYBOOK_ARGUMENTS': ['--verbose'],
            'ANSIBLE_LIBRARY': '/usr/share/ansible-waldur/',
            'PLAYBOOK_ICON_SIZE': (64, 64),
            'API_URL': 'http://localhost/',
            'PRIVATE_KEY_PATH': '/etc/waldur/id_rsa',
            'PUBLIC_KEY_UUID': 'PUBLIC_KEY_UUID',
        }

    @staticmethod
    def django_app():
        return 'waldur_ansible'

    @staticmethod
    def rest_urls():
        from .urls import register_in
        return register_in
