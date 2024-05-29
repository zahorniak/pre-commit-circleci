#!/usr/bin/env python3

import os
import subprocess
import sys
import shutil


def main():
    # Check if running in CircleCI environment
    if os.getenv("CIRCLECI"):
        print("Circleci environment detected, skipping validation.")
        sys.exit(0)

    # Check if CircleCI CLI is installed
    if not shutil.which("circleci"):
        print(
            "Circleci CLI could not be found. Install the latest CLI version https://circleci.com/docs/2.0/local-cli/#installation"
        )
        sys.exit(1)

    # Validate CircleCI config
    try:
        result = subprocess.run(
            ["circleci", "config", "validate"], capture_output=True, text=True
        )
        result.check_returncode()
        print("CircleCI Configuration Passed Validation.")
    except subprocess.CalledProcessError as e:
        print("CircleCI Configuration Failed Validation.")
        print(e.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
