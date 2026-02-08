"""Tests for circleci_validate.py hook."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import circleci_validate


class TestMain:
    """Tests for the main() function."""

    def test_skips_in_circleci_environment(
        self, mock_circleci_env: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that validation is skipped when running in CircleCI."""
        with pytest.raises(SystemExit) as exc_info:
            circleci_validate.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Circleci environment detected" in captured.out

    def test_fails_when_cli_not_installed(
        self, mock_circleci_not_installed: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that validation fails when CircleCI CLI is not installed."""
        with pytest.raises(SystemExit) as exc_info:
            circleci_validate.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Circleci CLI could not be found" in captured.out

    def test_validates_config_successfully(
        self,
        mock_circleci_installed: MagicMock,
        simple_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful config validation."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Config is valid"
            mock_result.stderr = ""
            mock_result.check_returncode = MagicMock()  # Does nothing on success
            mock_run.return_value = mock_result

            with patch("sys.argv", ["circleci_validate", str(simple_config)]):
                # main() doesn't call sys.exit() on success, it just returns
                circleci_validate.main()

            captured = capsys.readouterr()
            assert "CircleCI Configuration Passed Validation" in captured.out

            # Verify circleci was called with correct args
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0:3] == ["circleci", "config", "validate"]
            assert str(simple_config) in call_args

    def test_validates_config_failure(
        self,
        mock_circleci_installed: MagicMock,
        invalid_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test failed config validation."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error: Invalid config"
            # check_returncode raises CalledProcessError for non-zero exit
            mock_result.check_returncode = MagicMock(
                side_effect=subprocess.CalledProcessError(
                    1, "circleci", stderr="Error: Invalid config"
                )
            )
            mock_run.return_value = mock_result

            with patch("sys.argv", ["circleci_validate", str(invalid_config)]):
                with pytest.raises(SystemExit) as exc_info:
                    circleci_validate.main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "CircleCI Configuration Failed Validation" in captured.out

    def test_passes_org_slug_argument(
        self,
        mock_circleci_installed: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that org-slug argument is passed to circleci CLI."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.check_returncode = MagicMock()
            mock_run.return_value = mock_result

            with patch(
                "sys.argv",
                ["circleci_validate", "--org-slug=github/my-org", str(simple_config)],
            ):
                circleci_validate.main()

            call_args = mock_run.call_args[0][0]
            assert "--org-slug=github/my-org" in call_args

    def test_default_config_path(
        self,
        mock_circleci_installed: MagicMock,
    ) -> None:
        """Test that default config path is used when no args provided."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.check_returncode = MagicMock()
            mock_run.return_value = mock_result

            with patch("sys.argv", ["circleci_validate"]):
                circleci_validate.main()

            call_args = mock_run.call_args[0][0]
            # Only validate, config, validate - no config file specified
            assert call_args == ["circleci", "config", "validate"]
