from nodeconductor.core import executors as core_executors
from nodeconductor.core import tasks as core_tasks


class RunJobExecutor(core_executors.CreateExecutor):

    @classmethod
    def get_task_signature(cls, job, serialized_job, **kwargs):
        return core_tasks.BackendMethodTask().si(
            serialized_job, 'run_job', state_transition='begin_executing')
