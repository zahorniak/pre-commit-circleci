"""Tests for circleci_validate.py hook."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import circleci_validate


def _success_result() -> MagicMock:
    """Return a mock subprocess result for a passing validation."""
    result = MagicMock()
    result.returncode = 0
    result.stdout = "Config is valid"
    result.stderr = ""
    return result


def _failure_result() -> MagicMock:
    """Return a mock subprocess result for a failing validation."""
    result = MagicMock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "Error: Invalid config"
    return result


class TestMain:
    """Tests for the main() function."""

    def test_skips_in_circleci_environment(
        self, mock_circleci_env: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("sys.argv", ["circleci_validate"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_validate.main()

        assert exc_info.value.code == 0
        assert "CircleCI environment detected" in capsys.readouterr().out

    def test_fails_when_cli_not_installed(
        self, mock_circleci_not_installed: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("sys.argv", ["circleci_validate"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_validate.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "CircleCI CLI not found" in captured.out
        assert "https://cli.circleci.com/" in captured.out

    def test_legacy_validates_config_successfully(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_legacy: MagicMock,
        simple_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch("sys.argv", ["circleci_validate", str(simple_config)]):
                circleci_validate.main()

        assert "CircleCI Configuration Passed Validation" in capsys.readouterr().out
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == [
            "circleci",
            "config",
            "validate",
            str(simple_config),
        ]

    def test_legacy_validation_failure(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_legacy: MagicMock,
        invalid_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with patch("subprocess.run", return_value=_failure_result()):
            with patch("sys.argv", ["circleci_validate", str(invalid_config)]):
                with pytest.raises(SystemExit) as exc_info:
                    circleci_validate.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "CircleCI Configuration Failed Validation" in captured.out
        assert "Error: Invalid config" in captured.err

    def test_v1_uses_config_flag(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_v1: MagicMock,
        simple_config: Path,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch("sys.argv", ["circleci_validate", str(simple_config)]):
                circleci_validate.main()

        assert mock_run.call_args[0][0] == [
            "circleci",
            "config",
            "validate",
            "--config",
            str(simple_config),
        ]

    def test_legacy_passes_org_slug_unchanged(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_legacy: MagicMock,
        simple_config: Path,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch(
                "sys.argv",
                ["circleci_validate", "--org-slug=github/my-org", str(simple_config)],
            ):
                circleci_validate.main()

        assert "--org-slug=github/my-org" in mock_run.call_args[0][0]

    def test_v1_translates_org_slug(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_v1: MagicMock,
        simple_config: Path,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch(
                "sys.argv",
                ["circleci_validate", "--org-slug=github/my-org", str(simple_config)],
            ):
                circleci_validate.main()

        cmd = mock_run.call_args[0][0]
        assert "--org=github/my-org" in cmd
        assert "--org-slug=github/my-org" not in cmd

    def test_legacy_translates_org_flag_with_slash(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_legacy: MagicMock,
        simple_config: Path,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch(
                "sys.argv",
                ["circleci_validate", "--org=github/my-org", str(simple_config)],
            ):
                circleci_validate.main()

        assert "--org-slug=github/my-org" in mock_run.call_args[0][0]

    def test_legacy_translates_org_flag_uuid(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_legacy: MagicMock,
        simple_config: Path,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch(
                "sys.argv",
                ["circleci_validate", "--org=1234-abcd", str(simple_config)],
            ):
                circleci_validate.main()

        assert "--org-id=1234-abcd" in mock_run.call_args[0][0]

    def test_verbose_stays_on_legacy(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_legacy: MagicMock,
        simple_config: Path,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch(
                "sys.argv", ["circleci_validate", "--verbose", str(simple_config)]
            ):
                circleci_validate.main()

        assert "--verbose" in mock_run.call_args[0][0]

    def test_verbose_maps_to_debug_on_v1(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_v1: MagicMock,
        simple_config: Path,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch("sys.argv", ["circleci_validate", "-v", str(simple_config)]):
                circleci_validate.main()

        cmd = mock_run.call_args[0][0]
        assert "--debug" in cmd
        assert "--verbose" not in cmd

    def test_unknown_flags_pass_through(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_legacy: MagicMock,
        simple_config: Path,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch(
                "sys.argv",
                [
                    "circleci_validate",
                    "--ignore-deprecated-images",
                    str(simple_config),
                ],
            ):
                circleci_validate.main()

        assert "--ignore-deprecated-images" in mock_run.call_args[0][0]

    def test_default_config_path(
        self,
        mock_circleci_installed: MagicMock,
        mock_cli_legacy: MagicMock,
    ) -> None:
        with patch("subprocess.run", return_value=_success_result()) as mock_run:
            with patch("sys.argv", ["circleci_validate"]):
                circleci_validate.main()

        assert mock_run.call_args[0][0] == ["circleci", "config", "validate"]
