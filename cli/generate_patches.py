#!/usr/bin/env python
# coding=utf-8
# PYTHON_ARGCOMPLETE_OK

import sys
from argparse import ArgumentParser

# Allow this script to be used from the parent directory
sys.path.append(".")

from app.models import Project, File
from app.utils.SourceFile import SourceFile


def main():
    # Parse arguments
    argument_parser = ArgumentParser(description="Generate patches.")
    argument_parser.add_argument(
        "--project", type=str, required=True,
        help="The name of the project. If not provided, all projects will be processed."
    )
    # TODO allow selection of first/last line + which patches to generate
    arguments = argument_parser.parse_args()

    # Verify that the project exists
    project_query = Project.query.filter(Project.name == arguments.project)
    if project_query.count() == 0:
        print(f"Project '{arguments.project}' doesn't exist.", file=sys.stderr)
        exit(1)

    # Retrieve all files
    files = File.query.filter(File.project_id == project_query.first().id).all()

    if len(files) == 0:
        print("No files found to process.")
        exit(2)

    for file in files:
        print(f"Generating patches for '{file.filename}'...")
        source_file = SourceFile(file, 1, -1)
        source_file.generate_patches()

    print("Done")
    exit(0)


if __name__ == "__main__":
    main()
