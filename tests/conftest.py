"""Shared pytest fixtures for pre-commit-circleci tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_config(fixtures_dir: Path) -> Path:
    """Return path to simple valid config."""
    return fixtures_dir / "simple" / "config.yml"


@pytest.fixture
def invalid_config(fixtures_dir: Path) -> Path:
    """Return path to invalid config."""
    return fixtures_dir / "invalid" / "config.yml"


@pytest.fixture
def dynamic_config_dir(fixtures_dir: Path) -> Path:
    """Return path to dynamic config directory."""
    return fixtures_dir / "dynamic"


@pytest.fixture
def dynamic_setup_config(dynamic_config_dir: Path) -> Path:
    """Return path to dynamic setup config."""
    return dynamic_config_dir / "config.yml"


@pytest.fixture
def dynamic_src_dir(dynamic_config_dir: Path) -> Path:
    """Return path to dynamic src directory."""
    return dynamic_config_dir / "src"


@pytest.fixture
def mock_circleci_installed() -> Generator[MagicMock, None, None]:
    """Mock shutil.which to return circleci as installed."""
    with patch("shutil.which") as mock_which:
        mock_which.return_value = "/usr/local/bin/circleci"
        yield mock_which


@pytest.fixture
def mock_circleci_not_installed() -> Generator[MagicMock, None, None]:
    """Mock shutil.which to return circleci as not installed."""
    with patch("shutil.which") as mock_which:
        mock_which.return_value = None
        yield mock_which


@pytest.fixture
def mock_circleci_env() -> Generator[None, None, None]:
    """Set CIRCLECI environment variable."""
    os.environ["CIRCLECI"] = "true"
    yield
    del os.environ["CIRCLECI"]


@pytest.fixture
def mock_subprocess_success() -> Generator[MagicMock, None, None]:
    """Mock subprocess.run to return success."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Config is valid"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_subprocess_failure() -> Generator[MagicMock, None, None]:
    """Mock subprocess.run to return failure."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Invalid config"
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_subprocess_pack_success() -> Generator[MagicMock, None, None]:
    """Mock subprocess.run to return packed YAML."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """version: 2.1
jobs:
  build:
    docker:
      - image: cimg/base:current
    steps:
      - checkout
workflows:
  main:
    jobs:
      - build
"""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run
