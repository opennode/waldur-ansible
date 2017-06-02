from zipfile import ZipFile

from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework.serializers import ValidationError
from waldur_ansible import serializers


class PlaybookSerializerTest(TestCase):
    def test_valid_playbook_should_succeed(self):
        data = self._get_data()
        serializer = serializers.PlaybookSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            self.fail(e)

    def test_playbook_with_invalid_file_extension_should_fail(self):
        data = self._get_data(filename='playbook.invalid')
        serializer = serializers.PlaybookSerializer(data=data)
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)

    def test_playbook_with_invalid_file_type_should_fail(self):
        data = self._get_data()
        data['zip_file'] = ContentFile('content', name='playbook.zip')
        serializer = serializers.PlaybookSerializer(data=data)
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)

    def test_playbook_with_invalid_entrypoint_should_fail(self):
        data = self._get_data()
        data['entrypoint'] = 'invalid'
        serializer = serializers.PlaybookSerializer(data=data)
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)

    def _get_data(self, filename='playbook.zip'):
        temp_file = ContentFile('file content', name=filename)
        zip_file = ZipFile(temp_file, 'w')
        zip_file.writestr('main.yml', 'test')
        zip_file.close()
        temp_file.seek(0)

        return {
            'name': 'test playbook',
            'zip_file': temp_file,
            'entrypoint': 'main.yml',
            'parameters': [
                {
                    'name': 'parameter1',
                },
                {
                    'name': 'parameter2',
                },
            ]
        }


class PlaybookParameterSerializerTest(TestCase):
    def test_parameter_with_invalid_name_format_should_fail(self):
        data = {
            'name': 'parameter name with spaces'
        }
        serializer = serializers.PlaybookParameterSerializer(data=data)
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)

    def test_parameter_with_valid_name_format_should_succeed(self):
        data = {
            'name': 'parameter1'
        }
        serializer = serializers.PlaybookParameterSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            self.fail(e)
