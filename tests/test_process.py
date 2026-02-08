"""Tests for circleci_process.py hook."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import circleci_process


class TestRunProcess:
    """Tests for the run_process() function."""

    def test_runs_process_command(
        self,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that circleci config process is called correctly."""
        result = circleci_process.run_process(
            config_path=simple_config,
            org_slug=None,
            org_id=None,
            pipeline_params=None,
            verbose=False,
        )

        assert result == 0
        call_args = mock_subprocess_success.call_args[0][0]
        assert call_args[0:3] == ["circleci", "config", "process"]
        assert str(simple_config) in call_args

    def test_includes_org_slug(
        self,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that org-slug is included in command."""
        circleci_process.run_process(
            config_path=simple_config,
            org_slug="github/my-org",
            org_id=None,
            pipeline_params=None,
            verbose=False,
        )

        call_args = mock_subprocess_success.call_args[0][0]
        assert "--org-slug=github/my-org" in call_args

    def test_includes_org_id(
        self,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that org-id is included in command."""
        circleci_process.run_process(
            config_path=simple_config,
            org_slug=None,
            org_id="12345",
            pipeline_params=None,
            verbose=False,
        )

        call_args = mock_subprocess_success.call_args[0][0]
        assert "--org-id=12345" in call_args

    def test_includes_pipeline_parameters(
        self,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that pipeline-parameters is included in command."""
        circleci_process.run_process(
            config_path=simple_config,
            org_slug=None,
            org_id=None,
            pipeline_params='{"foo": "bar"}',
            verbose=False,
        )

        call_args = mock_subprocess_success.call_args[0][0]
        assert '--pipeline-parameters={"foo": "bar"}' in call_args

    def test_includes_verbose_flag(
        self,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that verbose flag is included in command."""
        circleci_process.run_process(
            config_path=simple_config,
            org_slug=None,
            org_id=None,
            pipeline_params=None,
            verbose=True,
        )

        call_args = mock_subprocess_success.call_args[0][0]
        assert "--verbose" in call_args

    def test_returns_exit_code_on_failure(
        self,
        mock_subprocess_failure: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that exit code is returned on failure."""
        result = circleci_process.run_process(
            config_path=simple_config,
            org_slug=None,
            org_id=None,
            pipeline_params=None,
            verbose=False,
        )

        assert result == 1


class TestParseArgs:
    """Tests for the parse_args() function."""

    def test_parses_single_file(self) -> None:
        """Test parsing a single config file."""
        with patch("sys.argv", ["circleci_process", "config.yml"]):
            args = circleci_process.parse_args()

        assert args.filenames == ["config.yml"]
        assert args.org_slug is None
        assert args.org_id is None
        assert args.pipeline_parameters is None
        assert args.verbose is False

    def test_parses_multiple_files(self) -> None:
        """Test parsing multiple config files."""
        with patch("sys.argv", ["circleci_process", "config1.yml", "config2.yml"]):
            args = circleci_process.parse_args()

        assert args.filenames == ["config1.yml", "config2.yml"]

    def test_parses_all_options(self) -> None:
        """Test parsing all options."""
        with patch(
            "sys.argv",
            [
                "circleci_process",
                "--org-slug=github/org",
                "--org-id=123",
                '--pipeline-parameters={"key": "value"}',
                "--verbose",
                "config.yml",
            ],
        ):
            args = circleci_process.parse_args()

        assert args.org_slug == "github/org"
        assert args.org_id == "123"
        assert args.pipeline_parameters == '{"key": "value"}'
        assert args.verbose is True
        assert args.filenames == ["config.yml"]


class TestMain:
    """Tests for the main() function."""

    def test_skips_in_circleci_environment(
        self, mock_circleci_env: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that processing is skipped when running in CircleCI."""
        with patch("sys.argv", ["circleci_process", "config.yml"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_process.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "CircleCI environment detected" in captured.out

    def test_fails_when_cli_not_installed(
        self, mock_circleci_not_installed: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that processing fails when CircleCI CLI is not installed."""
        with patch("sys.argv", ["circleci_process", "config.yml"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_process.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "CircleCI CLI not found" in captured.out

    def test_processes_single_file_successfully(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful processing of a single config file."""
        with patch("sys.argv", ["circleci_process", str(simple_config)]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_process.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "passed processing" in captured.out

    def test_processes_multiple_files(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test processing multiple config files."""
        with patch(
            "sys.argv", ["circleci_process", str(simple_config), str(simple_config)]
        ):
            with pytest.raises(SystemExit) as exc_info:
                circleci_process.main()

        assert exc_info.value.code == 0
        # Should be called twice
        assert mock_subprocess_success.call_count == 2

    def test_skips_missing_files(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_success: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that missing files are skipped with warning."""
        with patch("sys.argv", ["circleci_process", "nonexistent.yml"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_process.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Skipping missing file" in captured.err

    def test_returns_max_exit_code(
        self,
        mock_circleci_installed: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that maximum exit code is returned."""
        # First call succeeds, second fails
        with patch("subprocess.run") as mock_run:
            success_result = MagicMock()
            success_result.returncode = 0
            success_result.stdout = ""
            success_result.stderr = ""

            failure_result = MagicMock()
            failure_result.returncode = 1
            failure_result.stdout = ""
            failure_result.stderr = "Error"

            mock_run.side_effect = [success_result, failure_result]

            with patch(
                "sys.argv",
                ["circleci_process", str(simple_config), str(simple_config)],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    circleci_process.main()

        assert exc_info.value.code == 1
