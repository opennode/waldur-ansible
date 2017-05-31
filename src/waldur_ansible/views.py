from nodeconductor.core.views import ActionsViewSet
from nodeconductor.structure.permissions import is_staff

from . import models, serializers


class PlaybookViewSet(ActionsViewSet):
    lookup_field = 'uuid'
    queryset = models.Playbook.objects.all().order_by('pk')
    unsafe_methods_permissions = [is_staff]
    serializer_class = serializers.PlaybookSerializer
