from __future__ import unicode_literals

import factory

from rest_framework.reverse import reverse

from nodeconductor.core.utils import get_detail_view_name, get_list_view_name
from nodeconductor.structure import models

from .. import models


class PlaybookFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.Playbook

    name = factory.Sequence(lambda n: 'playbook%s' % n)
    description = factory.Sequence(lambda n: 'Description %s' % n)
    file = factory.django.FileField(filename='playbook.zip')

    @factory.post_generation
    def parameters(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for parameter in extracted:
                self.parameters.add(parameter)
        else:
            PlaybookParameterFactory.create_batch(3, playbook=self)

    @classmethod
    def get_url(cls, playbook=None, action=None):
        if playbook is None:
            playbook = PlaybookFactory()

        url = 'http://testserver' + reverse(get_detail_view_name(models.Playbook), kwargs={'uuid': playbook.uuid})
        return url if action is None else url + action + '/'

    @classmethod
    def get_list_url(cls):
        return 'http://testserver' + reverse(get_list_view_name(models.Playbook))


class PlaybookParameterFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.PlaybookParameter

    playbook = factory.SubFactory(PlaybookFactory)
    name = factory.Sequence(lambda n: 'parameter%s' % n)
    description = factory.Sequence(lambda n: 'Description %s' % n)
    default = factory.Sequence(lambda n: 'Value%s' % n)

