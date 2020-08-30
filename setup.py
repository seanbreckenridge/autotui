import io
from setuptools import setup, find_packages

requirements = ["logzero", "simplejson"]

# Use the README.md content for the long description:
with io.open('README.md', encoding='utf-8') as fo:
    long_description = fo.read()

setup(
    name='AutoTUI',
    version="0.1.0",
    url='https://github.com/seanbreckenridge/autotui',
    author='Sean Breckenridge',
    author_email='seanbrecke@gmail.com',
    description=('''helpers for creating TUIs with persistent data'''),
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    packages=find_packages(include=['autotui']),
    test_suite='tests',
    install_requires=requirements,
    keywords='data prompt namedtuple',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8'
    ],
)
