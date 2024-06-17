#!/usr/bin/python3

import argparse
from pit.commands import (
    cat_file,
    init,
    commit,
    hash_object,
)


def init_parser(subparsers) -> None:
    """Subparser for init command"""
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new repository")

    init_parser.add_argument(
        "path",
        metavar="directory",
        nargs="?",
        default=".",
        help="Path to .pit folder to create")


def cat_file_parser(subparsers) -> None:
    """Subparser for cat-file command """
    cat_file_parser = subparsers.add_parser(
        "cat-file",
        help="Display contents of an object"
    )

    cat_file_parser.add_argument(
        "type",
        metavar="type",
        choices=["blob", "commit", "tag", "tree"],
        help="type to display")

    cat_file_parser.add_argument(
        "object",
        metavar="object",
        help="Object to display")


def hash_object_parser(subparsers) -> None:
    argsp = subparsers.add_parser(
        "hash-object",
        help="Compute object ID and optionally creates a blob from a file",
    )

    argsp.add_argument(
        "-t",
        metavar="type",
        dest="type",
        choices=["blob", "commit", "tag", "tree"],
        default="blob",
        help="Specify the type")

    argsp.add_argument(
        "-w",
        dest="write",
        action="store_true",
        help="Actually write the object into the database")

    argsp.add_argument(
        "path",
        help="Read object from <file>"
    )


def ls_tree_parser(subparsers) -> None:
    argsp = subparsers.add_parser(
        "ls-tree", help="Pretty-print a tree object.")
    argsp.add_argument("-r",
                       dest="recursive",
                       action="store_true",
                       help="Recurse into sub-trees")

    argsp.add_argument("tree",
                       help="A tree-ish object.")


def main():
    parser = argparse.ArgumentParser(description="Custom Git-like CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    init_parser(subparsers)
    cat_file_parser(subparsers)
    hash_object_parser(subparsers)

    args = parser.parse_args()

    command = args.command
    match command:
        case "cat-file":
            return cat_file(args)
        case "hash-object":
            return hash_object(args)
        case "init":
            return init(args.path)
        case "commit":
            return commit()
        case _:
            parser.print_help()
    return 0


if __name__ == "__main__":
    main()
