#!/usr/bin/env python3
"""Update inventory after explicitly rebuilding or signing a bundled helper."""
from package_common import PLUGIN, refresh

if __name__ == '__main__':
    refresh(PLUGIN)
    print('Updated payload hashes and observed helper metadata')
