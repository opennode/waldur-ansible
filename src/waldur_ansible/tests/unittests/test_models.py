from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.test import TestCase

from ..factories import PlaybookFactory, PlaybookParameterFactory


class PlaybookTest(TestCase):
    def test_file_is_renamed_after_upload(self):
        zip_file = ContentFile('file content', name='playbook.zip')
        playbook = PlaybookFactory(archive=zip_file)
        self.assertNotEqual(zip_file.name, playbook.archive.name)

    def test_renamed_file_extension_is_zip(self):
        zip_file = ContentFile('file content', name='playbook.zip')
        playbook = PlaybookFactory(archive=zip_file)
        self.assertTrue(playbook.archive.name.endswith('.zip'))


class PlaybookParameterTest(TestCase):
    def setUp(self):
        self.playbook = PlaybookFactory()

    def test_cannot_create_parameters_with_same_name_for_same_playbook(self):
        param = PlaybookParameterFactory(playbook=self.playbook)
        self.assertRaises(IntegrityError, PlaybookParameterFactory, playbook=self.playbook, name=param.name)
