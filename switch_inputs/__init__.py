# This file is needed to impport the package
import os
import sys

# Append current folder to path
ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, ROOT)

from cli import main

def cli():
    return main(obj={})


if __name__ == '__main__':
    cli()
