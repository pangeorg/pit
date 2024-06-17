import sys
from pathlib import Path
import logging
from typing import List
from pit.repo import (
    repo_create,
    repo_find,
    Repository,
)
from pit.objects import (
    object_read,
    object_find,
    object_hash,
    PitTree
)

logger = logging.getLogger(__name__)


def cmd_ls_tree(args):
    repo = repo_find()
    ls_tree(repo, args.tree, args.recursive)


def ls_tree(repo: Repository, ref: str, recursive=None, prefix=""):
    import os
    sha = object_find(repo, ref, fmt=b"tree")
    obj: PitTree = object_read(repo, sha)
    for item in obj.items:
        if len(item.mode) == 5:
            type = item.mode[0:1]
        else:
            type = item.mode[0:2]

        match type:  # Determine the type.
            case b'04': type = "tree"
            case b'10': type = "blob"  # A regular file.
            # A symlink. Blob contents is link target.
            case b'12': type = "blob"
            case b'16': type = "commit"  # A submodule
            case _: raise Exception(f"Weird tree leaf mode {item.mode}")

        if not (recursive and type == 'tree'):  # This is a leaf
            print("{0} {1} {2}\t{3}".format(
                "0" * (6 - len(item.mode)) + item.mode.decode("ascii"),
                # Git's ls-tree displays the type
                # of the object pointed to.  We can do that too :)
                type,
                item.sha,
                os.path.join(prefix, item.path)))
        else:  # This is a branch, recurse
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))


def cmd_hash_object(args) -> int:
    if args.write:
        repo = repo_find()
    else:
        repo = None

    with open(args.path, "rb") as fd:
        sha = object_hash(fd, args.type.encode(), repo)
        sys.stdout.buffer.write(sha + "\n")
        sys.stdout.flush()
    return 0


def hash_object(args) -> int:
    return cmd_hash_object(args)


def cmd_cat_file(args) -> int:
    repo = repo_find()
    return cat_file(repo, args.object, fmt=args.type.encode())


def cat_file(repo, obj, fmt=None) -> int:
    obj = object_read(repo, object_find(repo, obj, fmt=fmt))
    sys.stdout.buffer.write(obj.serialize())
    return 0


def init(path: str | Path) -> int:
    repo_create(path)
    return 0


def add(cwd: str | Path | None = None, files: List[str] = []):
    raise NotImplementedError("Add not implemented")


def commit(cwd: str | Path | None = None):
    raise NotImplementedError("Commit not implemented")
