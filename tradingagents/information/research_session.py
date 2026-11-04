"""Opt-in manual collection bridge; backup precedes all canonical writes."""

import argparse
import json
import sqlite3
from pathlib import Path

import requests

from tradingagents.information.adaptive_discovery import research
from tradingagents.information.polling import job_lock
from tradingagents.information.store import SQLiteInformationStore


def collect(path, backup, *, run_id, session, now=None, clock=None):
    """Require an existing store and a new backup, under the collector lock.

    On failure retain both files for inspection; never automatically overwrite
    the canonical store with a backup. All writers must honor the same lock.
    """
    path, backup = Path(path).resolve(), Path(backup).resolve()
    if not path.is_file() or backup.exists() or path == backup:
        raise ValueError('existing store and unused distinct backup path required')
    store = SQLiteInformationStore(path, read_only=True)
    with job_lock(store):
        with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as source:
            if source.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('canonical integrity check failed')
            # Exclusive creation prevents accidental replacement of prior backups.
            with backup.open('xb'):
                pass
            with sqlite3.connect(backup) as destination:
                source.backup(destination)
                if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('backup integrity check failed')
        writable = SQLiteInformationStore(path)
        result = research(writable, run_id=run_id, session=session, now=now, clock=clock)
        with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as connection:
            if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('post-collection integrity failed; preserve backup')
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--allow-canonical-write', action='store_true')
    args = parser.parse_args(argv)
    if not args.allow_canonical_write:
        parser.error('explicit --allow-canonical-write required')
    with requests.Session() as session:
        result = collect(args.store, args.backup, run_id=args.run_id, session=session)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
