from celery import chain

from nodeconductor.core.executors import BaseExecutor
from nodeconductor.core import tasks as core_tasks


class RunJobExecutor(BaseExecutor):
    @classmethod
    def pre_apply(cls, job, **kwargs):
        job.schedule_running()
        job.save(update_fields=['state'])

    @classmethod
    def get_task_signature(cls, job, serialized_job, **kwargs):
        return chain(
            core_tasks.IndependentBackendMethodTask().si(
                serialized_job, 'unpack_playbook', state_transition='begin_running'),
            core_tasks.BackendMethodTask().si(serialized_job, 'run_job'),
        )

    @classmethod
    def get_failure_signature(cls, job, serialized_job, **kwargs):
        return chain(
            core_tasks.IndependentBackendMethodTask().si(serialized_job, 'delete_playbook'),
            core_tasks.StateTransitionTask().si(serialized_job, state_transition='set_erred')
        )

    @classmethod
    def get_success_signature(cls, job, serialized_job, **kwargs):
        return chain(
            core_tasks.IndependentBackendMethodTask().si(serialized_job, 'delete_playbook'),
            core_tasks.StateTransitionTask().si(serialized_job, state_transition='set_ok')
        )
