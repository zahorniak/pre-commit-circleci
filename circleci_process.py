#!/usr/bin/env python3
"""
circleci_process.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A *pre-commit* hook that runs `circleci config process` on one or more
CircleCI configuration files.

Exit code:
  * 0  - all configs processed successfully
  * 1+ - at least one config failed
"""

from __future__ import annotations

import os
import argparse
import subprocess
import sys
from pathlib import Path


def run_process(
    config_path: Path,
    org_slug: str | None,
    org_id: str | None,
    pipeline_params: str | None,
    verbose: bool,
) -> int:
    """Run `circleci config process` and return its exit code."""
    cmd: list[str] = ["circleci", "config", "process", str(config_path)]

    if org_slug:
        cmd.append(f"--org-slug={org_slug}")
    if org_id:
        cmd.append(f"--org-id={org_id}")
    if pipeline_params:
        cmd.append(f"--pipeline-parameters={pipeline_params}")
    if verbose:
        cmd.append("--verbose")

    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if completed.returncode == 0:
        # Hide verbose CircleCI output on success
        print(f"✅  CircleCI configuration passed processing: {config_path}")
    else:
        # Re-emit CircleCI output so the user can see the problem
        sys.stderr.write(completed.stdout + completed.stderr)
    return completed.returncode


def parse_args() -> argparse.Namespace:  # noqa: D401
    """Return parsed CLI arguments."""
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
        "--pipeline-parameters",
        help=(
            "YAML/JSON string or file path with pipeline parameters "
            '(e.g. \'{"foo": "bar"}\' or params.yml)'
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="pass --verbose through to the CircleCI CLI "
        "(for failing operations in that implementation)",
    )
    parser.add_argument(
        "filenames",
        nargs="+",
        help="config files to check",
    )
    return parser.parse_args()


def main() -> None:
    """Entry-point for the pre-commit hook."""
    args = parse_args()

    # Check if running in CircleCI environment
    if os.getenv("CIRCLECI"):
        print("Circleci environment detected, skipping validation.")
        sys.exit(0)

    exit_code = 0
    for file_name in args.filenames:
        path = Path(file_name)
        if not path.exists():
            print(f"⚠️  Skipping missing file: {path}", file=sys.stderr)
            continue

        ret = run_process(
            config_path=path,
            org_slug=args.org_slug,
            org_id=args.org_id,
            pipeline_params=args.pipeline_parameters,
            verbose=args.verbose,
        )
        exit_code = max(exit_code, ret)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
