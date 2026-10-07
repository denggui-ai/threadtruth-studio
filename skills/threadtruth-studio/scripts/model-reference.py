#!/usr/bin/env python3
"""Export or validate a private, portable model reference package."""
import sys

# Runtime helpers keep all generated files in the caller's private output.
sys.dont_write_bytecode = True
from model_reference import main

if __name__ == '__main__':
    main()
