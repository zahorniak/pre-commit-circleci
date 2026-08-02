#!/usr/bin/env python3
"""
circleci_cli.py
~~~~~~~~~~~~~~~

Shared helpers for the hooks in this repository.

The helpers detect the CircleCI CLI generation. They build commands
that are correct for the detected generation.

Supported generations:
  * Legacy CLI (0.1.x)
  * CLI v1 (major version 1)
"""

from __future__ import annotations

import os
import re
import subprocess

# The CLI download page. All hooks show this URL in their messages.
CLI_INSTALL_URL = "https://cli.circleci.com/"

# Cache for the detection result. None means "not detected yet".
_IS_V1: bool | None = None

# The first "<major>.<minor>" number in the version output.
_VERSION_RE = re.compile(r"(\d+)\.\d+")


def is_cli_v1() -> bool:
    """Return True when the installed CLI is v1 or later.

    The function caches the result for the process lifetime.
    A failed command or unknown output counts as the legacy CLI.
    """
    global _IS_V1
    if _IS_V1 is None:
        _IS_V1 = _detect_cli_v1()
    return _IS_V1


def _detect_cli_v1() -> bool:
    """Run `circleci version` and parse the major version."""
    env = dict(os.environ)
    # Skip the slow update check of the legacy CLI. CLI v1 ignores
    # this variable.
    env["CIRCLECI_CLI_SKIP_UPDATE_CHECK"] = "true"
    try:
        result = subprocess.run(
            ["circleci", "version"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
    except OSError:
        return False
    match = _VERSION_RE.search(result.stdout)
    if not match:
        return False
    return int(match.group(1)) >= 1


def _org_args(org: str | None, org_slug: str | None, org_id: str | None) -> list[str]:
    """Return the org flags for the detected CLI generation.

    Precedence: --org first, then --org-slug, then --org-id.
    """
    value = org or org_slug or org_id
    if not value:
        return []
    if is_cli_v1():
        return [f"--org={value}"]
    if org:
        # Translate the v1-style value for the legacy CLI. A slug
        # contains a slash. A UUID does not.
        if "/" in org:
            return [f"--org-slug={org}"]
        return [f"--org-id={org}"]
    if org_slug:
        return [f"--org-slug={org_slug}"]
    return [f"--org-id={org_id}"]


def _verbose_args(verbose: bool) -> list[str]:
    """Return the verbose flag for the detected CLI generation."""
    if not verbose:
        return []
    if is_cli_v1():
        return ["--debug"]
    return ["--verbose"]


def build_validate_cmd(
    path: str | None,
    org: str | None = None,
    org_slug: str | None = None,
    org_id: str | None = None,
    verbose: bool = False,
    extra: list[str] | None = None,
) -> list[str]:
    """Build the `circleci config validate` command.

    CLI v1 reads the path from the --config flag. The legacy CLI
    reads the path as a positional argument.
    """
    cmd = ["circleci", "config", "validate"]
    if path:
        if is_cli_v1():
            cmd += ["--config", path]
        else:
            cmd.append(path)
    cmd += _org_args(org, org_slug, org_id)
    cmd += _verbose_args(verbose)
    if extra:
        cmd += extra
    return cmd


def build_process_cmd(
    path: str,
    org: str | None = None,
    org_slug: str | None = None,
    org_id: str | None = None,
    pipeline_parameters: str | None = None,
    verbose: bool = False,
    extra: list[str] | None = None,
) -> list[str]:
    """Build the `circleci config process` command.

    The two CLI generations read the path as a positional argument.
    """
    cmd = ["circleci", "config", "process", path]
    cmd += _org_args(org, org_slug, org_id)
    if pipeline_parameters:
        cmd.append(f"--pipeline-parameters={pipeline_parameters}")
    cmd += _verbose_args(verbose)
    if extra:
        cmd += extra
    return cmd
