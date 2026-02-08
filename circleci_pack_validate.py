#!/usr/bin/env python3
"""
circleci_pack_validate.py
~~~~~~~~~~~~~~~~~~~~~~~~~

A *pre-commit* hook that packs and validates CircleCI dynamic configuration.
Handles projects using continuation orb with modular src/ directory.

Exit code:
  * 0  - all validations passed
  * 1  - at least one validation failed
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def validate_config(
    config_path: str,
    org_slug: str | None,
    org_id: str | None,
) -> tuple[int, str, str]:
    """Run circleci config validate and return exit code, stdout, stderr."""
    cmd: list[str] = ["circleci", "config", "validate", config_path]
    if org_slug:
        cmd.append(f"--org-slug={org_slug}")
    if org_id:
        cmd.append(f"--org-id={org_id}")

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def pack_config(src_dir: str, output_path: str) -> tuple[int, str, str]:
    """Run circleci config pack and return exit code, stdout, stderr."""
    cmd: list[str] = ["circleci", "config", "pack", src_dir]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        with open(output_path, "w") as f:
            f.write(result.stdout)

    return result.returncode, result.stdout, result.stderr


def parse_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Pack and validate CircleCI dynamic configuration"
    )
    parser.add_argument(
        "--setup-config",
        default=".circleci/config.yml",
        help="Setup config file (default: .circleci/config.yml)",
    )
    parser.add_argument(
        "--src-dir",
        default=".circleci/src",
        help="Source directory to pack (default: .circleci/src)",
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip setup config validation",
    )
    parser.add_argument(
        "--skip-continuation",
        action="store_true",
        help="Skip continuation config validation",
    )
    parser.add_argument(
        "--org-slug",
        help="Organization slug for private orbs (e.g., github/example-org)",
    )
    parser.add_argument(
        "--org-id",
        help="Organization ID for private orbs",
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
        print(
            "CircleCI CLI not found. Install: "
            "https://circleci.com/docs/2.0/local-cli/#installation"
        )
        sys.exit(1)

    exit_code = 0

    # Validate setup config
    if not args.skip_setup:
        if not os.path.isfile(args.setup_config):
            print(f"Setup config not found: {args.setup_config}")
            sys.exit(1)

        print(f"Validating setup config: {args.setup_config}")
        ret, stdout, stderr = validate_config(
            args.setup_config, args.org_slug, args.org_id
        )
        if ret == 0:
            print("  Setup configuration passed validation.")
        else:
            print("  Setup configuration failed validation.")
            print(stderr)
            exit_code = 1

    # Pack and validate continuation config
    if not args.skip_continuation:
        if not os.path.isdir(args.src_dir):
            print(f"Source directory not found: {args.src_dir}")
            print("  Skipping continuation config validation.")
        else:
            print(f"Packing continuation config from: {args.src_dir}")

            # Use temp file for packed config
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yml", delete=False
            ) as tmp:
                tmp_path = tmp.name

            try:
                ret, stdout, stderr = pack_config(args.src_dir, tmp_path)
                if ret != 0:
                    print("  Failed to pack configuration.")
                    print(stderr)
                    exit_code = 1
                else:
                    print("  Packed successfully.")
                    print("Validating continuation config...")
                    ret, stdout, stderr = validate_config(
                        tmp_path, args.org_slug, args.org_id
                    )
                    if ret == 0:
                        print("  Continuation configuration passed validation.")
                    else:
                        print("  Continuation configuration failed validation.")
                        print(stderr)
                        exit_code = 1
            finally:
                # Always clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
