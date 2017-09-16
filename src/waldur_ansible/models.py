from __future__ import unicode_literals
import os
import re
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.translation import ugettext_lazy as _
from django_fsm import transition, FSMIntegerField
from model_utils import FieldTracker
from model_utils.models import TimeStampedModel

from nodeconductor.core.fields import JSONField
from nodeconductor.core.models import NameMixin, DescribableMixin, UuidMixin, SshPublicKey
from nodeconductor_openstack.openstack_tenant import models as openstack_models

from .backend import AnsibleBackend


User = get_user_model()


def get_upload_path(instance, filename):
    return '%s/%s.png' % (instance._meta.model_name, instance.uuid.hex)


@python_2_unicode_compatible
class Playbook(UuidMixin, NameMixin, DescribableMixin, models.Model):
    workspace = models.CharField(max_length=255, unique=True, help_text=_('Absolute path to the playbook workspace.'))
    entrypoint = models.CharField(max_length=255, help_text=_('Relative path to the file in the workspace to execute.'))
    image = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    tracker = FieldTracker()

    @staticmethod
    def get_url_name():
        return 'ansible_playbook'

    @staticmethod
    def generate_workspace_path():
        base_path = os.path.join(
            settings.MEDIA_ROOT,
            settings.WALDUR_ANSIBLE.get('PLAYBOOKS_DIR_NAME', 'ansible_playbooks'),
        )
        path = os.path.join(base_path, uuid.uuid4().hex)
        while os.path.exists(path):
            path = os.path.join(base_path, uuid.uuid4().hex)

        return path

    def get_backend(self):
        return AnsibleBackend(self)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class PlaybookParameter(DescribableMixin, models.Model):
    class Meta(object):
        unique_together = ('playbook', 'name')
        ordering = ['order']

    name = models.CharField(
        max_length=255,
        validators=[validators.RegexValidator(re.compile('^[\w]+$'), _('Enter a valid name.'))],
        help_text=_('Required. 255 characters or fewer. Letters, numbers and _ characters'),
    )
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, related_name='parameters')
    required = models.BooleanField(default=False)
    default = models.CharField(max_length=255, blank=True, help_text=_('Default argument for this parameter.'))
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Job(UuidMixin, NameMixin, DescribableMixin, TimeStampedModel, models.Model):
    class Meta(object):
        pass

    class States(object):
        SCHEDULED = 1
        EXECUTING = 2
        OK = 3
        ERRED = 4

        CHOICES = (
            (SCHEDULED, _('Scheduled')),
            (EXECUTING, _('Executing')),
            (OK, _('OK')),
            (ERRED, _('Erred')),
        )

    class Permissions(object):
        project_path = 'service_project_link__project'
        customer_path = 'service_project_link__project__customer'

    user = models.ForeignKey(User, related_name='+')
    ssh_public_key = models.ForeignKey(SshPublicKey, related_name='+')
    service_project_link = models.ForeignKey(openstack_models.OpenStackTenantServiceProjectLink, related_name='+')
    subnet = models.ForeignKey(openstack_models.SubNet, related_name='+')
    playbook = models.ForeignKey(Playbook, related_name='jobs')
    arguments = JSONField(default={}, blank=True, null=True)
    output = models.TextField(blank=True)
    state = FSMIntegerField(
        default=States.SCHEDULED,
        choices=States.CHOICES,
    )

    @staticmethod
    def get_url_name():
        return 'ansible_job'

    def get_backend(self):
        return self.playbook.get_backend()

    @transition(field=state, source=States.SCHEDULED, target=States.EXECUTING)
    def begin_executing(self):
        pass

    @transition(field=state, source=States.EXECUTING, target=States.OK)
    def set_ok(self):
        pass

    @transition(field=state, source=States.EXECUTING, target=States.ERRED)
    def set_erred(self):
        pass

    @property
    def human_readable_state(self):
        return force_text(dict(self.States.CHOICES)[self.state])

    def __str__(self):
        return self.name

    def get_tag(self):
        return 'job:%s' % self.uuid.hex
