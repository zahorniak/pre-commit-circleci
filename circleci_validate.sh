#!/usr/bin/env bash
set -e

if [[ -n $CIRCLECI ]]; then
    echo "Circleci environment detected, skipping validation."
    exit 0
fi

if ! command -v circleci &> /dev/null
then
    echo "Circleci CLI could not be found. Install the latest CLI version https://circleci.com/docs/2.0/local-cli/#installation"
    exit 1
fi

if ! eMSG=$(circleci config validate $@ -c .circleci/config.yml); then
	echo "CircleCI Configuration Failed Validation."
	echo $eMSG
	exit 1
fi
