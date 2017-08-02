from django_filters.rest_framework import DjangoFilterBackend

from nodeconductor.core import mixins as core_mixins
from nodeconductor.core import validators as core_validators
from nodeconductor.core import views as core_views
from nodeconductor.structure.filters import GenericRoleFilter
from nodeconductor.structure.metadata import ActionsMetadata
from nodeconductor.structure.permissions import is_staff, is_manager

from . import filters, models, serializers, executors


class PlaybookViewSet(core_views.ActionsViewSet):
    lookup_field = 'uuid'
    queryset = models.Playbook.objects.all().order_by('pk')
    unsafe_methods_permissions = [is_staff]
    serializer_class = serializers.PlaybookSerializer


class JobViewSet(core_mixins.CreateExecutorMixin, core_views.ActionsViewSet):
    lookup_field = 'uuid'
    queryset = models.Job.objects.all().order_by('pk')
    filter_backends = (GenericRoleFilter, DjangoFilterBackend)
    filter_class = filters.AnsibleJobsFilter
    unsafe_methods_permissions = [is_manager]
    serializer_class = serializers.JobSerializer
    metadata_class = ActionsMetadata
    destroy_validators = [core_validators.StateValidator(models.Job.States.OK, models.Job.States.ERRED)]
    create_executor = executors.RunJobExecutor
