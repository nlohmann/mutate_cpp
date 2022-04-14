#!/usr/bin/env python
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
    argument_parser = ArgumentParser(description="Create a new project.")
    argument_parser.add_argument(
        "--name", type=str, required=True,
        help="The name of the project."
    )
    argument_parser.add_argument(
        "--workdir", type=str, required=True,
        help="The working directory in which all commands will be executed."
    )
    argument_parser.add_argument(
        "--build-command", type=str, required=True,
        help="The build command to use."
    )
    argument_parser.add_argument(
        "--quickcheck-command", type=str, required=False, default='',
        help="The quickcheck command to use."
    )
    argument_parser.add_argument(
        "--quickcheck-timeout", type=int, required=False,
        help="The timeout of the quickcheck command."
    )
    argument_parser.add_argument(
        "--test-command", type=str, required=True,
        help="The test command to use."
    )
    argument_parser.add_argument(
        "--test-timeout", type=int, required=False,
        help="The timeout of the test command."
    )
    argument_parser.add_argument(
        "--clean-command", type=str, required=False, default='',
        help="The clean command to use."
    )
    arguments = argument_parser.parse_args()

    # Verify that a project with the same name doesn't exist yet
    if Project.query.filter(Project.name == arguments.name).count() > 0:
        print(f"Project '{arguments.name}' already exists", file=sys.stderr)
        exit(1)

    # Add the project to the DB
    project = Project(
        name=arguments.name,
        workdir=arguments.workdir,
        build_command=arguments.build_command,
        quickcheck_command=arguments.quickcheck_command,
        quickcheck_timeout=arguments.quickcheck_timeout,
        test_command=arguments.test_command,
        test_timeout=arguments.test_timeout,
        clean_command=arguments.clean_command
    )
    db.session.add(project)
    db.session.commit()

    print(f"Project '{project.name}' created successfully.")
    exit(0)


if __name__ == "__main__":
    main()
