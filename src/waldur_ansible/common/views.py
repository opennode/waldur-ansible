import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from waldur_ansible.common import filters as common_filters

from waldur_core.core import managers as core_managers
from waldur_core.structure import views as structure_views, filters as structure_filters
from . import serializers, models

logger = logging.getLogger(__name__)


def build_applications_queryset():
    return core_managers.SummaryQuerySet(models.ApplicationModel.get_application_models())


def get_project_jobs_count(project):
    return build_applications_queryset().filter(project=project).count()


structure_views.ProjectCountersView.register_counter('ansible', get_project_jobs_count)


class ApplicationsSummaryViewSet(ListModelMixin, GenericViewSet):
    serializer_class = serializers.SummaryApplicationSerializer
    filter_backends = (structure_filters.GenericRoleFilter, common_filters.ApplicationSummaryFilterBackend, DjangoFilterBackend)

    def get_queryset(self):
        return build_applications_queryset()
