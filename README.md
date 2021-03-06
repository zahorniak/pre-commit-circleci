# Usage
## 1. Install dependencies
* [`pre-commit`](https://pre-commit.com/#install)
* [`circleci-cli`](https://circleci.com/docs/2.0/local-cli/#installation)

## 2. Create config file ***.pre-commit-config.yaml*** with content:
```bash
$ cat .pre-commit-config.yaml
- repo: https://github.com/zahorniak/pre-commit-circleci.git
  rev: v0.1 # get latest tag from release tab
  hooks:
    - id: circleci_validate
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
[branchname 1111111] add circleci hook
 1 file changed, 5 insertions(+), 1 deletion(-)
 ```

## How hook works
|   Hook    |   Description    |
|  ---  |  ---  |
|   `circleci_validate`    |   Validates CircleCI configuration using command `circleci config validate`    |



### Run hook manually
```bash
$ pre-commit run -a
Validate CircleCI config.................................................Passed
```
