#!/usr/bin/env python3
"""
circleci_pack.py
~~~~~~~~~~~~~~~~

A *pre-commit* hook that runs `circleci config pack` on a source directory
to pack modular CircleCI configuration files.

Exit code:
  * 0  - pack successful
  * 1  - pack failed
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from circleci_cli import CLI_INSTALL_URL


def parse_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Pack modular CircleCI config from src/ directory"
    )
    parser.add_argument(
        "--src-dir",
        required=True,
        help="Source directory to pack (e.g., .circleci/src)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to stdout)",
    )
    parser.add_argument(
        "--org-slug",
        help="deprecated, ignored: circleci config pack accepts no org flags",
    )
    parser.add_argument(
        "--org-id",
        help="deprecated, ignored: circleci config pack accepts no org flags",
    )
    return parser.parse_args()


def main() -> None:
    """Entry-point for the pre-commit hook."""
    args = parse_args()

    # Skip in CircleCI environment
    if os.getenv("CIRCLECI"):
        print("CircleCI environment detected, skipping.")
        sys.exit(0)

    # Check CLI availability
    if not shutil.which("circleci"):
        print(f"CircleCI CLI not found. Install: {CLI_INSTALL_URL}")
        sys.exit(1)

    # Verify src-dir exists
    if not os.path.isdir(args.src_dir):
        print(f"Source directory not found: {args.src_dir}")
        sys.exit(1)

    # `circleci config pack` accepts no org flags on any CLI
    # generation. Warn and ignore them.
    if args.org_slug or args.org_id:
        print(
            "Warning: `circleci config pack` accepts no org flags; "
            "--org-slug/--org-id ignored.",
            file=sys.stderr,
        )

    # Build command
    cmd: list[str] = ["circleci", "config", "pack", args.src_dir]

    # Run pack
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        print(f"Failed to pack configuration from {args.src_dir}")
        print(result.stderr)
        sys.exit(1)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(result.stdout)
        print(f"Packed configuration written to {args.output}")
    else:
        print(result.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
