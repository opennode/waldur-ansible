from __future__ import unicode_literals

import django_filters
from django.contrib import auth
from django.utils import six
from django_filters.filterset import FilterSetMetaclass
from waldur_ansible.playbook_jobs import models as playbook_jobs_models
from waldur_core.core import filters as core_filters

from . import models

User = auth.get_user_model()


class BaseApplicationFilter(six.with_metaclass(FilterSetMetaclass, django_filters.FilterSet)):
    project = django_filters.UUIDFilter(name='service_project_link__project__uuid')
    project_uuid = django_filters.UUIDFilter(name='service_project_link__project__uuid')
    project_name = django_filters.CharFilter(name='service_project_link__project__name', lookup_expr='icontains')

    service_uuid = django_filters.UUIDFilter(name='service_project_link__service__uuid')
    service_name = django_filters.CharFilter(name='service_project_link__service__settings__name', lookup_expr='icontains')

    class Meta(object):
        fields = (
            'project', 'project_uuid', 'project_name',
            'service_uuid', 'service_name',
        )


class PythonManagementFilter(BaseApplicationFilter):
    class Meta(object):
        model = models.PythonManagement
        fields = BaseApplicationFilter.Meta.fields


class JobManagementFilter(BaseApplicationFilter):
    class Meta(object):
        model = playbook_jobs_models.Job
        fields = BaseApplicationFilter.Meta.fields


class ApplicationSummaryFilterBackend(core_filters.SummaryFilter):

    def get_queryset_filter(self, queryset):
        if queryset.model is models.PythonManagement:
            return PythonManagementFilter
        elif queryset.model is playbook_jobs_models.Job:
            return JobManagementFilter
        return super(ApplicationSummaryFilterBackend, self).get_queryset_filter(queryset)

    def get_base_filter(self):
        return BaseApplicationFilter
