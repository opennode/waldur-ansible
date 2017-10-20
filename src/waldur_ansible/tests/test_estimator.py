from __future__ import unicode_literals

import json
import mock

from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from nodeconductor.structure import models as structure_models
from nodeconductor.structure.tests import fixtures as structure_fixtures
from nodeconductor.structure.tests import factories as structure_factories
from nodeconductor_assembly_waldur.packages import models as package_models
from nodeconductor_openstack.openstack import apps as openstack_apps
from nodeconductor_openstack.openstack import models as openstack_models
from nodeconductor_openstack.openstack_tenant import apps as tenant_apps
from nodeconductor_openstack.openstack_tenant import models as tenant_models
from nodeconductor_openstack.openstack_tenant.tests import factories as tenant_factories

from . import factories


Types = package_models.PackageComponent.Types


class EstimationFixture(structure_fixtures.ProjectFixture):

    @cached_property
    def shared_settings(self):
        return structure_factories.ServiceSettingsFactory(
            type=openstack_apps.OpenStackConfig.service_name,
            shared=True,
            options={'external_network_id': 'test_network_id'},
            state=structure_models.ServiceSettings.States.OK,
        )

    @cached_property
    def prices(self):
        return {
            Types.CORES: 10,
            Types.RAM: 20,
            Types.STORAGE: 30,
        }

    @cached_property
    def template(self):
        template = package_models.PackageTemplate.objects.create(
            name='Premium package template',
            service_settings=self.shared_settings
        )
        for (type, price) in self.prices.items():
            package_models.PackageComponent.objects.create(
                type=type,
                price=price,
                template=template
            )
        return template

    @cached_property
    def shared_service(self):
        return openstack_models.OpenStackService.objects.get(
            customer=self.customer,
            settings=self.shared_settings,
        )

    @cached_property
    def shared_link(self):
        return openstack_models.OpenStackServiceProjectLink.objects.get(
            service=self.shared_service,
            project=self.project,
        )

    @cached_property
    def tenant(self):
        return openstack_models.Tenant.objects.create(
            name='Tenant',
            service_project_link=self.shared_link,
            extra_configuration={
                'package_uuid': self.template.uuid.hex
            }
        )

    @cached_property
    def private_settings(self):
        return structure_factories.ServiceSettingsFactory(
            type=tenant_apps.OpenStackTenantConfig.service_name,
            customer=self.customer,
            scope=self.tenant,
            options={
                'availability_zone': self.tenant.availability_zone,
                'tenant_id': self.tenant.backend_id,
                'external_network_id': self.tenant.external_network_id,
                'internal_network_id': self.tenant.internal_network_id,
            }
        )

    @cached_property
    def private_service(self):
        return tenant_models.OpenStackTenantService.objects.create(
            settings=self.private_settings,
            customer=self.customer,
        )

    @cached_property
    def private_link(self):
        return tenant_models.OpenStackTenantServiceProjectLink.objects.create(
            service=self.private_service,
            project=self.project,
        )

    @cached_property
    def image(self):
        return tenant_factories.ImageFactory(
            settings=self.private_settings,
            min_disk=10240,
            min_ram=1024
        )

    @cached_property
    def flavor(self):
        return tenant_factories.FlavorFactory(settings=self.private_settings)

    @cached_property
    def network(self):
        return tenant_models.Network.objects.create(settings=self.private_settings)

    @cached_property
    def subnet(self):
        return tenant_models.SubNet.objects.create(
            settings=self.private_settings,
            network=self.network,
        )

    @cached_property
    def ssh_public_key(self):
        return structure_factories.SshPublicKeyFactory(user=self.owner)


class EstimatorTest(APITransactionTestCase):

    def setUp(self):
        self.fixture = EstimationFixture()
        self.template = self.fixture.template

        self.private_settings = self.fixture.private_settings
        self.private_service = self.fixture.private_service

        self.private_link = self.fixture.private_link
        self.private_link_url = tenant_factories.OpenStackTenantServiceProjectLinkFactory.get_url(self.private_link)

        self.image = self.fixture.image
        self.image_url = tenant_factories.ImageFactory.get_url(self.image)

        self.flavor = self.fixture.flavor
        self.flavor_url = tenant_factories.FlavorFactory.get_url(self.flavor)

        self.subnet = self.fixture.subnet
        self.subnet_url = tenant_factories.SubNetFactory.get_url(self.subnet)

        self.prices = self.fixture.prices

        self.playbook = factories.PlaybookFactory()
        self.playbook_url = factories.PlaybookFactory.get_url(self.playbook)

        self.ssh_public_key = structure_factories.SshPublicKeyFactory(user=self.fixture.owner)
        self.ssh_public_key_url = structure_factories.SshPublicKeyFactory.get_url(self.ssh_public_key)

        self.path_patcher = mock.patch('os.path.exists')
        self.path_api = self.path_patcher.start()
        self.path_api.side_effect = lambda f: f == self.playbook.get_playbook_path()

        self.subprocess_patcher = mock.patch('subprocess.check_output')
        self.subprocess_api = self.subprocess_patcher.start()

        self.subprocess_api.return_value = self.get_valid_output()

    def tearDown(self):
        super(EstimatorTest, self).tearDown()
        self.path_patcher.stop()
        self.subprocess_patcher.stop()

    def test_user_can_get_estimation_report_for_valid_request(self):
        response = self.get_report()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data, self.get_expected_report())

    def test_validation_error_if_image_is_not_enough(self):
        self.image.min_ram = self.flavor.ram + 1
        self.image.save()

        response = self.get_report()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('flavor' in response.data[0])

    def test_validation_error_if_quota_exceeded(self):
        self.private_settings.quotas.filter(
            name=self.private_settings.Quotas.instances
        ).update(
            limit=10,
            usage=10
        )

        response = self.get_report()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('One or more quotas were exceeded' in response.data[0])

    def test_if_package_is_not_defined_price_is_zero(self):
        self.private_settings.scope = None
        self.private_settings.save()

        response = self.get_report()

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['cost'], 0)

    def get_report(self):
        self.client.force_login(self.fixture.owner)
        url = '%sestimate/' % reverse('ansible_job-list')
        return self.client.post(url, {
            'playbook': self.playbook_url,
            'service_project_link': self.private_link_url,
            'ssh_public_key': self.ssh_public_key_url,
        })

    def get_valid_output(self):
        return 'ok: [localhost] => %s' % json.dumps({
            'WALDUR_CHECK_MODE': True,
            'service_project_link': self.private_link_url,
            'flavor': self.flavor_url,
            'image': self.image_url,
            'name': 'Valid name',
            'system_volume_size': self.image.min_disk,
            'internal_ips_set': [
                {'subnet': self.subnet_url}
            ]
        })

    def get_expected_requirements(self):
        return {
            'cpu': self.flavor.cores,
            'ram': self.flavor.ram,
            'disk': self.flavor.disk,
        }

    def get_expected_prices(self):
        return {
            'cpu': self.prices[Types.CORES],
            'ram': self.prices[Types.RAM],
            'disk': self.prices[Types.STORAGE],
        }

    def get_expected_cost(self):
        return (
            self.flavor.cores * self.prices[Types.CORES] +
            self.flavor.ram * self.prices[Types.RAM] +
            self.flavor.disk * self.prices[Types.STORAGE]
        )

    def get_expected_report(self):
        return {
            'requirements': self.get_expected_requirements(),
            'prices': self.get_expected_prices(),
            'cost': self.get_expected_cost()
        }

