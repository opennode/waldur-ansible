from __future__ import unicode_literals

from ddt import data, ddt
from rest_framework.test import APITransactionTestCase
from rest_framework import status

from nodeconductor.structure.tests import factories as structure_factories
from nodeconductor_openstack.openstack_tenant.tests import factories as openstack_factories

from . import factories, fixtures


class JobBaseTest(APITransactionTestCase):
    def setUp(self):
        self.fixture = fixtures.JobFixture()
        self.job = self.fixture.job

    def _get_valid_payload(self, user, job=None):
        job = job or factories.JobFactory()
        key = structure_factories.SshPublicKeyFactory(user=user)
        return {
            'name': 'test job',
            'service_project_link': openstack_factories.OpenStackTenantServiceProjectLinkFactory.get_url(self.fixture.spl),
            'ssh_public_key': structure_factories.SshPublicKeyFactory.get_url(key),
            'playbook': factories.PlaybookFactory.get_url(job.playbook),
            'arguments': job.arguments,
        }


@ddt
class JobRetrieveTest(JobBaseTest):

    def test_anonymous_user_cannot_retrieve_job(self):
        response = self.client.get(factories.JobFactory.get_list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data('staff', 'global_support', 'owner',
          'customer_support', 'admin', 'manager', 'project_support')
    def test_user_can_retrieve_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        response = self.client.get(factories.JobFactory.get_url(self.job))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_user_cannot_retrieve_job(self):
        self.client.force_authenticate(self.fixture.user)
        response = self.client.get(factories.JobFactory.get_url(self.job))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@ddt
class JobCreateTest(JobBaseTest):

    @data('staff', 'owner', 'manager', 'admin')
    def test_user_can_create_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        payload = self._get_valid_payload(getattr(self.fixture, user))
        response = self.client.post(factories.JobFactory.get_list_url(), data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    @data('global_support', 'customer_support', 'project_support')
    def test_user_cannot_create_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        payload = self._get_valid_payload(getattr(self.fixture, user))
        response = self.client.post(factories.JobFactory.get_list_url(), data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_create_job_with_invalid_argument(self):
        self.client.force_authenticate(self.fixture.staff)
        payload = self._get_valid_payload(self.fixture.staff)
        payload['arguments'] = {'invalid': 'invalid'}

        response = self.client.post(factories.JobFactory.get_list_url(), data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['Argument invalid is not listed in playbook parameters.'])

    def test_user_cannot_create_job_with_unspecified_required_parameter(self):
        self.client.force_authenticate(self.fixture.staff)
        playbook = factories.PlaybookFactory(
            parameters=[factories.PlaybookParameterFactory(required=True, default='')])
        job = factories.JobFactory(playbook=playbook)
        payload = self._get_valid_payload(self.fixture.staff, job)
        payload['arguments'] = {}

        response = self.client.post(factories.JobFactory.get_list_url(), data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['Not all required playbook parameters were specified.'])


@ddt
class JobUpdateTest(JobBaseTest):

    @data('staff', 'owner', 'manager', 'admin')
    def test_user_can_update_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        payload = {'name': 'test job 2'}
        response = self.client.put(factories.JobFactory.get_url(self.job), data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.job.refresh_from_db()
        self.assertEqual(self.job.name, payload['name'])

    @data('global_support', 'customer_support', 'project_support')
    def test_user_cannot_update_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        payload = {'name': 'test job 2'}
        response = self.client.put(factories.JobFactory.get_url(self.job), data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@ddt
class JobDeleteTest(JobBaseTest):

    @data('staff', 'owner', 'manager', 'admin')
    def test_staff_user_can_delete_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        response = self.client.delete(factories.JobFactory.get_url(self.job))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @data('global_support', 'customer_support', 'project_support')
    def test_user_cannot_delete_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        response = self.client.delete(factories.JobFactory.get_url(self.job))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
