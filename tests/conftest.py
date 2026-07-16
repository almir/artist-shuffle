"""Shared test fixtures.

The script lives in a hyphenated file (``artist-shuffle.py``) that cannot be
imported with a normal ``import`` statement, so it is loaded from its path.
"""

from __future__ import annotations

import importlib.util
import random
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "artist-shuffle.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("artist_shuffle", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def artist_shuffle() -> ModuleType:
    """The loaded artist-shuffle module."""
    return _load_module()


@pytest.fixture(autouse=True)
def deterministic_random() -> None:
    """Seed the global RNG so tests that shuffle are reproducible."""
    random.seed(0)


@pytest.fixture
def make_library(tmp_path: Path):
    """Create a directory of empty song files from ``"Artist - Title"`` names."""

    def _make(names: list[str]) -> Path:
        library = tmp_path / "library"
        library.mkdir()
        for name in names:
            (library / name).touch()
        return library

    return _make
