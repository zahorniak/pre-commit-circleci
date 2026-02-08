"""Tests for circleci_pack.py hook."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import circleci_pack


class TestParseArgs:
    """Tests for the parse_args() function."""

    def test_requires_src_dir(self) -> None:
        """Test that --src-dir is required."""
        with patch("sys.argv", ["circleci_pack"]):
            with pytest.raises(SystemExit):
                circleci_pack.parse_args()

    def test_parses_src_dir(self) -> None:
        """Test parsing --src-dir argument."""
        with patch("sys.argv", ["circleci_pack", "--src-dir=.circleci/src"]):
            args = circleci_pack.parse_args()

        assert args.src_dir == ".circleci/src"
        assert args.output is None
        assert args.org_slug is None
        assert args.org_id is None

    def test_parses_all_options(self) -> None:
        """Test parsing all options."""
        with patch(
            "sys.argv",
            [
                "circleci_pack",
                "--src-dir=.circleci/src",
                "--output=config.yml",
                "--org-slug=github/org",
                "--org-id=123",
            ],
        ):
            args = circleci_pack.parse_args()

        assert args.src_dir == ".circleci/src"
        assert args.output == "config.yml"
        assert args.org_slug == "github/org"
        assert args.org_id == "123"


class TestMain:
    """Tests for the main() function."""

    def test_skips_in_circleci_environment(
        self, mock_circleci_env: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that packing is skipped when running in CircleCI."""
        with patch("sys.argv", ["circleci_pack", "--src-dir=.circleci/src"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "CircleCI environment detected" in captured.out

    def test_fails_when_cli_not_installed(
        self, mock_circleci_not_installed: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that packing fails when CircleCI CLI is not installed."""
        with patch("sys.argv", ["circleci_pack", "--src-dir=.circleci/src"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "CircleCI CLI not found" in captured.out

    def test_fails_when_src_dir_not_found(
        self,
        mock_circleci_installed: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that packing fails when src directory doesn't exist."""
        with patch("sys.argv", ["circleci_pack", "--src-dir=/nonexistent/path"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Source directory not found" in captured.out

    def test_packs_config_successfully(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_pack_success: MagicMock,
        dynamic_src_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful config packing."""
        with patch("sys.argv", ["circleci_pack", f"--src-dir={dynamic_src_dir}"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack.main()

        assert exc_info.value.code == 0

        # Verify circleci pack was called with correct args
        call_args = mock_subprocess_pack_success.call_args[0][0]
        assert call_args[0:3] == ["circleci", "config", "pack"]
        assert str(dynamic_src_dir) in call_args

        # Output should be printed to stdout
        captured = capsys.readouterr()
        assert "version: 2.1" in captured.out

    def test_writes_output_to_file(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_pack_success: MagicMock,
        dynamic_src_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that output is written to file when --output is specified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            output_path = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "circleci_pack",
                    f"--src-dir={dynamic_src_dir}",
                    f"--output={output_path}",
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    circleci_pack.main()

            assert exc_info.value.code == 0

            # Check output file was written
            with open(output_path) as f:
                content = f.read()
            assert "version: 2.1" in content

            captured = capsys.readouterr()
            assert f"Packed configuration written to {output_path}" in captured.out
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_includes_org_slug(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_pack_success: MagicMock,
        dynamic_src_dir: Path,
    ) -> None:
        """Test that org-slug is included in command."""
        with patch(
            "sys.argv",
            ["circleci_pack", f"--src-dir={dynamic_src_dir}", "--org-slug=github/org"],
        ):
            with pytest.raises(SystemExit):
                circleci_pack.main()

        call_args = mock_subprocess_pack_success.call_args[0][0]
        assert "--org-slug=github/org" in call_args

    def test_includes_org_id(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_pack_success: MagicMock,
        dynamic_src_dir: Path,
    ) -> None:
        """Test that org-id is included in command."""
        with patch(
            "sys.argv",
            ["circleci_pack", f"--src-dir={dynamic_src_dir}", "--org-id=12345"],
        ):
            with pytest.raises(SystemExit):
                circleci_pack.main()

        call_args = mock_subprocess_pack_success.call_args[0][0]
        assert "--org-id=12345" in call_args

    def test_fails_on_pack_error(
        self,
        mock_circleci_installed: MagicMock,
        mock_subprocess_failure: MagicMock,
        dynamic_src_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that packing fails on circleci error."""
        with patch("sys.argv", ["circleci_pack", f"--src-dir={dynamic_src_dir}"]):
            with pytest.raises(SystemExit) as exc_info:
                circleci_pack.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Failed to pack configuration" in captured.out
