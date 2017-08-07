from __future__ import unicode_literals

from zipfile import is_zipfile, ZipFile

from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions

from nodeconductor.core import models as core_models
from nodeconductor.core.utils import get_detail_view_name
from nodeconductor.core.serializers import AugmentedSerializerMixin, JSONField
from nodeconductor.structure.permissions import _has_manager_access
from nodeconductor.structure.serializers import PermissionFieldFilteringMixin
from nodeconductor_openstack.openstack_tenant import models as openstack_models

from . import models


class PlaybookParameterSerializer(serializers.ModelSerializer):
    name = serializers.RegexField('^[\w]+$')

    class Meta(object):
        model = models.PlaybookParameter
        fields = ('name', 'description', 'required', 'default')


class PlaybookSerializer(AugmentedSerializerMixin, serializers.HyperlinkedModelSerializer):
    archive = serializers.FileField(write_only=True)
    parameters = PlaybookParameterSerializer(many=True)

    class Meta(object):
        model = models.Playbook
        fields = ('url', 'uuid', 'name', 'description', 'archive', 'entrypoint', 'parameters', 'image')
        protected_fields = ('entrypoint', 'parameters', 'archive')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
        }

    def validate_archive(self, value):
        if not is_zipfile(value):
            raise serializers.ValidationError(_('ZIP file must be uploaded.'))
        elif not value.name.endswith('.zip'):
            raise serializers.ValidationError(_("File must have '.zip' extension."))

        zip_file = ZipFile(value)
        invalid_file = zip_file.testzip()
        if invalid_file is not None:
            raise serializers.ValidationError(
                _('File {filename} in archive {archive_name} has an invalid type.'.format(
                    filename=invalid_file, archive_name=zip_file.filename)))

        return value

    def validate(self, attrs):
        if self.instance:
            return attrs

        zip_file = ZipFile(attrs['archive'])
        entrypoint = attrs['entrypoint']
        if entrypoint not in zip_file.namelist():
            raise serializers.ValidationError(
                _('Failed to find entrypoint {entrypoint} in archive {archive_name}.'.format(
                    entrypoint=entrypoint, archive_name=zip_file.filename)))

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        parameters_data = validated_data.pop('parameters')
        archive = validated_data.pop('archive')
        validated_data['workspace'] = models.Playbook.generate_workspace_path()

        zip_file = ZipFile(archive)
        zip_file.extractall(validated_data['workspace'])
        zip_file.close()

        playbook = models.Playbook.objects.create(**validated_data)
        for parameter_data in parameters_data:
            models.PlaybookParameter.objects.create(playbook=playbook, **parameter_data)

        return playbook


class JobSerializer(AugmentedSerializerMixin,
                    PermissionFieldFilteringMixin,
                    serializers.HyperlinkedModelSerializer):
    service_project_link = serializers.HyperlinkedRelatedField(
        lookup_field='pk',
        view_name='openstacktenant-spl-detail',
        queryset=openstack_models.OpenStackTenantServiceProjectLink.objects.all(),
    )
    ssh_public_key = serializers.HyperlinkedRelatedField(
        lookup_field='uuid',
        view_name='sshpublickey-detail',
        queryset=core_models.SshPublicKey.objects.all(),
    )
    project = serializers.HyperlinkedRelatedField(
        source='service_project_link.project',
        lookup_field='uuid',
        view_name='project-detail',
        read_only=True,
    )
    project_name = serializers.ReadOnlyField(source='service_project_link.project.name')
    project_uuid = serializers.ReadOnlyField(source='service_project_link.project.uuid')
    playbook = serializers.HyperlinkedRelatedField(
        lookup_field='uuid',
        view_name=get_detail_view_name(models.Playbook),
        queryset=models.Playbook.objects.all(),
    )
    playbook_name = serializers.ReadOnlyField(source='playbook.name')
    playbook_uuid = serializers.ReadOnlyField(source='playbook.uuid')
    arguments = JSONField(default={})
    state = serializers.SerializerMethodField()

    class Meta(object):
        model = models.Job
        fields = ('url', 'uuid', 'name', 'description',
                  'service_project_link', 'ssh_public_key',
                  'project', 'project_name', 'project_uuid',
                  'playbook', 'playbook_name', 'playbook_uuid',
                  'arguments', 'state', 'output', 'created', 'modified')
        read_only_fields = ('output', 'created', 'modified')
        protected_fields = ('service_project_link', 'ssh_public_key', 'playbook', 'arguments')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
        }

    def get_filtered_field_names(self):
        return 'project', 'service_project_link', 'ssh_public_key'

    def get_state(self, obj):
        return obj.get_state_display()

    def check_project(self, attrs):
        if self.instance:
            project = self.instance.service_project_link.project
        else:
            project = attrs['service_project_link'].project
        if not _has_manager_access(self.context['request'].user, project):
            raise exceptions.PermissionDenied()

    def check_arguments(self, attrs):
        playbook = self.instance.playbook if self.instance else attrs['playbook']
        arguments = attrs['arguments']
        parameter_names = playbook.parameters.all().values_list('name', flat=True)
        for argument in arguments.keys():
            if argument not in parameter_names and argument != 'project_uuid':
                raise serializers.ValidationError(_('Argument %s is not listed in playbook parameters.' % argument))

        if playbook.parameters.exclude(name__in=arguments.keys()).filter(required=True, default__exact='').exists():
            raise serializers.ValidationError(_('Not all required playbook parameters were specified.'))

        unfilled_parameters = playbook.parameters.exclude(name__in=arguments.keys())
        for parameter in unfilled_parameters:
            if parameter.default:
                arguments[parameter.name] = parameter.default

    def check_subnet(self, attrs):
        if not self.instance:
            settings = attrs['service_project_link'].service.settings
            if not openstack_models.SubNet.objects.filter(settings=settings).exists():
                raise serializers.ValidationError(_('Selected OpenStack provider does not have any subnet yet.'))
            else:
                attrs['subnet'] = openstack_models.SubNet.objects.filter(settings=settings).first()

    def validate(self, attrs):
        if not self.instance:
            attrs['user'] = self.context['request'].user

        self.check_project(attrs)
        self.check_arguments(attrs)
        self.check_subnet(attrs)
        return attrs
