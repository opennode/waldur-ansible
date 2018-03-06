from django import forms
from django.contrib import admin

from . import models


class AddPlaybookAdminForm(forms.ModelForm):
    class Meta:
        model = models.CachedRepositoryPythonLibrary
        fields = ('name',)


class PlaybookAdmin(admin.ModelAdmin):
    list_filter = ('name',)
    list_display = ('name',)


admin.site.register(models.CachedRepositoryPythonLibrary, PlaybookAdmin)
