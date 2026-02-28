#!/usr/bin/env python
"""Django management script for OsdagBridge web backend.

Requires the 'web-backend' extra: pip install -e ".[web-backend]"
"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "osdagbridge_web.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        print(
            "Django is not installed.\n"
            "Install with: pip install -e '.[web-backend]'"
        )
        sys.exit(1)
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

