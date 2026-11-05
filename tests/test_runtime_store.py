import json
from pathlib import Path

import pytest

import tradingagents.information.runtime_store as runtime
from tradingagents.default_config import build_default_config
from tradingagents.information.runtime_store import runtime_store_path
from tradingagents.information.store import SQLiteInformationStore


def test_active_authority_default_and_explicit_override_guard(tmp_path, monkeypatch):
    path = tmp_path / 'production.sqlite3'
    other = tmp_path / 'legacy.sqlite3'
    SQLiteInformationStore(path)
    SQLiteInformationStore(other)
    config = tmp_path / 'authority.json'
    config.write_text(json.dumps({'state': 'ACTIVE', 'information_store_path': str(path)}))
    monkeypatch.setattr(runtime, 'AUTHORITY_FILE', config)
    monkeypatch.delenv('TRADINGAGENTS_INFORMATION_STORE_PATH', raising=False)
    monkeypatch.delenv('TRADINGAGENTS_ALLOW_NONCANONICAL_STORE', raising=False)
    monkeypatch.chdir(tmp_path.parent)
    assert runtime_store_path() == path
    assert build_default_config()['information_store_path'] == str(path)
    with pytest.raises(ValueError, match='active authority'):
        runtime_store_path(other)
    for read_only in (False, True):
        with pytest.raises(ValueError, match='active authority'):
            SQLiteInformationStore(other, read_only=read_only)
    missing = tmp_path / 'accidental.sqlite3'
    with pytest.raises(ValueError, match='refusing creation'):
        SQLiteInformationStore(missing)
    assert not missing.exists()
    monkeypatch.setenv('TRADINGAGENTS_ALLOW_NONCANONICAL_STORE', '1')
    assert runtime_store_path(other) == other
    config.write_text(json.dumps({'state': 'PREPARED', 'information_store_path': str(path)}))
    with pytest.raises(ValueError, match='not active'):
        runtime_store_path()


def test_shared_opt_in_is_independent_of_cwd(tmp_path, monkeypatch):
    path = tmp_path / 'evidence.sqlite3'
    SQLiteInformationStore(path)
    monkeypatch.setenv('TRADINGAGENTS_INFORMATION_STORE_PATH', str(path))
    monkeypatch.chdir(tmp_path.parent)
    assert runtime_store_path() == path
    assert build_default_config()['information_store_path'] == str(path)


def test_missing_relative_and_unconfigured_paths_never_create(tmp_path, monkeypatch):
    monkeypatch.delenv('TRADINGAGENTS_INFORMATION_STORE_PATH', raising=False)
    monkeypatch.chdir(tmp_path)
    for value in (None, Path('alternate.sqlite3'), tmp_path / 'missing.sqlite3'):
        with pytest.raises(ValueError):
            runtime_store_path(value)
    assert list(tmp_path.iterdir()) == []


def test_explicit_configuration_wins(tmp_path, monkeypatch):
    path = tmp_path / 'existing.sqlite3'
    SQLiteInformationStore(path)
    monkeypatch.setenv('TRADINGAGENTS_INFORMATION_STORE_PATH', str(tmp_path / 'wrong'))
    assert runtime_store_path(path) == path
