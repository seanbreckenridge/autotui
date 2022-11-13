import io
from pathlib import Path
from setuptools import setup, find_packages

requirements = Path("requirements.txt").read_text().splitlines()

# Use the README.md content for the long description:
with io.open("README.md", encoding="utf-8") as fo:
    long_description = fo.read()

pkg = "autotui"
setup(
    name=pkg,
    version="0.4.3",
    url="https://github.com/seanbreckenridge/autotui",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=(
        """quickly create UIs to interactively prompt, validate, and persist python objects to disk (JSON/YAML) and back using type hints"""
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(include=[pkg]),
    package_data={pkg: ["py.typed"]},
    test_suite="tests",
    install_requires=requirements,
    python_requires=">=3.8",
    extras_require={
        "testing": [
            "pytest",
            "mypy",
            "flake8",
        ],
        "optional": ["orjson", "pyfzf-iter"],
    },
    keywords="data prompt namedtuple",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
