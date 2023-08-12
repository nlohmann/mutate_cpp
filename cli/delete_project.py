#!/usr/bin/env python3
# coding=utf-8
# PYTHON_ARGCOMPLETE_OK

import sys
from argparse import ArgumentParser

# Allow this script to be used from the parent directory
sys.path.append(".")

from app import db
from app.models import Project


def main():
    # Parse arguments
    argument_parser = ArgumentParser(description="Delete a project.")
    argument_parser.add_argument(
        "--project", type=str, required=True,
        help="The name of the project to delete."
    )
    arguments = argument_parser.parse_args()

    # Find that project
    project_query = Project.query.filter(Project.name == arguments.project)
    if project_query.count() == 0:
        print(f"Project '{arguments.project}' does not exist", file=sys.stderr)
        exit(1)

    # Delete the project from the DB
    db.session.delete(project_query.first())
    db.session.commit()

    print(f"Project '{arguments.project}' deleted successfully.")
    exit(0)


if __name__ == "__main__":
    main()
