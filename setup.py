import io
from setuptools import setup, find_packages

requirements = ["logzero>=1.5", "simplejson>=3.17", "prompt_toolkit>=3.0"]

# Use the README.md content for the long description:
with io.open("README.md", encoding="utf-8") as fo:
    long_description = fo.read()

setup(
    name="autotui",
    version="0.0.1",
    url="https://github.com/seanbreckenridge/autotui",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=("""helpers for creating TUIs with persistent data"""),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(include=["autotui"]),
    test_suite="tests",
    install_requires=requirements,
    python_requires=">=3.8",
    extras_require={
        "testing": [
            "pytest",
            "mypy",
        ],
        "optional": ["dateparser"],
    },
    keywords="data prompt namedtuple",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
)
