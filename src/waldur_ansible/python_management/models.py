from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from waldur_core.core import models as core_models, fields as core_fields
from waldur_core.core.validators import validate_name
from waldur_openstack.openstack_tenant import models as openstack_models

User = get_user_model()

@python_2_unicode_compatible
class PythonManagement(core_models.UuidMixin, TimeStampedModel, models.Model):
    user = models.ForeignKey(User, related_name='+')
    instance = models.ForeignKey(openstack_models.Instance, related_name='+')
    service_project_link = models.ForeignKey(openstack_models.OpenStackTenantServiceProjectLink, related_name='+')
    virtual_envs_dir_path = models.CharField(max_length=255)
    python_version = models.CharField(max_length=10)

    class Permissions(object):
        project_path = 'service_project_link__project'
        customer_path = 'service_project_link__project__customer'

    class Meta:
        unique_together = (('instance', 'virtual_envs_dir_path'),)

    @staticmethod
    def get_url_name():
        return 'python_management'

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


@python_2_unicode_compatible
class VirtualEnvironment(core_models.UuidMixin, core_models.NameMixin, models.Model):
    python_management = models.ForeignKey(PythonManagement, on_delete=models.CASCADE, related_name='virtual_environments')

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


@python_2_unicode_compatible
class InstalledLibrary(core_models.UuidMixin, core_models.NameMixin, models.Model):
    virtual_environment = models.ForeignKey(VirtualEnvironment, on_delete=models.CASCADE, related_name='installed_libraries')
    version = models.CharField(max_length=255)

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


class PythonManagementRequest(core_models.UuidMixin, core_models.StateMixin, TimeStampedModel):
    python_management = models.ForeignKey(PythonManagement, on_delete=models.CASCADE, related_name='+')

    class Meta(object):
        abstract = True


class RelatedToVirtualEnv(models.Model):
    virtual_env_name = models.CharField(max_length=255)

    class Meta(object):
        abstract = True


class OutputStoring(models.Model):
    output = models.TextField(blank=True)

    class Meta(object):
        abstract = True


class BackendProcessablePythonManagementRequest(object):
    def get_backend(self):
        from waldur_ansible.python_management.backend.python_management_backend import PythonManagementBackend
        return PythonManagementBackend()


@python_2_unicode_compatible
class PythonManagementInitializeRequest(BackendProcessablePythonManagementRequest, OutputStoring, PythonManagementRequest):

    # holds sychronization_requests One-To-Many relation

    def get_backend(self):
        from waldur_ansible.python_management.backend.python_management_backend import PythonManagementInitializationBackend
        return PythonManagementInitializationBackend()

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


@python_2_unicode_compatible
class PythonManagementSynchronizeRequest(BackendProcessablePythonManagementRequest, RelatedToVirtualEnv, OutputStoring, PythonManagementRequest):
    libraries_to_install = core_fields.JSONField(default=[], help_text=_('List of libraries to install'), blank=True)
    libraries_to_remove = core_fields.JSONField(default=[], help_text=_('List of libraries to remove'), blank=True)
    initialization_request = models.ForeignKey(PythonManagementInitializeRequest, related_name="sychronization_requests", null=True)

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


@python_2_unicode_compatible
class PythonManagementDeleteRequest(BackendProcessablePythonManagementRequest, RelatedToVirtualEnv, OutputStoring, PythonManagementRequest):

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


@python_2_unicode_compatible
class PythonManagementDeleteVirtualEnvRequest(BackendProcessablePythonManagementRequest, RelatedToVirtualEnv, OutputStoring, PythonManagementRequest):

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


@python_2_unicode_compatible
class PythonManagementFindVirtualEnvsRequest(BackendProcessablePythonManagementRequest, RelatedToVirtualEnv, OutputStoring, PythonManagementRequest):

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


@python_2_unicode_compatible
class PythonManagementFindInstalledLibrariesRequest(BackendProcessablePythonManagementRequest, RelatedToVirtualEnv, OutputStoring, PythonManagementRequest):

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex


@python_2_unicode_compatible
class CachedRepositoryPythonLibrary(core_models.UuidMixin, models.Model):
    name = models.CharField(max_length=255, validators=[validate_name], db_index=True)

    def __str__(self):
        return self.__class__.__name__ + self.uuid.hex
