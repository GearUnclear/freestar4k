"""HTTP requests with timeouts and status checks for background weather polling."""

import threading
import requests

from broadcast_support import validate_weather

_local = threading.local()


def response(url, **kwargs):
    if not hasattr(_local, 'session'):
        _local.session = requests.Session()
    result = _local.session.get(url, timeout=(3, 12), **kwargs)
    result.raise_for_status()
    return result


def json_data(url, sections=None, **kwargs):
    data = response(url, **kwargs).json()
    return validate_weather(data, sections) if sections is not None else data
