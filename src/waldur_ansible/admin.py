from zipfile import is_zipfile, ZipFile

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from . import models


class ChangePlaybookParameterInline(admin.TabularInline):
    model = models.PlaybookParameter
    extra = 0
    readonly_fields = ('name', 'description', 'is_required', 'default')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class AddPlaybookParameterInline(admin.TabularInline):
    model = models.PlaybookParameter
    extra = 3
    fields = ('name', 'description', 'is_required', 'default')


class PlaybookAdminForm(forms.ModelForm):
    def clean_file(self):
        value = self.cleaned_data['zip_file']
        if not is_zipfile(value):
            raise ValidationError(_('ZIP file must be uploaded.'))
        elif not value.name.endswith('.zip'):
            raise ValidationError(_("File must have '.zip' extension."))
        return value

    def clean(self):
        if self.errors or self.instance:
            return super(PlaybookAdminForm, self).clean()

        zip_file = ZipFile(self.cleaned_data['zip_file'])
        entrypoint = self.cleaned_data['entrypoint']
        if entrypoint not in zip_file.namelist():
            raise ValidationError(_('Failed to find entrypoint %s in zip file.' % entrypoint))

        return super(PlaybookAdminForm, self).clean()


class PlaybookAdmin(admin.ModelAdmin):
    list_filter = ('name', 'description')
    list_display = ('name', 'description')
    form = PlaybookAdminForm

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return self.readonly_fields + ('zip_file', 'entrypoint')
        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = [AddPlaybookParameterInline]
        return super(PlaybookAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.inlines = [ChangePlaybookParameterInline]
        return super(PlaybookAdmin, self).change_view(request, object_id, form_url, extra_context)


admin.site.register(models.Playbook, PlaybookAdmin)
