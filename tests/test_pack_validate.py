"""Tests for circleci_pack_validate.py hook."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

import circleci_pack_validate


class TestValidateConfig:
    """Tests for the validate_config() function."""

    def test_runs_validate_command(
        self,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that circleci config validate is called correctly."""
        ret, stdout, stderr = circleci_pack_validate.validate_config(
            config_path=str(simple_config),
            org_slug=None,
            org_id=None,
        )

        assert ret == 0
        call_args = mock_subprocess_success.call_args[0][0]
        assert call_args[0:3] == ["circleci", "config", "validate"]
        assert str(simple_config) in call_args

    def test_includes_org_slug(
        self,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that org-slug is included in command."""
        circleci_pack_validate.validate_config(
            config_path=str(simple_config),
            org_slug="github/org",
            org_id=None,
        )

        call_args = mock_subprocess_success.call_args[0][0]
        assert "--org-slug=github/org" in call_args

    def test_includes_org_id(
        self,
        mock_subprocess_success: MagicMock,
        simple_config: Path,
    ) -> None:
        """Test that org-id is included in command."""
        circleci_pack_validate.validate_config(
            config_path=str(simple_config),
            org_slug=None,
            org_id="12345",
        )

        call_args = mock_subprocess_success.call_args[0][0]
        assert "--org-id=12345" in call_args


class TestPackConfig:
    """Tests for the pack_config() function."""

    def test_runs_pack_command(
        self,
        mock_subprocess_pack_success: MagicMock,
        dynamic_src_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Test that circleci config pack is called correctly."""
        output_path = tmp_path / "output.yml"
        ret, stdout, stderr = circleci_pack_validate.pack_config(
            src_dir=str(dynamic_src_dir),
            output_path=str(output_path),
        )

        assert ret == 0
        call_args = mock_subprocess_pack_success.call_args[0][0]
        assert call_args[0:3] == ["circleci", "config", "pack"]
        assert str(dynamic_src_dir) in call_args

    def test_writes_output_file(
        self,
        mock_subprocess_pack_success: MagicMock,
        dynamic_src_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Test that output is written to file."""
        output_path = tmp_path / "output.yml"
        circleci_pack_validate.pack_config(
            src_dir=str(dynamic_src_dir),
            output_path=str(output_path),
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "version: 2.1" in content


class TestParseArgs:
    """Tests for the parse_args() function."""

    def test_default_values(self) -> None:
        """Test default argument values."""
        with patch("sys.argv", ["circleci_pack_validate"]):
            args = circleci_pack_validate.parse_args()

        assert args.setup_config == ".circleci/config.yml"
        assert args.src_dir == ".circleci/src"
        assert args.skip_setup is False
        assert args.skip_continuation is False
        assert args.org_slug is None
        assert args.org_id is None

    def test_parses_all_options(self) -> None:
        """Test parsing all options."""
        with patch(
            "sys.argv",
            [
                "circleci_pack_validate",
                "--setup-config=setup.yml",
                "--src-dir=src",
                "--skip-setup",
                "--skip-continuation",
                "--org-slug=github/org",
                "--org-id=123",
            ],
        ):
            args = circleci_pack_validate.parse_args()

        assert args.setup_config == "setup.yml"
        assert args.src_dir == "src"
        assert args.skip_setup is True
        assert args.skip_continuation is True
        assert args.org_slug == "github/org"
        assert args.org_id == "123"


class TestMain:
    """Tests for the main() function."""

    def test_skips_in_circleci_environment(
        self, mock_circleci_env: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that validation is skipped when running in CircleCI."""
        with patch("sys.argv", ["circleci_pack_validate"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack_validate.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "CircleCI environment detected" in captured.out

    def test_fails_when_cli_not_installed(
        self, mock_circleci_not_installed: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that validation fails when CircleCI CLI is not installed."""
        with patch("sys.argv", ["circleci_pack_validate"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack_validate.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "CircleCI CLI not found" in captured.out

    def test_fails_when_setup_config_not_found(
        self,
        mock_circleci_installed: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that validation fails when setup config doesn't exist."""
        with patch(
            "sys.argv",
            ["circleci_pack_validate", "--setup-config=/nonexistent/config.yml"],
        ):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack_validate.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Setup config not found" in captured.out

    def test_validates_setup_config(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_success: MagicMock,
        dynamic_setup_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that setup config is validated."""
        with patch(
            "sys.argv",
            [
                "circleci_pack_validate",
                f"--setup-config={dynamic_setup_config}",
                "--skip-continuation",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack_validate.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Setup configuration passed validation" in captured.out

    def test_skips_setup_validation(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_success: MagicMock,
        dynamic_src_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that setup validation can be skipped."""
        with patch(
            "sys.argv",
            [
                "circleci_pack_validate",
                "--skip-setup",
                f"--src-dir={dynamic_src_dir}",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack_validate.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Validating setup config" not in captured.out

    def test_skips_continuation_when_src_dir_not_found(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_success: MagicMock,
        dynamic_setup_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that continuation validation is skipped when src dir doesn't exist."""
        with patch(
            "sys.argv",
            [
                "circleci_pack_validate",
                f"--setup-config={dynamic_setup_config}",
                "--src-dir=/nonexistent/src",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack_validate.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Source directory not found" in captured.out
        assert "Skipping continuation config validation" in captured.out

    def test_skips_continuation_validation(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_success: MagicMock,
        dynamic_setup_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that continuation validation can be skipped."""
        with patch(
            "sys.argv",
            [
                "circleci_pack_validate",
                f"--setup-config={dynamic_setup_config}",
                "--skip-continuation",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack_validate.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Packing continuation config" not in captured.out

    def test_validates_both_configs(
        self,
        mock_circleci_installed: MagicMock,
        dynamic_setup_config: Path,
        dynamic_src_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that both setup and continuation configs are validated."""
        with patch("subprocess.run") as mock_run:
            # First call: validate setup config
            # Second call: pack config
            # Third call: validate packed config
            success_result = MagicMock()
            success_result.returncode = 0
            success_result.stdout = "version: 2.1\njobs:\n  build:\n    docker:\n      - image: cimg/base:current"
            success_result.stderr = ""
            mock_run.return_value = success_result

            with patch(
                "sys.argv",
                [
                    "circleci_pack_validate",
                    f"--setup-config={dynamic_setup_config}",
                    f"--src-dir={dynamic_src_dir}",
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    circleci_pack_validate.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Setup configuration passed validation" in captured.out
        assert "Continuation configuration passed validation" in captured.out

    def test_reports_setup_validation_failure(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_failure: MagicMock,
        dynamic_setup_config: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that setup validation failure is reported."""
        with patch(
            "sys.argv",
            [
                "circleci_pack_validate",
                f"--setup-config={dynamic_setup_config}",
                "--skip-continuation",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack_validate.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Setup configuration failed validation" in captured.out

    def test_reports_pack_failure(
        self,
        mock_circleci_installed: MagicMock,
        dynamic_setup_config: Path,
        dynamic_src_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that pack failure is reported."""
        with patch("subprocess.run") as mock_run:
            # Setup validation succeeds
            success_result = MagicMock()
            success_result.returncode = 0
            success_result.stdout = ""
            success_result.stderr = ""

            # Pack fails
            failure_result = MagicMock()
            failure_result.returncode = 1
            failure_result.stdout = ""
            failure_result.stderr = "Pack error"

            mock_run.side_effect = [success_result, failure_result]

            with patch(
                "sys.argv",
                [
                    "circleci_pack_validate",
                    f"--setup-config={dynamic_setup_config}",
                    f"--src-dir={dynamic_src_dir}",
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    circleci_pack_validate.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Failed to pack configuration" in captured.out

    def test_reports_continuation_validation_failure(
        self,
        mock_circleci_installed: MagicMock,
        dynamic_setup_config: Path,
        dynamic_src_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that continuation validation failure is reported."""
        with patch("subprocess.run") as mock_run:
            # Setup validation succeeds
            setup_success = MagicMock()
            setup_success.returncode = 0
            setup_success.stdout = ""
            setup_success.stderr = ""

            # Pack succeeds
            pack_success = MagicMock()
            pack_success.returncode = 0
            pack_success.stdout = "version: 2.1"
            pack_success.stderr = ""

            # Continuation validation fails
            continuation_failure = MagicMock()
            continuation_failure.returncode = 1
            continuation_failure.stdout = ""
            continuation_failure.stderr = "Validation error"

            mock_run.side_effect = [setup_success, pack_success, continuation_failure]

            with patch(
                "sys.argv",
                [
                    "circleci_pack_validate",
                    f"--setup-config={dynamic_setup_config}",
                    f"--src-dir={dynamic_src_dir}",
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    circleci_pack_validate.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Continuation configuration failed validation" in captured.out

    def test_cleans_up_temp_file(
        self,
        mock_circleci_installed: MagicMock,
        dynamic_setup_config: Path,
        dynamic_src_dir: Path,
    ) -> None:
        """Test that temp file is cleaned up after validation."""
        created_temp_files: list[str] = []

        original_named_temp = circleci_pack_validate.tempfile.NamedTemporaryFile

        def track_temp_file(*args, **kwargs):
            """Track created temp files."""
            result = original_named_temp(*args, **kwargs)
            created_temp_files.append(result.name)
            return result

        with patch("subprocess.run") as mock_run:
            success_result = MagicMock()
            success_result.returncode = 0
            success_result.stdout = "version: 2.1"
            success_result.stderr = ""
            mock_run.return_value = success_result

            with patch.object(
                circleci_pack_validate.tempfile,
                "NamedTemporaryFile",
                track_temp_file,
            ):
                with patch(
                    "sys.argv",
                    [
                        "circleci_pack_validate",
                        f"--setup-config={dynamic_setup_config}",
                        f"--src-dir={dynamic_src_dir}",
                    ],
                ):
                    with pytest.raises(SystemExit):
                        circleci_pack_validate.main()

        # Verify temp file was created and then cleaned up
        assert len(created_temp_files) == 1
        assert not os.path.exists(created_temp_files[0])

    def test_cleans_up_temp_file_on_error(
        self,
        mock_circleci_installed: MagicMock,
        dynamic_setup_config: Path,
        dynamic_src_dir: Path,
    ) -> None:
        """Test that temp file is cleaned up even when validation fails."""
        created_temp_files: list[str] = []

        original_named_temp = circleci_pack_validate.tempfile.NamedTemporaryFile

        def track_temp_file(*args, **kwargs):
            """Track created temp files."""
            result = original_named_temp(*args, **kwargs)
            created_temp_files.append(result.name)
            return result

        with patch("subprocess.run") as mock_run:
            # Setup succeeds, pack succeeds, validation fails
            success_result = MagicMock()
            success_result.returncode = 0
            success_result.stdout = "version: 2.1"
            success_result.stderr = ""

            failure_result = MagicMock()
            failure_result.returncode = 1
            failure_result.stdout = ""
            failure_result.stderr = "Error"

            mock_run.side_effect = [success_result, success_result, failure_result]

            with patch.object(
                circleci_pack_validate.tempfile,
                "NamedTemporaryFile",
                track_temp_file,
            ):
                with patch(
                    "sys.argv",
                    [
                        "circleci_pack_validate",
                        f"--setup-config={dynamic_setup_config}",
                        f"--src-dir={dynamic_src_dir}",
                    ],
                ):
                    with pytest.raises(SystemExit):
                        circleci_pack_validate.main()

        # Verify temp file was created and then cleaned up
        assert len(created_temp_files) == 1
        assert not os.path.exists(created_temp_files[0])
