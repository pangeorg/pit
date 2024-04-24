#!/usr/bin/python3

import argparse
from pit.commands import cat_file, init, commit


def main():
    parser = argparse.ArgumentParser(description="Custom Git-like CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Subparser for cat-file command
    cat_file_parser = subparsers.add_parser(
        "cat-file", help="Display contents of an object"
    )
    cat_file_parser.add_argument("object", help="Object to display")

    # Subparser for init command
    _ = subparsers.add_parser("init", help="Initialize a new repository")

    # Subparser for commit command
    commit_parser = subparsers.add_parser(
        "commit", help="Record changes to the repository"
    )
    commit_parser.add_argument("-m", "--message", help="Commit message")

    args = parser.parse_args()

    command = args.command
    match command:
        case "cat-file":
            return cat_file(args.object)
        case "init":
            return init()
        case "commit":
            return commit()
        case _:
            parser.print_help()
    return 0


if __name__ == "__main__":
    main()
