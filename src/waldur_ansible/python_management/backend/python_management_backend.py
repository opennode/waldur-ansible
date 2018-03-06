import json
import logging
import os
import subprocess  # nosec

import six
from django.conf import settings
from waldur_ansible.playbook_jobs.backend import exceptions
from waldur_ansible.python_management import models, constants, executors

from waldur_core.core.views import RefreshTokenMixin
from . import output_lines_post_processors, locking_service, extracted_information_handlers, additional_extra_args_builders

logger = logging.getLogger(__name__)


class PythonManagementBackend(object):

    def process_python_management_request(self, python_management_request):
        PythonManagementBackendHelper.process_request(python_management_request)


class PythonManagementInitializationBackend(PythonManagementBackend):

    def process_python_management_request(self, python_management_initialization_request):
        super(PythonManagementInitializationBackend, self).process_python_management_request(python_management_initialization_request)

        for synchronization_request in python_management_initialization_request.sychronization_requests.all():
            executors.PythonManagementRequestExecutor.execute(synchronization_request, async=True)


class PythonManagementBackendHelper(object):
    REQUEST_TYPES_PLAYBOOKS_CORRESPONDENCE = {
        models.PythonManagementInitializeRequest: constants.PythonManagementConstants.INSTALL_PYTHON_ENVIRONMENT,
        models.PythonManagementSynchronizeRequest: constants.PythonManagementConstants.SYNCHRONIZE_PACKAGES,
        models.PythonManagementFindVirtualEnvsRequest: constants.PythonManagementConstants.FIND_INSTALLED_VIRTUAL_ENVIRONMENTS,
        models.PythonManagementFindInstalledLibrariesRequest: constants.PythonManagementConstants.FIND_INSTALLED_LIBRARIES_FOR_VIRTUAL_ENVIRONMENT,
        models.PythonManagementDeleteVirtualEnvRequest: constants.PythonManagementConstants.DELETE_VIRTUAL_ENVIRONMENT,
        models.PythonManagementDeleteRequest: constants.PythonManagementConstants.DELETE_PYTHON_ENVIRONMENT,
    }

    REQUEST_TYPES_EXTRA_ARGS_CORRESPONDENCE = {
        models.PythonManagementInitializeRequest: None,
        models.PythonManagementSynchronizeRequest: additional_extra_args_builders.build_sync_request_extra_args,
        models.PythonManagementFindVirtualEnvsRequest: additional_extra_args_builders.build_additional_extra_args,
        models.PythonManagementFindInstalledLibrariesRequest: additional_extra_args_builders.build_additional_extra_args,
        models.PythonManagementDeleteVirtualEnvRequest: additional_extra_args_builders.build_additional_extra_args,
        models.PythonManagementDeleteRequest: None,
    }

    REQUEST_TYPES_POST_PROCESSOR_CORRESPONDENCE = {
        models.PythonManagementInitializeRequest: output_lines_post_processors.InitializationOutputLinesPostProcessor,
        models.PythonManagementSynchronizeRequest: output_lines_post_processors.InstalledLibrariesOutputLinesPostProcessor,
        models.PythonManagementFindVirtualEnvsRequest: output_lines_post_processors.InstalledVirtualEnvironmentsOutputLinesPostProcessor,
        models.PythonManagementFindInstalledLibrariesRequest: output_lines_post_processors.InstalledLibrariesOutputLinesPostProcessor,
        models.PythonManagementDeleteVirtualEnvRequest: output_lines_post_processors.NullOutputLinesPostProcessor,
        models.PythonManagementDeleteRequest: output_lines_post_processors.NullOutputLinesPostProcessor,
    }

    REQUEST_TYPES_HANDLERS_CORRESPONDENCE = {
        models.PythonManagementInitializeRequest: extracted_information_handlers.InitializationRequestExtractedInformationHandler,
        models.PythonManagementSynchronizeRequest: extracted_information_handlers.InstalledLibrariesExtractedInformationHandler,
        models.PythonManagementFindVirtualEnvsRequest: extracted_information_handlers.PythonManagementFindVirtualEnvsRequestExtractedInformationHandler,
        models.PythonManagementFindInstalledLibrariesRequest: extracted_information_handlers.InstalledLibrariesExtractedInformationHandler,
        models.PythonManagementDeleteVirtualEnvRequest: extracted_information_handlers.NullExtractedInformationHandler,
        models.PythonManagementDeleteRequest: extracted_information_handlers.PythonManagementDeletionRequestExtractedInformationHandler,
    }

    LOCKED_FOR_PROCESSING = 'Whole environment or the particular virutal environnment is now being processed, request cannot be executed!'

    @staticmethod
    def process_request(python_management_request):
        if not locking_service.PythonManagementBackendLockingService.is_processing_allowed(python_management_request):
            python_management_request.output = PythonManagementBackendHelper.LOCKED_FOR_PROCESSING
            python_management_request.save(update_fields=['output'])
            return
        try:
            locking_service.PythonManagementBackendLockingService.lock_for_processing(python_management_request)

            command = PythonManagementBackendHelper.build_command(python_management_request)
            command_str = ' '.join(command)

            logger.debug('Executing command "%s".', command_str)
            env = dict(
                os.environ,
                ANSIBLE_LIBRARY=settings.WALDUR_PLAYBOOK_JOBS['ANSIBLE_LIBRARY'],
                ANSIBLE_HOST_KEY_CHECKING='False',
            )
            request_class = type(python_management_request)
            lines_post_processor_instance = PythonManagementBackendHelper.instantiate_line_post_processor_class(
                request_class)
            extracted_information_handler = PythonManagementBackendHelper.instantiate_extracted_information_handler_class(
                request_class)
            try:
                for output_line in PythonManagementBackendHelper.process_output_iterator(command, env):
                    python_management_request.output += output_line
                    python_management_request.save(update_fields=['output'])
                    lines_post_processor_instance.post_process_line(output_line)
            except subprocess.CalledProcessError as e:
                logger.info('Failed to execute command "%s".', command_str)
                six.reraise(exceptions.AnsibleBackendError, e)
            else:
                logger.info('Command "%s" was successfully executed.', command_str)
                extracted_information_handler.handle_extracted_information(
                    python_management_request, lines_post_processor_instance)
        finally:
            locking_service.PythonManagementBackendLockingService.handle_on_processing_finished(python_management_request)

    @staticmethod
    def instantiate_line_post_processor_class(python_management_request_class):
        lines_post_processor_class = PythonManagementBackendHelper.REQUEST_TYPES_POST_PROCESSOR_CORRESPONDENCE \
            .get(python_management_request_class)
        lines_post_processor_instance = lines_post_processor_class()
        return lines_post_processor_instance

    @staticmethod
    def instantiate_extracted_information_handler_class(python_management_request_class):
        extracted_information_handler_class = PythonManagementBackendHelper.REQUEST_TYPES_HANDLERS_CORRESPONDENCE \
            .get(python_management_request_class)
        extracted_information_handler_instance = extracted_information_handler_class()
        return extracted_information_handler_instance

    @staticmethod
    def process_output_iterator(command, env):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1, env=env)  # nosec
        for stdout_line in iter(process.stdout.readline, ""):
            yield stdout_line
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

    @staticmethod
    def build_command(python_management_request):
        playbook_path = settings.WALDUR_PYTHON_MANAGEMENT.get('PYTHON_MANAGEMENT_PLAYBOOKS_DIRECTORY') \
                        + PythonManagementBackendHelper.REQUEST_TYPES_PLAYBOOKS_CORRESPONDENCE.get(type(python_management_request)) \
                        + '.yml'
        PythonManagementBackendHelper.ensure_playbook_exists_or_raise(playbook_path)

        command = [settings.WALDUR_PLAYBOOK_JOBS.get('PLAYBOOK_EXECUTION_COMMAND', 'ansible-playbook')]

        if settings.WALDUR_PLAYBOOK_JOBS.get('PLAYBOOK_ARGUMENTS'):
            command.extend(settings.WALDUR_PLAYBOOK_JOBS.get('PLAYBOOK_ARGUMENTS'))

        command.extend(['--extra-vars', PythonManagementBackendHelper.build_extra_vars(python_management_request)])

        command.extend(['--ssh-common-args', '-o UserKnownHostsFile=/dev/null'])

        return command + [playbook_path]

    @staticmethod
    def ensure_playbook_exists_or_raise(playbook_path):
        if not os.path.exists(playbook_path):
            raise exceptions.AnsibleBackendError('Playbook %s does not exist.' % playbook_path)

    @staticmethod
    def build_extra_vars(python_management_request):
        extra_vars = PythonManagementBackendHelper.build_common_extra_vars(python_management_request)

        additional_extra_args_building_function = PythonManagementBackendHelper.REQUEST_TYPES_EXTRA_ARGS_CORRESPONDENCE.get(type(python_management_request))

        if additional_extra_args_building_function:
            extra_vars.update(additional_extra_args_building_function(python_management_request))

        return json.dumps(extra_vars)

    @staticmethod
    def build_common_extra_vars(python_management_request):
        python_management = python_management_request.python_management
        return dict(
            api_url=settings.WALDUR_PLAYBOOK_JOBS['API_URL'],
            access_token=RefreshTokenMixin().refresh_token(python_management.user).key,
            project_uuid=python_management.service_project_link.project.uuid.hex,
            provider_uuid=python_management.service_project_link.service.uuid.hex,
            private_key_path=settings.WALDUR_PLAYBOOK_JOBS['PRIVATE_KEY_PATH'],
            public_key_uuid=settings.WALDUR_PLAYBOOK_JOBS['PUBLIC_KEY_UUID'],
            default_system_user=PythonManagementBackendHelper.decide_default_system_user(python_management.instance.image_name),
            instance_uuid=python_management.instance.uuid.hex,
            virtual_envs_dir_path=python_management.virtual_envs_dir_path,
        )

    @staticmethod
    def decide_default_system_user(image_name):
        if "debian" in image_name:
            return "debian"
        elif "ubuntu" in image_name:
            return "ubuntu"
        else:
            raise ValueError("Cannot find default user for the installed image")
