#!/usr/bin/env python
"""
CLI Wrapper for DataCamp Downloader
Run with: python cli.py [command] [options]
"""

import sys
from datacamp_downloader.downloader import app

if __name__ == "__main__":
    app()
