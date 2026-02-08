from setuptools import setup, find_packages

setup(
    name="pre_commit_circleci",
    version="0.1.0",
    packages=find_packages(),
    py_modules=[
        "circleci_validate",
        "circleci_process",
        "circleci_pack",
        "circleci_pack_validate",
    ],
    entry_points={
        "console_scripts": [
            "circleci-validate=circleci_validate:main",
            "circleci-process=circleci_process:main",
            "circleci-pack=circleci_pack:main",
            "circleci-pack-validate=circleci_pack_validate:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ],
    },
    python_requires=">=3.10",
)
