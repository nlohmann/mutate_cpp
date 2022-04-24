#!/usr/bin/env python
# coding=utf-8
# PYTHON_ARGCOMPLETE_OK

import sys
from argparse import ArgumentParser
from pathlib import Path

# Allow this script to be used from the parent directory
sys.path.append(".")

from app import db
from app.models import Project, File


def main():
    # Parse arguments
    argument_parser = ArgumentParser(description="Add files to a project.")
    argument_parser.add_argument(
        "--project", type=str, required=True,
        help="The name of the project."
    )
    argument_parser.add_argument(
        'files', type=str, metavar="FILE", nargs='+',
        help="A file to be added to the project."
    )
    arguments = argument_parser.parse_args()

    # Verify that the project exists
    project_query = Project.query.filter(Project.name == arguments.project)
    if project_query.count() != 1:
        print(f"Project '{arguments.project}' doesn't exist.", file=sys.stderr)
        exit(1)

    # Retrieve project id
    project_id = project_query.first().id

    for arg_filename in arguments.files:
        file_path: Path = Path(arg_filename)
        filename = file_path.absolute().as_posix()

        # Verify that the file exists
        if not file_path.exists():
            print(f"File '{file_path}' doesn't exist.", file=sys.stderr)
            exit(2)

        # Verify that the file isn't already added to the project
        file_contents = file_path.read_text()

        # Add the file to the db
        file = File(
            filename=filename,
            content=file_contents,
            project_id=project_id
        )

        if File.query.filter(File.project_id == project_id).filter(File.filename == filename).count() > 0:
            print(f"Skipping file '{file_path.name}' since it is already added to project '{arguments.project}'.")
            continue

        db.session.add(file)
        db.session.commit()

        print(f"File '{file_path.name}' added successfully.")
    exit(0)


if __name__ == "__main__":
    main()
