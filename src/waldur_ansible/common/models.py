from __future__ import unicode_literals

from django.apps import apps
from django.db import models
from django.utils.lru_cache import lru_cache

from waldur_core.structure import models as structure_models


class RelatedToVirtualEnv(models.Model):
    virtual_env_name = models.CharField(max_length=255)

    class Meta(object):
        abstract = True


class OutputStoring(models.Model):
    output = models.TextField(blank=True)

    class Meta(object):
        abstract = True


class ApplicationModel(structure_models.StructureModel):
    class Meta(object):
        abstract = True

    @classmethod
    @lru_cache(maxsize=1)
    def get_application_models(cls):
        return [model for model in apps.get_models() if issubclass(model, cls)]
