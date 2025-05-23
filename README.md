# Overview

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/zahorniak/pre-commit-circleci?label=latest%20release)](https://github.com/zahorniak/pre-commit-circleci/releases/)
[![GitHub Release Date - Published_At](https://img.shields.io/github/release-date/zahorniak/pre-commit-circleci)](https://github.com/zahorniak/pre-commit-circleci/releases/)

[![issues - pre-commit-circleci](https://img.shields.io/github/issues/zahorniak/pre-commit-circleci)](https://github.com/zahorniak/pre-commit-circleci/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/zahorniak/pre-commit-circleci)](https://github.com/zahorniak/pre-commit-circleci/pulls)

# Usage

## 1. Install dependencies

- [`pre-commit`](https://pre-commit.com/#install)
- [`circleci-cli`](https://circleci.com/docs/2.0/local-cli/#installation)

## 2. Create config file _.pre-commit-config.yaml_ with content:

- For CircleCI config validation :

```bash
$ cat .pre-commit-config.yaml
- repo: https://github.com/zahorniak/pre-commit-circleci.git
  rev: v1.1.0 # Ensure this is the latest tag, comparing to the Releases tab
  hooks:
    - id: circleci_validate
```

- For CircleCI config processing test :

```bash
$ cat .pre-commit-config.yaml
- repo: https://github.com/zahorniak/pre-commit-circleci.git
  rev: v1.1.0 # Ensure this is the latest tag, comparing to the Releases tab
  hooks:
    - id: circleci_process
```

If you wish to pass additional args to circleci_validate or circleci_process,
you can specify them in the config. See `circleci config validate --help` or
`circleci config process --help` for accepted args. You must use the form
`--arg=value`, not `--arg value`.

For example, to set an org-slug:

```bash
$ cat .pre-commit-config.yaml
- repo: https://github.com/zahorniak/pre-commit-circleci.git
  rev: v1.1.0 # Ensure this is the latest tag, comparing to the Releases tab
  hooks:
    - id: circleci_validate
      args:
        - --org-slug=my/organization
```

Or specify a custom config file:

```bash
$ cat .pre-commit-config.yaml
- repo: https://github.com/zahorniak/pre-commit-circleci.git
  rev: v1.1.0
  hooks:
    - id: circleci_validate
      args:
        - .circleci/continue_config.yml
```

The CircleCI process hook allow passing multiple configuration files.

For example :

```bash
$ cat .pre-commit-config.yaml
- repo: https://github.com/zahorniak/pre-commit-circleci.git
  rev: v1.1.0
  hooks:
    - id: circleci_process
      args:
        - '--pipeline-parameters={"foo": "bar"}'
        - .circleci/config-1.yml
        - .circleci/config-2.yml
```

## 3. Install hook

```bash
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

## 4. Commit code

```bash
$ git commit -m "add circleci hook"
Validate CircleCI config.................................................Passed
Process CircleCI configuration...........................................Passed
[branchname 1111111] add circleci hook
 1 file changed, 5 insertions(+), 1 deletion(-)
```

## How hook works

| Hook                | Description                                                                  |
| ------------------- | ---------------------------------------------------------------------------- |
| `circleci_validate` | Validates CircleCI configuration using command `circleci config validate`    |
| `circleci_process`  | Process the CircleCI configuration(s) using command`circleci config process` |

### Run hook manually

```bash
$ pre-commit run -a
Validate CircleCI config.................................................Passed
Process CircleCI configuration...........................................Passed
```
