from pathlib import Path

import pytest

from tradingagents.default_config import build_default_config
from tradingagents.information.runtime_store import runtime_store_path
from tradingagents.information.store import SQLiteInformationStore


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
