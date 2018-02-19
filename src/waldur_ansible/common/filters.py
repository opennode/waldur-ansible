from __future__ import unicode_literals

import django_filters
from django.contrib import auth
from django.utils import six
from django_filters.filterset import FilterSetMetaclass

from waldur_core.core import filters as core_filters
from waldur_core.core.filters import BaseExternalFilter
from . import models

User = auth.get_user_model()


class BaseApplicationFilter(six.with_metaclass(FilterSetMetaclass, BaseExternalFilter, django_filters.FilterSet)):
    project = django_filters.UUIDFilter(name='project__uuid')
    project_uuid = django_filters.UUIDFilter(name='project__uuid')
    project_name = django_filters.CharFilter(name='project__name', lookup_expr='icontains')

    class Meta(object):
        model = models.ApplicationModel
        fields = (
            'project', 'project_uuid', 'project_name',
        )


class ApplicationSummaryFilterBackend(core_filters.SummaryFilter):

    def get_queryset_filter(self, queryset):
        return BaseApplicationFilter

    def get_base_filter(self):
        return BaseApplicationFilter
