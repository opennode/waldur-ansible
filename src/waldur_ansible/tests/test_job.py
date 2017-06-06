from __future__ import unicode_literals

from ddt import data, ddt
from rest_framework.test import APITransactionTestCase
from rest_framework import status

from nodeconductor.structure.tests.factories import ProjectFactory, UserFactory
from nodeconductor.structure.tests.fixtures import ProjectFixture

from . import factories


@ddt
class JobPermissionsTest(APITransactionTestCase):
    def setUp(self):
        self.fixture = ProjectFixture()
        self.job = factories.JobFactory(project=self.fixture.project)

    def test_anonymous_user_cannot_retrieve_job(self):
        response = self.client.get(factories.JobFactory.get_list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data('staff', 'global_support', 'owner',
          'customer_support', 'admin', 'manager', 'project_support')
    def test_user_can_retrieve_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        response = self.client.get(factories.JobFactory.get_url(self.job))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_retrieve_job(self):
        self.client.force_authenticate(self.fixture.user)
        response = self.client.get(factories.JobFactory.get_url(self.job))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data('staff', 'owner', 'manager')
    def test_user_can_create_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        payload = self._get_valid_payload()
        response = self.client.post(factories.JobFactory.get_list_url(), data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @data('global_support', 'customer_support', 'admin', 'project_support')
    def test_user_cannot_create_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        payload = self._get_valid_payload()
        response = self.client.post(factories.JobFactory.get_list_url(), data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data('staff', 'owner', 'manager')
    def test_user_can_update_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        payload = {'name': 'test job 2'}
        response = self.client.put(factories.JobFactory.get_url(self.job), data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.job.refresh_from_db()
        self.assertEqual(self.job.name, payload['name'])

    @data('global_support', 'customer_support', 'admin', 'project_support')
    def test_user_cannot_update_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        payload = {'name': 'test job 2'}
        response = self.client.put(factories.JobFactory.get_url(self.job), data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data('staff', 'owner', 'manager')
    def test_staff_user_can_delete_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        response = self.client.delete(factories.JobFactory.get_url(self.job))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @data('global_support', 'customer_support', 'admin', 'project_support')
    def test_user_cannot_delete_job(self, user):
        self.client.force_authenticate(getattr(self.fixture, user))
        response = self.client.delete(factories.JobFactory.get_url(self.job))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _get_valid_payload(self, job=None):
        job = job or factories.JobFactory(project=self.fixture.project)
        return {
            'name': 'test job',
            'project': ProjectFactory.get_url(job.project),
            'playbook': factories.PlaybookFactory.get_url(job.playbook),
            'arguments': job.arguments,
        }


class JobCreationTest(APITransactionTestCase):
    def setUp(self):
        self.staff = UserFactory(is_staff=True)

    def test_user_cannot_create_job_with_invalid_argument(self):
        self.client.force_authenticate(self.staff)
        payload = self._get_valid_payload()
        payload['arguments'] = {'invalid': 'invalid'}

        response = self.client.post(factories.JobFactory.get_list_url(), data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['Argument invalid is not listed in playbook parameters.'])

    def test_user_cannot_create_job_with_unspecified_required_parameter(self):
        self.client.force_authenticate(self.staff)
        playbook = factories.PlaybookFactory(
            parameters=[factories.PlaybookParameterFactory(required=True, default='')])
        job = factories.JobFactory(playbook=playbook)
        payload = self._get_valid_payload(job)
        payload['arguments'] = {}

        response = self.client.post(factories.JobFactory.get_list_url(), data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['Not all required playbook parameters were specified.'])

    def _get_valid_payload(self, job=None):
        job = job or factories.JobFactory()
        return {
            'name': 'test job',
            'project': ProjectFactory.get_url(job.project),
            'playbook': factories.PlaybookFactory.get_url(job.playbook),
            'arguments': job.arguments,
        }
