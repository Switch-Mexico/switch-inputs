import os
from setuptools import find_packages, setup, Command

with open("README.md", "r") as fh:
    long_description = fh.read()

here = os.path.abspath(os.path.dirname(__file__))

about = {}

with open(os.path.join(here, "switch_inputs", "__version__.py")) as f:
    exec (f.read(), about)

required = [
    'tqdm',
    'pandas',
    'requests',
    'click',
    'pyyaml',
]


setup(
    name="switch-inputs",
    version=about['__version__'],
    author="pesap",
    author_email="pesapsanchez@gmail.com",
    description="Create input files for switch",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/example-project",
    install_requires=required,
    packages=find_packages(include=['switch_inputs', 'switch_inputs.*'],
                           exclude=['tests']),
    entry_points={
        'console_scripts': ['inputs = switch_inputs:main']
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha"
    ),
)
