from __future__ import unicode_literals

from zipfile import is_zipfile

from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, validators

from nodeconductor.core.serializers import AugmentedSerializerMixin

from . import models


class PlaybookParameterSerializer(serializers.ModelSerializer):
    name = serializers.RegexField('^[\w]+$')

    class Meta(object):
        model = models.PlaybookParameter
        fields = ('name', 'description', 'is_required', 'default')


class PlaybookSerializer(AugmentedSerializerMixin, serializers.HyperlinkedModelSerializer):
    file = serializers.FileField(write_only=True)
    parameters = PlaybookParameterSerializer(many=True)

    class Meta(object):
        model = models.Playbook
        fields = ('url', 'uuid', 'name', 'description', 'file', 'parameters')
        protected_fields = ('file', 'parameters')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
        }

    def validate_file(self, value):
        if not is_zipfile(value):
            raise serializers.ValidationError(_('ZIP file must be uploaded.'))
        elif not value.name.endswith('.zip'):
            raise serializers.ValidationError(_("File must have '.zip' extension."))
        return value

    @transaction.atomic
    def create(self, validated_data):
        parameters_data = validated_data.pop('parameters')

        playbook = models.Playbook.objects.create(**validated_data)
        for parameter_data in parameters_data:
            models.PlaybookParameter.objects.create(playbook=playbook, **parameter_data)

        return playbook
