import io
from setuptools import setup, find_packages

requirements = ["simplejson>=3.17", "prompt_toolkit>=3.0"]

# Use the README.md content for the long description:
with io.open("README.md", encoding="utf-8") as fo:
    long_description = fo.read()

pkg = "autotui"
setup(
    name=pkg,
    version="0.1.5",
    url="https://github.com/seanbreckenridge/autotui",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=("""helpers for creating TUIs with persistent typed data"""),
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
        ],
        "optional": ["dateparser"],
    },
    keywords="data prompt namedtuple",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
