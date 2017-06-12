from nodeconductor.core.executors import ActionExecutor
from nodeconductor.core import tasks as core_tasks


class RunJobExecutor(ActionExecutor):
    @classmethod
    def pre_apply(cls, job, **kwargs):
        job.schedule_running()
        job.save(update_fields=['state'])

    @classmethod
    def get_task_signature(cls, job, serialized_job, **kwargs):
        return core_tasks.BackendMethodTask().si(
            serialized_job, 'run_job', state_transition='begin_running')
