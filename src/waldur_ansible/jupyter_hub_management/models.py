from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django_fsm import FSMIntegerField
from model_utils.models import TimeStampedModel
from waldur_ansible.common import models as common_models
from waldur_ansible.python_management import models as python_management_models

from waldur_core.core import models as core_models
from waldur_core.structure import models as structure_models

User = get_user_model()


class JupyterHubOAuthType(object):
    # these numbers are important for both frontend and ansible playbook logic
    GITLAB = 1
    AZURE = 2

    CHOICES = (
        (GITLAB, 'GitLab'),
        (AZURE, 'Microsoft Azure'),
    )


@python_2_unicode_compatible
class JupyterHubOAuthConfig(core_models.UuidMixin, models.Model):
    type = FSMIntegerField(choices=JupyterHubOAuthType.CHOICES)

    oauth_callback_url = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    # required for Azure:
    tenant_id = models.CharField(max_length=255, blank=True, null=True)
    gitlab_host = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class JupyterHubManagement(core_models.UuidMixin, TimeStampedModel, common_models.ApplicationModel):
    user = models.ForeignKey(User, related_name='+')
    python_management = models.ForeignKey(python_management_models.PythonManagement, related_name='+')

    session_time_to_live_hours = models.IntegerField(default=24)
    jupyter_hub_oauth_config = models.OneToOneField(
        JupyterHubOAuthConfig,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    instance_content_type = models.ForeignKey(ContentType, null=True, related_name='+')
    instance_object_id = models.PositiveIntegerField(null=True)
    instance = GenericForeignKey('instance_content_type', 'instance_object_id')

    project = models.ForeignKey(structure_models.Project, null=True, related_name='+')

    # holds reference to jupyter_hub_users

    class Meta:
        unique_together = (('instance_content_type', 'instance_object_id',),)

    class Permissions:
        project_path = 'project'
        customer_path = 'project__customer'

    @staticmethod
    def get_url_name():
        return 'jupyter_hub_management'

    def get_admin_users(self):
        return JupyterHubUser.objects.filter(jupyter_hub_management=self, admin=True)

    def get_whitelisted_users(self):
        return JupyterHubUser.objects.filter(jupyter_hub_management=self, whitelisted=True)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class JupyterHubUser(core_models.UuidMixin, models.Model):
    jupyter_hub_management = models.ForeignKey(JupyterHubManagement, on_delete=models.CASCADE, related_name='jupyter_hub_users')
    admin = models.BooleanField(default=False)
    # plays role only in case of OAuth
    whitelisted = models.BooleanField(default=False)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


class JupyterHubManagementRequest(core_models.UuidMixin, core_models.StateMixin, TimeStampedModel, common_models.OutputStoring):
    jupyter_hub_management = models.ForeignKey(JupyterHubManagement, on_delete=models.CASCADE, related_name='+')

    class Meta(object):
        abstract = True

    def get_backend(self):
        from waldur_ansible.jupyter_hub_management.backend.backend import JupyterHubManagementBackend
        return JupyterHubManagementBackend()


@python_2_unicode_compatible
class JupyterHubManagementSyncConfigurationRequest(JupyterHubManagementRequest):

    # holds make_virtual_env_global_requests reference

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class JupyterHubManagementMakeVirtualEnvironmentGlobalRequest(common_models.RelatedToVirtualEnv, JupyterHubManagementRequest):
    update_configuration_request = models.ForeignKey(JupyterHubManagementSyncConfigurationRequest, related_name="make_virtual_env_global_requests", null=True)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class JupyterHubManagementDeleteRequest(JupyterHubManagementRequest):

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)


@python_2_unicode_compatible
class JupyterHubManagementMakeVirtualEnvironmentLocalRequest(common_models.RelatedToVirtualEnv, JupyterHubManagementRequest):

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.uuid.hex)
