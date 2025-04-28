from setuptools import setup, find_packages

setup(
    name="pre_commit_circleci",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["circleci_validate", "circleci_process"],
    entry_points={
        "console_scripts": [
            "circleci-validate=circleci_validate:main",
            "circleci-process=circleci_process:main",
        ],
    },
)
