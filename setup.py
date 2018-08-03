"""Setup file for install and test.

Taken from:
https://pythonhosted.org/an_example_pypi_project/setuptools.html
for pytest:
https://pytest.org/latest/goodpractises.html
for tox:
https://testrun.org/tox/latest/example/basic.html#
integration-with-setuptools-distribute-test-commands
"""

import os
from setuptools import setup
from setuptools import find_packages


def read(fname):
    """Open a local file and return as string.

    Used for populating descriptions and arguments from file.
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def main():
    """Run the setup."""
    setup(
        name="itunessync",
        version="0.0.1",
        author="Matthew Hussey",
        author_email="matthew.hussey@googlemail.com",
        description=("Synchronise itunes music and playlists to another drive."),
        license='MIT',
        keywords="python",
        url="none.non",
        entry_points={
            'console_scripts': [
                'itunessync = itunessync.__main__:main'
            ]},
        packages=find_packages(where='src'),
        package_data={
            'itunessync': [
                'logging.conf'
            ]},
        package_dir={'': 'src'},
        install_requires=[],
        long_description=read("README"),
        classifiers=[
            "Development Status :: 1 - Planning",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Programming Language :: Python :: 2.7"],
        setup_requires=['pytest-runner'],
        tests_require=['mock', 'pytest-cov', 'robber', 'pytest']
    )

if __name__ == "__main__":
    main()
