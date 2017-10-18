from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import ugettext_lazy as _
from rest_framework import decorators, response, status

from nodeconductor.core import exceptions as core_exceptions
from nodeconductor.core import mixins as core_mixins
from nodeconductor.core import validators as core_validators
from nodeconductor.core import views as core_views
from nodeconductor.structure import views as structure_views
from nodeconductor.structure.filters import GenericRoleFilter
from nodeconductor.structure.metadata import ActionsMetadata
from nodeconductor.structure.permissions import is_staff, is_administrator
from nodeconductor_openstack.openstack_tenant import models as openstack_models

from . import filters, models, serializers, executors


class PlaybookViewSet(core_views.ActionsViewSet):
    lookup_field = 'uuid'
    queryset = models.Playbook.objects.all().order_by('pk')
    unsafe_methods_permissions = [is_staff]
    serializer_class = serializers.PlaybookSerializer


def check_all_related_resource_are_stable(job):
    stable_states = (openstack_models.Instance.States.OK, openstack_models.Instance.States.ERRED)
    if not all(resource.state in stable_states for resource in job.get_related_resources()):
        raise core_exceptions.IncorrectStateException(_('Related resources are not stable yet. '
                                                        'Please wait until provisioning is completed.'))


class JobViewSet(core_mixins.CreateExecutorMixin, core_views.ActionsViewSet):
    lookup_field = 'uuid'
    queryset = models.Job.objects.all().order_by('pk')
    filter_backends = (GenericRoleFilter, DjangoFilterBackend)
    filter_class = filters.AnsibleJobsFilter
    unsafe_methods_permissions = [is_administrator]
    serializer_class = serializers.JobSerializer
    metadata_class = ActionsMetadata
    create_executor = executors.RunJobExecutor

    destroy_validators = [
        check_all_related_resource_are_stable,
        core_validators.StateValidator(models.Job.States.OK, models.Job.States.ERRED)
    ]
    delete_executor = executors.DeleteJobExecutor

    @decorators.list_route(methods=['POST'])
    def estimate(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        backend = job.get_backend()
        backend.run_job(job, check_mode=True)
        job.refresh_from_db()
        items = backend.decode_output(job.output)
        job.delete()
        return response.Response(items, status=status.HTTP_200_OK)


def get_project_jobs_count(project):
    return models.Job.objects.filter(service_project_link__project=project).count()

structure_views.ProjectCountersView.register_counter('ansible', get_project_jobs_count)
