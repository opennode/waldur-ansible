from nodeconductor.core import NodeConductorExtension


class AnsibleExtension(NodeConductorExtension):

    class Settings:
        WALDUR_ANSIBLE = {
            'PLAYBOOKS_DIR_NAME': 'ansible_playbooks',
            'PRESERVE_PLAYBOOK_ARCHIVE_AFTER_DELETION': False,
            'PLAYBOOK_EXECUTION_COMMAND': 'ansible-playbook',
            'PLAYBOOK_ARGUMENTS': ['--verbose'],
            'ANSIBLE_LIBRARY': '/usr/share/ansible-waldur/',
        }

    @staticmethod
    def django_app():
        return 'waldur_ansible'

    @staticmethod
    def rest_urls():
        from .urls import register_in
        return register_in
