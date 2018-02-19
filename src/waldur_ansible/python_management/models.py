from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from waldur_ansible.common import models as common_models

from waldur_core.core import models as core_models, fields as core_fields
from waldur_core.core.validators import validate_name
from waldur_core.structure import models as structure_models

User = get_user_model()

@python_2_unicode_compatible
class PythonManagement(core_models.UuidMixin, TimeStampedModel, common_models.ApplicationModel):
    user = models.ForeignKey(User, related_name='+')
    virtual_envs_dir_path = models.CharField(max_length=255)
    python_version = models.CharField(max_length=10)
    system_user = models.CharField(max_length=255, null=True)

    instance_content_type = models.ForeignKey(ContentType, null=True, related_name='+')
    instance_object_id = models.PositiveIntegerField(null=True)
    instance = GenericForeignKey('instance_content_type', 'instance_object_id')

    project = models.ForeignKey(structure_models.Project, null=True, related_name='+')

    class Permissions:
        project_path = 'project'
        customer_path = 'project__customer'

    class Meta:
        unique_together = (('instance_content_type', 'instance_object_id', 'virtual_envs_dir_path', 'system_user'),)

    @staticmethod
    def get_url_name():
        return 'python_management'

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class VirtualEnvironment(core_models.UuidMixin, core_models.NameMixin, models.Model):
    python_management = models.ForeignKey(PythonManagement, on_delete=models.CASCADE, related_name='virtual_environments')
    jupyter_hub_global = models.BooleanField(default=False)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class InstalledLibrary(core_models.UuidMixin, core_models.NameMixin, models.Model):
    virtual_environment = models.ForeignKey(VirtualEnvironment, on_delete=models.CASCADE, related_name='installed_libraries')
    version = models.CharField(max_length=255)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


class PythonManagementRequest(core_models.UuidMixin, core_models.StateMixin, TimeStampedModel, common_models.OutputStoring):
    python_management = models.ForeignKey(PythonManagement, on_delete=models.CASCADE, related_name='+')

    class Meta(object):
        abstract = True

    def get_backend(self):
        from waldur_ansible.python_management.backend.python_management_backend import PythonManagementBackend
        return PythonManagementBackend()


@python_2_unicode_compatible
class PythonManagementInitializeRequest(PythonManagementRequest):

    # holds sychronization_requests One-To-Many relation

    def get_backend(self):
        from waldur_ansible.python_management.backend.python_management_backend import PythonManagementInitializationBackend
        return PythonManagementInitializationBackend()

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class PythonManagementSynchronizeRequest(common_models.RelatedToVirtualEnv, PythonManagementRequest):
    libraries_to_install = core_fields.JSONField(default=[], help_text=_('List of libraries to install'), blank=True)
    libraries_to_remove = core_fields.JSONField(default=[], help_text=_('List of libraries to remove'), blank=True)
    initialization_request = models.ForeignKey(PythonManagementInitializeRequest, related_name="sychronization_requests", null=True)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class PythonManagementDeleteRequest(common_models.RelatedToVirtualEnv, PythonManagementRequest):

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class PythonManagementDeleteVirtualEnvRequest(common_models.RelatedToVirtualEnv, PythonManagementRequest):

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class PythonManagementFindVirtualEnvsRequest(common_models.RelatedToVirtualEnv, PythonManagementRequest):

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class PythonManagementFindInstalledLibrariesRequest(common_models.RelatedToVirtualEnv, PythonManagementRequest):

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class CachedRepositoryPythonLibrary(core_models.UuidMixin, models.Model):
    name = models.CharField(max_length=255, validators=[validate_name], db_index=True)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)
