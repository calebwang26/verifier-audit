"""Lets the tests import the top-level modules (run_suite, mutate, ...)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
