"""
Minimal setup.py so `pip install -e .` works for system-wide install.
Python 3.11+ required.
"""
from setuptools import setup, find_packages

setup(
    name="porcupine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "porcupine=porcupine:app",
        ],
    },
    python_requires=">=3.11",
)
