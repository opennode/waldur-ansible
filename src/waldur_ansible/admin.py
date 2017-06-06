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


class PlaybookAdminForm(forms.ModelForm):
    def clean_archive(self):
        value = self.cleaned_data['archive']
        if not is_zipfile(value):
            raise ValidationError(_('ZIP file must be uploaded.'))
        elif not value.name.endswith('.zip'):
            raise ValidationError(_("File must have '.zip' extension."))
        return value

    def clean(self):
        cleaned_data = super(PlaybookAdminForm, self).clean()
        archive = cleaned_data.get('archive')
        entrypoint = cleaned_data.get('entrypoint')
        if self.errors or not (archive and entrypoint):
            return

        zip_file = ZipFile(archive)
        if entrypoint not in zip_file.namelist():
            raise ValidationError(_('Failed to find entrypoint %s in archive.' % entrypoint))


class PlaybookAdmin(admin.ModelAdmin):
    list_filter = ('name', 'description')
    list_display = ('name', 'description')
    form = PlaybookAdminForm

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return self.readonly_fields + ('archive', 'entrypoint')
        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = [AddPlaybookParameterInline]
        return super(PlaybookAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.inlines = [ChangePlaybookParameterInline]
        return super(PlaybookAdmin, self).change_view(request, object_id, form_url, extra_context)


class JobAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'arguments': JSONEditor(),
        }

    def clean(self):
        cleaned_data = super(JobAdminForm, self).clean()
        playbook = cleaned_data.get('playbook')
        arguments = cleaned_data.get('arguments')
        if self.errors or not (playbook and arguments):
            return

        arguments = json.loads(arguments)
        parameter_names = playbook.parameters.all().values_list('name', flat=True)
        for argument in arguments.keys():
            if argument not in parameter_names:
                raise ValidationError(_('Argument %s is not listed in playbook parameters.' % argument))

        if playbook.parameters.exclude(name__in=arguments.keys()).filter(required=True, default__exact='').exists():
            raise ValidationError(_('Not all required playbook parameters were specified.'))

        return cleaned_data


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
