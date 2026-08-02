"""Tests for the circleci_cli.py shared helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import circleci_cli

LEGACY_VERSION_OUTPUT = "0.1.34038+3fea946 (release)\n"
V1_VERSION_OUTPUT = "circleci 1.0.46087-pre (0560a043ef86)\n"


def _version_result(output: str, returncode: int = 0) -> MagicMock:
    """Return a mock subprocess result with the given output."""
    result = MagicMock()
    result.returncode = returncode
    result.stdout = output
    result.stderr = ""
    return result


class TestIsCliV1:
    """Tests for CLI generation detection."""

    def test_legacy_output_detects_legacy(self) -> None:
        with patch(
            "subprocess.run", return_value=_version_result(LEGACY_VERSION_OUTPUT)
        ):
            assert circleci_cli.is_cli_v1() is False

    def test_v1_output_detects_v1(self) -> None:
        with patch("subprocess.run", return_value=_version_result(V1_VERSION_OUTPUT)):
            assert circleci_cli.is_cli_v1() is True

    def test_unknown_output_falls_back_to_legacy(self) -> None:
        with patch("subprocess.run", return_value=_version_result("no numbers here")):
            assert circleci_cli.is_cli_v1() is False

    def test_command_failure_falls_back_to_legacy(self) -> None:
        with patch("subprocess.run", side_effect=OSError("no such file")):
            assert circleci_cli.is_cli_v1() is False

    def test_result_is_cached(self) -> None:
        with patch(
            "subprocess.run", return_value=_version_result(V1_VERSION_OUTPUT)
        ) as mock_run:
            assert circleci_cli.is_cli_v1() is True
            assert circleci_cli.is_cli_v1() is True
        assert mock_run.call_count == 1

    def test_detection_skips_update_check(self) -> None:
        with patch(
            "subprocess.run", return_value=_version_result(LEGACY_VERSION_OUTPUT)
        ) as mock_run:
            circleci_cli.is_cli_v1()
        env = mock_run.call_args.kwargs["env"]
        assert env["CIRCLECI_CLI_SKIP_UPDATE_CHECK"] == "true"


class TestBuildValidateCmd:
    """Tests for the validate command builder."""

    def test_legacy_positional_path(self, mock_cli_legacy: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml")
        assert cmd == ["circleci", "config", "validate", "cfg.yml"]

    def test_v1_config_flag(self, mock_cli_v1: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml")
        assert cmd == ["circleci", "config", "validate", "--config", "cfg.yml"]

    def test_no_path(self, mock_cli_v1: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd(None)
        assert cmd == ["circleci", "config", "validate"]

    def test_legacy_org_slug(self, mock_cli_legacy: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml", org_slug="github/my-org")
        assert cmd == [
            "circleci",
            "config",
            "validate",
            "cfg.yml",
            "--org-slug=github/my-org",
        ]

    def test_v1_org_from_slug(self, mock_cli_v1: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml", org_slug="github/my-org")
        assert cmd == [
            "circleci",
            "config",
            "validate",
            "--config",
            "cfg.yml",
            "--org=github/my-org",
        ]

    def test_v1_org_from_id(self, mock_cli_v1: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml", org_id="1234-abcd")
        assert cmd[-1] == "--org=1234-abcd"

    def test_legacy_org_from_slash_value(self, mock_cli_legacy: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml", org="github/my-org")
        assert cmd[-1] == "--org-slug=github/my-org"

    def test_legacy_org_from_uuid_value(self, mock_cli_legacy: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml", org="1234-abcd")
        assert cmd[-1] == "--org-id=1234-abcd"

    def test_org_precedence(self, mock_cli_v1: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd(
            "cfg.yml", org="a/b", org_slug="c/d", org_id="e"
        )
        assert cmd[-1] == "--org=a/b"

    def test_verbose_legacy(self, mock_cli_legacy: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml", verbose=True)
        assert cmd[-1] == "--verbose"

    def test_verbose_v1_maps_to_debug(self, mock_cli_v1: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd("cfg.yml", verbose=True)
        assert cmd[-1] == "--debug"

    def test_extra_args_pass_through(self, mock_cli_legacy: MagicMock) -> None:
        cmd = circleci_cli.build_validate_cmd(
            "cfg.yml", extra=["--ignore-deprecated-images"]
        )
        assert cmd[-1] == "--ignore-deprecated-images"


class TestBuildProcessCmd:
    """Tests for the process command builder."""

    def test_legacy_full_command(self, mock_cli_legacy: MagicMock) -> None:
        cmd = circleci_cli.build_process_cmd(
            "cfg.yml",
            org_slug="github/my-org",
            pipeline_parameters='{"foo": "bar"}',
            verbose=True,
        )
        assert cmd == [
            "circleci",
            "config",
            "process",
            "cfg.yml",
            "--org-slug=github/my-org",
            '--pipeline-parameters={"foo": "bar"}',
            "--verbose",
        ]

    def test_v1_full_command(self, mock_cli_v1: MagicMock) -> None:
        cmd = circleci_cli.build_process_cmd(
            "cfg.yml",
            org_slug="github/my-org",
            pipeline_parameters='{"foo": "bar"}',
            verbose=True,
        )
        assert cmd == [
            "circleci",
            "config",
            "process",
            "cfg.yml",
            "--org=github/my-org",
            '--pipeline-parameters={"foo": "bar"}',
            "--debug",
        ]
