from django.utils.functional import cached_property
from waldur_openstack.openstack_tenant.tests import fixtures as openstack_fixtures

from . import factories


class PythonManagementFixture(openstack_fixtures.OpenStackTenantFixture):
    @cached_property
    def python_management(self):
        return factories.PythonManagementFactory(
            service_project_link=self.spl,
            virtual_envs_dir_path='my-virtual-envs',
            instance=self.instance,
            user=self.user
        )
