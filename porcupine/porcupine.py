"""
Root entry point so users can run:  python porcupine.py <command>
or after pip install:               porcupine <command>
"""
from cli.main import app

if __name__ == "__main__":
    app()
