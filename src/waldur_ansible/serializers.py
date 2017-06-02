from __future__ import unicode_literals

from zipfile import is_zipfile, ZipFile

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
    parameters = PlaybookParameterSerializer(many=True)

    class Meta(object):
        model = models.Playbook
        fields = ('url', 'uuid', 'name', 'description', 'zip_file', 'entrypoint', 'parameters')
        protected_fields = ('zip_file', 'entrypoint', 'parameters')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
        }

    def validate_zip_file(self, value):
        if not is_zipfile(value):
            raise serializers.ValidationError(_('ZIP file must be uploaded.'))
        elif not value.name.endswith('.zip'):
            raise serializers.ValidationError(_("File must have '.zip' extension."))
        return value

    def validate(self, attrs):
        if self.instance:
            return attrs

        zip_file = ZipFile(attrs['zip_file'])
        entrypoint = attrs['entrypoint']
        if entrypoint not in zip_file.namelist():
            raise serializers.ValidationError(_('Failed to find entrypoint %s in zip file.' % entrypoint))

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        parameters_data = validated_data.pop('parameters')

        playbook = models.Playbook.objects.create(**validated_data)
        for parameter_data in parameters_data:
            models.PlaybookParameter.objects.create(playbook=playbook, **parameter_data)

        return playbook
