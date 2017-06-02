from __future__ import unicode_literals
import os
import re
import uuid

from django.conf import settings
from django.core import validators
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from nodeconductor.core.models import NameMixin, DescribableMixin, UuidMixin


def get_playbook_path(instance, filename):
    new_filename = '{uuid}.{extension}'.format(
        uuid=uuid.uuid4(),
        extension=filename.split('.')[-1]
    )
    return os.path.join(settings.WALDUR_ANSIBLE.get('PLAYBOOKS_DIR_NAME', 'ansible_playbooks'), new_filename)


@python_2_unicode_compatible
class Playbook(UuidMixin, NameMixin, DescribableMixin, models.Model):
    zip_file = models.FileField(upload_to=get_playbook_path)
    entrypoint = models.CharField(max_length=255, help_text=_('The file to execute in a playbook.'))

    @staticmethod
    def get_url_name():
        return 'ansible_playbook'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class PlaybookParameter(DescribableMixin, models.Model):
    class Meta(object):
        unique_together = ('playbook', 'name')

    name = models.CharField(
        max_length=255,
        validators=[validators.RegexValidator(re.compile('^[\w]+$'), _('Enter a valid name.'))],
        help_text=_('Required. 255 characters or fewer. Letters, numbers and _ characters'),
    )
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, related_name='parameters')
    is_required = models.BooleanField(default=False)
    default = models.CharField(max_length=255, blank=True, help_text=_('Default argument for this parameter.'))

    def __str__(self):
        return self.name
