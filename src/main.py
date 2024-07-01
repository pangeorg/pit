#!/usr/bin/python3

import argparse
from pit.commands import (
    cmd_cat_file,
    init,
    commit,
    cmd_hash_object,
    cmd_ls_tree,
    cmd_checkout,
    cmd_show_ref,
    cmd_tag,
    cmd_rev_parse,
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


def checkout_parser(subparsers) -> None:
    argsp = subparsers.add_parser(
        "checkout", help="Checkout a commit inside a directory")
    argsp.add_argument("commit",
                       help="The commit or tree to checkout.")

    argsp.add_argument("path",
                       help="The empty path to checkout on.")


def showref_parser(subparsers) = > None:
    argsp = subparsers.add_parser(
        "show-ref", help="Show all references")


def tag_parser(subparsers) = > None:
    argsp = argsubparsers.add_parser(
        "tag",
        help="List and create tags")

    argsp.add_argument("-a",
                       action="store_true",
                       dest="create_tag_object",
                       help="Whether to create a tag object")

    argsp.add_argument("name",
                       nargs="?",
                       help="The new tag's name")

    argsp.add_argument("object",
                       default="HEAD",
                       nargs="?",
                       help="The object the new tag will point to")


def rev_parse_parser(subparsers):
    argsp = subparsers.add_parser(
        "rev-parse",
        help="Parse revision (or other objects) identifiers")

    argsp.add_argument("--type",
                       metavar="type",
                       dest="type",
                       choices=["blob", "commit", "tag", "tree"],
                       default=None,
                       help="Specify the expected type")

    argsp.add_argument("name",
                       help="The name to parse")


def main():
    parser = argparse.ArgumentParser(description="Custom Git-like CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    init_parser(subparsers)
    cat_file_parser(subparsers)
    hash_object_parser(subparsers)
    ls_tree_parser(subparsers)
    checkout_parser(subparsers)
    rev_parse_parser(subparsers)

    args = parser.parse_args()

    match args.command:
        case "cat-file":
            return cmd_cat_file(args)
        case "checkout":
            return cmd_checkout(args)
        case "commit":
            return commit()
        case "show-ref":
            return cmd_show_ref(args)
        case "hash-object":
            return cmd_hash_object(args)
        case "init":
            return init(args.path)
        case "ls-tree":
            return cmd_ls_tree(args)
        case "rev-parse":
            return cmd_rev_parse(args)
        case "tag":
            return cmd_tag(args)
        case _:
            parser.print_help()
    return 0


if __name__ == "__main__":
    main()
