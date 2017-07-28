from __future__ import unicode_literals
import os
import re
import uuid

from django.conf import settings
from django.core import validators
from django.db import models
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.translation import ugettext_lazy as _
from django_fsm import transition, FSMIntegerField
from model_utils.models import TimeStampedModel

from nodeconductor.core.fields import JSONField
from nodeconductor.core.models import NameMixin, DescribableMixin, UuidMixin
from nodeconductor.structure.models import Project

from .backend import AnsibleBackend


@python_2_unicode_compatible
class Playbook(UuidMixin, NameMixin, DescribableMixin, models.Model):
    workspace = models.CharField(max_length=255, unique=True, help_text=_('Absolute path to the playbook workspace.'))
    entrypoint = models.CharField(max_length=255, help_text=_('Relative path to the file in the workspace to execute.'))

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
        OK = 1
        ERRED = 2
        RUNNING = 3
        RUN_SCHEDULED = 4

        CHOICES = (
            (RUNNING, _('Running')),
            (RUN_SCHEDULED, _('Run Scheduled')),
            (OK, _('OK')),
            (ERRED, _('Erred')),
        )

    class Permissions(object):
        project_path = 'project'
        customer_path = 'project__customer'

    project = models.ForeignKey(Project, related_name='+')
    playbook = models.ForeignKey(Playbook, related_name='jobs')
    arguments = JSONField(default={}, blank=True, null=True)
    output = models.TextField(blank=True)
    state = FSMIntegerField(
        default=States.OK,
        choices=States.CHOICES,
    )

    @staticmethod
    def get_url_name():
        return 'ansible_job'

    def get_backend(self):
        return self.playbook.get_backend()

    @transition(field=state, source=[States.OK, States.ERRED], target=States.RUN_SCHEDULED)
    def schedule_running(self):
        pass

    @transition(field=state, source=States.RUN_SCHEDULED, target=States.RUNNING)
    def begin_running(self):
        pass

    @transition(field=state, source=States.RUNNING, target=States.OK)
    def set_ok(self):
        pass

    @transition(field=state, source='*', target=States.ERRED)
    def set_erred(self):
        pass

    @property
    def human_readable_state(self):
        return force_text(dict(self.States.CHOICES)[self.state])

    def __str__(self):
        return self.name
