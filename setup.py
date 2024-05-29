from setuptools import setup, find_packages

setup(
    name="pre_commit_circleci",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["circleci_validate"],
    entry_points={
        "console_scripts": [
            "circleci-validate=circleci_validate:main",
        ],
    },
)
