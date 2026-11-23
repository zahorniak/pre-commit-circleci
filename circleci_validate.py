#!/usr/bin/env python3
"""
circleci_validate.py
~~~~~~~~~~~~~~~~~~~~

A *pre-commit* hook that runs `circleci config validate`.

The hook supports the legacy CLI (0.1.x) and CLI v1. It translates
the path, org, and verbose arguments for the detected generation.

Exit code:
  * 0 - validation passed
  * 1 - validation failed, or the CLI is not installed
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from circleci_cli import CLI_INSTALL_URL, build_validate_cmd, cli_env


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    """Return the parsed known arguments and the unknown remainder."""
    parser = argparse.ArgumentParser(
        description="Run `circleci config validate` inside pre-commit.",
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="config file to validate (default: .circleci/config.yml)",
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
        "-v",
        "--verbose",
        action="store_true",
        help="verbose CLI output (--verbose on legacy, --debug on CLI v1)",
    )
    return parser.parse_known_args()


def main() -> None:
    """Entry-point for the pre-commit hook."""
    args, extra = parse_args()

    # Skip the hook in the CircleCI environment.
    if os.getenv("CIRCLECI"):
        print("CircleCI environment detected, skipping validation.")
        sys.exit(0)

    # Stop when the CircleCI CLI is not installed.
    if not shutil.which("circleci"):
        print(f"CircleCI CLI not found. Install: {CLI_INSTALL_URL}")
        sys.exit(1)

    cmd = build_validate_cmd(
        path=args.filename,
        org=args.org,
        org_slug=args.org_slug,
        org_id=args.org_id,
        verbose=args.verbose,
        extra=extra,
    )
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=False, env=cli_env()
    )
    if result.returncode == 0:
        print("CircleCI Configuration Passed Validation.")
    else:
        print("CircleCI Configuration Failed Validation.")
        sys.stderr.write(result.stdout + result.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
