import pickle  # nosec

import six


class AnsibleBackendError(Exception):
    def __init__(self, *args, **kwargs):
        if not args:
            super(AnsibleBackendError, self).__init__(*args, **kwargs)

        # CalledProcessError is not serializable by Celery, because it uses custom arguments *args
        # and define __init__ method, but don't call Exception.__init__ method
        # http://docs.celeryproject.org/en/latest/userguide/tasks.html#creating-pickleable-exceptions
        # That's why when Celery worker tries to deserialize AnsibleBackendError,
        # it uses empty invalid *args. It leads to unrecoverable error and worker dies.
        # When all workers are dead, all tasks are stuck in pending state forever.
        # In order to fix this issue we serialize exception to text type explicitly.
        args = list(args)
        for i, arg in enumerate(args):
            try:
                # pickle is used to check celery internal errors serialization,
                # it is safe from security point of view
                pickle.loads(pickle.dumps(arg))  # nosec
            except (pickle.PickleError, TypeError):
                args[i] = six.text_type(arg)

        super(AnsibleBackendError, self).__init__(*args, **kwargs)
