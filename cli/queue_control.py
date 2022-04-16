#!/usr/bin/env python
# coding=utf-8
# PYTHON_ARGCOMPLETE_OK

import sys
from argparse import ArgumentParser
from urllib import request

# Allow this script to be used from the parent directory
sys.path.append(".")

from app.models import Patch


# TODO retrieve the actual server and port from the application

def main():
    # Parse argument
    argument_parser = ArgumentParser(description="Control the Mutate++ queue.")
    argument_parser.add_argument(
        "action", choices=['start', 'stop', 'status'],
        help="The queue action to be done."
    )
    arguments = argument_parser.parse_args()

    if arguments.action == 'start':
        request.urlopen("http://127.0.0.1:5000/queue/start")
    elif arguments.action == 'stop':
        request.urlopen("http://127.0.0.1:5000/queue/stop")
    elif arguments.action == 'status':
        incomplete_patches = Patch.query.filter(Patch.state == 'incomplete').count()
        all_patches = Patch.query.count()
        if all_patches == 0:
            print("No patches generated.")
            exit(0)
        finished_patches = all_patches - incomplete_patches
        percentage = 100 * ((all_patches - incomplete_patches) / all_patches)
        print(f"Patch {finished_patches} / {all_patches} ({percentage:.0f}%)")


if __name__ == "__main__":
    main()
