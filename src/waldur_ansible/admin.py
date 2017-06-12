import json

from zipfile import is_zipfile, ZipFile

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from jsoneditor.forms import JSONEditor

from nodeconductor.core.admin import ExecutorAdminAction

from . import models, executors


class ChangePlaybookParameterInline(admin.TabularInline):
    model = models.PlaybookParameter
    extra = 0
    readonly_fields = ('name', 'description', 'required', 'default')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class AddPlaybookParameterInline(admin.TabularInline):
    model = models.PlaybookParameter
    extra = 3
    fields = ('name', 'description', 'required', 'default')


class ChangePlaybookAdminForm(forms.ModelForm):
    class Meta:
        model = models.Playbook
        fields = ('name', 'description', 'entrypoint')


class AddPlaybookAdminForm(forms.ModelForm):
    archive = forms.FileField()

    class Meta:
        model = models.Playbook
        fields = ('name', 'description', 'entrypoint')

    def clean_archive(self):
        value = self.cleaned_data['archive']
        if not is_zipfile(value):
            raise ValidationError(_('ZIP file must be uploaded.'))
        elif not value.name.endswith('.zip'):
            raise ValidationError(_("File must have '.zip' extension."))

        zip_file = ZipFile(value)
        invalid_file = zip_file.testzip()
        if invalid_file is not None:
            raise ValidationError(
                _('File {filename} in archive {archive_name} has an invalid type.'.format(
                    filename=invalid_file, archive_name=zip_file.filename)))

        return value

    def clean(self):
        cleaned_data = super(AddPlaybookAdminForm, self).clean()
        if self.errors:
            return cleaned_data

        archive = cleaned_data['archive']
        entrypoint = cleaned_data['entrypoint']

        zip_file = ZipFile(archive)
        if entrypoint not in zip_file.namelist():
            raise ValidationError(
                _('Failed to find entrypoint {entrypoint} in archive {archive_name}.'.format(
                    entrypoint=entrypoint, archive_name=zip_file.filename)))

        return cleaned_data

    def save(self, commit=True):
        self.instance.workspace = models.Playbook.generate_workspace_path()
        archive = self.cleaned_data.pop('archive')
        zip_file = ZipFile(archive)
        zip_file.extractall(self.instance.workspace)
        zip_file.close()

        return super(AddPlaybookAdminForm, self).save(commit)


class PlaybookAdmin(admin.ModelAdmin):
    list_filter = ('name', 'description')
    list_display = ('name', 'description')

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return self.readonly_fields + ('entrypoint',)
        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = [AddPlaybookParameterInline]
        self.form = AddPlaybookAdminForm
        return super(PlaybookAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.inlines = [ChangePlaybookParameterInline]
        self.form = ChangePlaybookAdminForm
        return super(PlaybookAdmin, self).change_view(request, object_id, form_url, extra_context)


class JobAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'arguments': JSONEditor(),
        }

    def clean(self):
        cleaned_data = super(JobAdminForm, self).clean()
        if self.errors:
            return cleaned_data

        if self.instance and self.instance.pk:
            playbook = self.instance.playbook
        else:
            playbook = cleaned_data['playbook']

        arguments = json.loads(cleaned_data.get('arguments'))
        parameter_names = playbook.parameters.all().values_list('name', flat=True)
        for argument in arguments.keys():
            if argument not in parameter_names and argument != 'project_uuid':
                raise ValidationError(_('Argument %s is not listed in playbook parameters.' % argument))

        if playbook.parameters.exclude(name__in=arguments.keys()).filter(required=True, default__exact='').exists():
            raise ValidationError(_('Not all required playbook parameters were specified.'))

        return cleaned_data

    def save(self, commit=True):
        arguments = self.instance.arguments
        playbook = self.instance.playbook
        unfilled_parameters = playbook.parameters.exclude(name__in=arguments.keys())
        for parameter in unfilled_parameters:
            if parameter.default:
                arguments[parameter.name] = parameter.default
        arguments['project_uuid'] = self.instance.project.uuid.hex
        return super(JobAdminForm, self).save(commit)


class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    fields = ('name', 'description', 'state', 'project',
              'playbook', 'arguments', 'output')
    list_filter = ('name', 'description', 'project', 'playbook')
    list_display = ('name', 'state', 'project', 'playbook')
    readonly_fields = ('output', 'created', 'modified')
    actions = ['execute']

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return self.readonly_fields + ('project', 'playbook')
        return self.readonly_fields

    class Execute(ExecutorAdminAction):
        executor = executors.RunJobExecutor
        short_description = _('Execute')

        def validate(self, job):
            States = models.Job.States
            if job.state not in (States.OK, States.ERRED):
                raise ValidationError(_('Job has to be OK or erred.'))

    execute = Execute()


admin.site.register(models.Playbook, PlaybookAdmin)
admin.site.register(models.Job, JobAdmin)
