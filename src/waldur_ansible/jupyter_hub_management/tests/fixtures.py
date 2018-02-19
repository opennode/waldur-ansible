from django.utils.functional import cached_property
from waldur_ansible.jupyter_hub_management import models
from waldur_ansible.python_management.tests import fixtures as python_management_fixtures

from . import factories


class JupyterHubManagementFixture(python_management_fixtures.PythonManagementFixture):
    @cached_property
    def jupyter_hub_management(self):
        return factories.JupyterHubManagementFactory(
            project=self.spl.project,
            session_time_to_live_hours=600,
            instance=self.instance,
            python_management=self.python_management,
            user=self.user,
        )

    @cached_property
    def jupyter_hub_oauth_config(self):
        return factories.JupyterHubOAuthConfigFactory(
            type=models.JupyterHubOAuthType.GITLAB,
            oauth_callback_url='oauth_callback_url',
            client_id='client_id',
            client_secret='client_secret',
            gitlab_host='gitlab_host_2'
        )

    @cached_property
    def jupyter_hub_admin_user(self):
        return factories.JupyterHubUserFactory(
            username='admin_user',
            password='pass',
            whitelisted=False,
            admin=True,
            jupyter_hub_management=self.jupyter_hub_management
        )

    @cached_property
    def jupyter_hub_whitelisted_user(self):
        return factories.JupyterHubUserFactory(
            username='regular_user',
            password='pass',
            whitelisted=True,
            admin=False,
            jupyter_hub_management=self.jupyter_hub_management
        )
