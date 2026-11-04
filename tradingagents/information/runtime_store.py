"""Explicit existing-store selection for operational entry points."""

import os
from pathlib import Path


def runtime_store_path(value=None):
    """Reject CWD-dependent paths and missing stores; never bootstrap production.

    Explicit caller configuration wins over the shared opt-in environment value.
    Low-level SQLiteInformationStore remains available for intentional creation.
    """
    value = value or os.environ.get('TRADINGAGENTS_INFORMATION_STORE_PATH')
    if not value:
        raise ValueError('explicit existing information store path required')
    path = Path(value)
    if not path.is_absolute():
        raise ValueError('absolute information store path required')
    if not path.is_file():
        raise ValueError('existing information store required; refusing creation')
    return path.resolve()
