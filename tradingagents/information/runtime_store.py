"""Explicit existing-store selection for operational entry points."""

import json
import os
from pathlib import Path

AUTHORITY_FILE = Path(__file__).resolve().parents[2] / '.information-authority.local.json'


def configured_store_path():
    """One private installation config, independent of the launch directory."""
    if not AUTHORITY_FILE.exists():
        return None
    config = json.loads(AUTHORITY_FILE.read_text(encoding='utf-8'))
    if config.get('state') != 'ACTIVE':
        raise ValueError('information authority is not active')
    value = config['information_store_path']
    path = Path(value)
    if not path.is_absolute() or not path.is_file():
        raise ValueError('configured authority must be an existing absolute file')
    return str(path.resolve())


def runtime_store_path(value=None):
    """Reject CWD-dependent paths and missing stores; never bootstrap production.

    Explicit caller configuration wins over the shared opt-in environment value.
    Low-level SQLiteInformationStore remains available for intentional creation.
    """
    authority = configured_store_path()
    value = value or os.environ.get('TRADINGAGENTS_INFORMATION_STORE_PATH') or authority
    if not value:
        raise ValueError('explicit existing information store path required')
    path = Path(value)
    if not path.is_absolute():
        raise ValueError('absolute information store path required')
    if not path.is_file():
        raise ValueError('existing information store required; refusing creation')
    if (authority and path.resolve() != Path(authority)
            and os.environ.get('TRADINGAGENTS_ALLOW_NONCANONICAL_STORE') != '1'):
        raise ValueError('store differs from active authority; explicit legacy opt-in required')
    return path.resolve()
