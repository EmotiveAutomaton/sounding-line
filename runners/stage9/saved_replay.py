"""Context-local saved-request reconstruction, with no reader fallback.

DESIGN CHECK: B03/X01/X02/X06; LESSONS 3--5, CONTROLS 6--7.
NULL: missing saved calls or requests outside their checkpoint refuse replay.
ALTERNATIVE: the original request constructors can be inspected before any
capsule creation. The explicit handler owns both checkpoints and requests;
ordinary execution has no handler. Nested replay refuses and exit restores
the prior context even on failure. This is not scientific admission.
"""
from contextlib import contextmanager
from contextvars import ContextVar

_handler = ContextVar('stage9_saved_request_replay', default=None)


def active():
    return _handler.get()


@contextmanager
def replaying(handler):
    if handler is None or active() is not None:
        raise ValueError('saved replay requires one explicit nonnested handler')
    token = _handler.set(handler)
    try:
        yield
    finally:
        _handler.reset(token)
