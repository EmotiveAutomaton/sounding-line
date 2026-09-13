"""Locally validated controller runtime; checks allocate no provider resources.

DESIGN CHECK: LESSONS3-5. Unsupported SDKs refuse before reservation under
both hypotheses. Version and used signatures are measured, never inferred.
"""
import importlib.metadata
import inspect
import sys

MODAL_VERSION = '1.5.4'
PYTHON_VERSION = (3, 13, 2)


def validate_runtime():
    version = importlib.metadata.version('modal')
    if version != MODAL_VERSION or sys.version_info[:3] != PYTHON_VERSION:
        raise ValueError('unvalidated Gear 3 controller Python/Modal runtime')
    import modal
    from modal._utils.async_utils import synchronizer
    from modal_proto import api_pb2
    contracts = [(modal.FunctionCall.cancel, {'terminate_containers'}),
                 (modal.App.run, {'client', 'environment_name', 'detach'}),
                 (modal.Volume.from_name, {'client', 'environment_name', 'create_if_missing'})]
    signatures = {}
    for fn, required in contracts:
        signature = inspect.signature(fn)
        if not required <= set(signature.parameters):
            raise ValueError('unsupported provider adapter signature')
        signatures[fn.__qualname__] = str(signature)
    if not callable(synchronizer.create_blocking):
        raise ValueError('unsupported provider synchronizer')
    if set(api_pb2.AppStopRequest.DESCRIPTOR.fields_by_name) != {'app_id', 'source'}:
        raise ValueError('unsupported AppStop request')
    api_pb2.TokenInfoGetRequest()
    return {'python': sys.version.split()[0], 'modal': version, 'signatures': signatures}
