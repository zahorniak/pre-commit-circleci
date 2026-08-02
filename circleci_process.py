#!/usr/bin/env python3
"""
circleci_process.py
~~~~~~~~~~~~~~~~~~~

A *pre-commit* hook that runs `circleci config process` on one or more
CircleCI configuration files.

The hook supports the legacy CLI (0.1.x) and CLI v1. It translates
the org and verbose arguments for the detected generation.

Exit code:
  * 0  - all configs processed successfully
  * 1+ - at least one config failed
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from circleci_cli import CLI_INSTALL_URL, build_process_cmd


def run_process(
    config_path: Path,
    org: str | None,
    org_slug: str | None,
    org_id: str | None,
    pipeline_params: str | None,
    verbose: bool,
    extra: list[str],
) -> int:
    """Run `circleci config process` and return its exit code."""
    cmd = build_process_cmd(
        path=str(config_path),
        org=org,
        org_slug=org_slug,
        org_id=org_id,
        pipeline_parameters=pipeline_params,
        verbose=verbose,
        extra=extra,
    )
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if completed.returncode == 0:
        # Hide the CircleCI output on success.
        print(f"✅  CircleCI configuration passed processing: {config_path}")
    else:
        # Show the CircleCI output so the user can see the problem.
        sys.stderr.write(completed.stdout + completed.stderr)
    return completed.returncode


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    """Return the parsed known arguments and the unknown remainder."""
    parser = argparse.ArgumentParser(
        description=(
            "Run `circleci config process` against the given file(s) inside pre-commit."
        ),
    )
    parser.add_argument(
        "--org-slug",
        help="organization slug (e.g. github/example-org) for private orbs",
    )
    parser.add_argument(
        "--org-id",
        help="organization ID for private orbs",
    )
    parser.add_argument(
        "--org",
        help="organization slug or ID (CLI v1 style) for private orbs",
    )
    parser.add_argument(
        "--pipeline-parameters",
        help=(
            "YAML/JSON string or file path with pipeline parameters "
            '(e.g. \'{"foo": "bar"}\' or params.yml)'
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="verbose CLI output (--verbose on legacy, --debug on CLI v1)",
    )
    parser.add_argument(
        "filenames",
        nargs="+",
        help="config files to check",
    )
    return parser.parse_known_args()


def main() -> None:
    """Entry-point for the pre-commit hook."""
    args, extra = parse_args()

    # Skip the hook in the CircleCI environment.
    if os.getenv("CIRCLECI"):
        print("CircleCI environment detected, skipping processing.")
        sys.exit(0)

    # Stop when the CircleCI CLI is not installed.
    if not shutil.which("circleci"):
        print(f"CircleCI CLI not found. Install: {CLI_INSTALL_URL}")
        sys.exit(1)

    exit_code = 0
    for file_name in args.filenames:
        path = Path(file_name)
        if not path.exists():
            print(f"⚠️  Skipping missing file: {path}", file=sys.stderr)
            continue

        ret = run_process(
            config_path=path,
            org=args.org,
            org_slug=args.org_slug,
            org_id=args.org_id,
            pipeline_params=args.pipeline_parameters,
            verbose=args.verbose,
            extra=extra,
        )
        exit_code = max(exit_code, ret)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
