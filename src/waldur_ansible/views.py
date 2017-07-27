from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from nodeconductor.core.validators import StateValidator
from nodeconductor.core.views import ActionsViewSet
from nodeconductor.structure.filters import GenericRoleFilter
from nodeconductor.structure.metadata import ActionsMetadata
from nodeconductor.structure.permissions import is_staff, is_manager

from . import filters, models, serializers, executors


class PlaybookViewSet(ActionsViewSet):
    lookup_field = 'uuid'
    queryset = models.Playbook.objects.all().order_by('pk')
    unsafe_methods_permissions = [is_staff]
    serializer_class = serializers.PlaybookSerializer


class JobViewSet(ActionsViewSet):
    lookup_field = 'uuid'
    queryset = models.Job.objects.all().order_by('pk')
    filter_backends = (GenericRoleFilter, DjangoFilterBackend)
    filter_class = filters.AnsibleJobsFilter
    unsafe_methods_permissions = [is_manager]
    serializer_class = serializers.JobSerializer
    metadata_class = ActionsMetadata
    destroy_validators = [StateValidator(models.Job.States.OK, models.Job.States.ERRED)]

    @detail_route(methods=['post'])
    def execute(self, request, uuid=None):
        executors.RunJobExecutor().execute(self.get_object())
        return Response({'status': _('Playbook job execution has been scheduled.')}, status=status.HTTP_202_ACCEPTED)

    execute_validators = [StateValidator(models.Job.States.OK, models.Job.States.ERRED)]
