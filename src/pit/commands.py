import os
import sys
from pathlib import Path
import logging
from typing import List
from collections import OrderedDict
from pit.utils import (
    ref_list,
)
from pit.repo import (
    repo_create,
    repo_find,
    repo_file,
    Repository,
)
from pit.objects import (
    object_read,
    object_find,
    object_hash,
    object_write,
    PitTree,
    PitTag,
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
            item_type = item.mode[0:1]
        else:
            item_type = item.mode[0:2]

        match item_type:  # Determine the type.
            case b'04': item_type = "tree"
            case b'10': item_type = "blob"  # A regular file.
            # A symlink. Blob contents is link target.
            case b'12': item_type = "blob"
            case b'16': item_type = "commit"  # A submodule
            case _: raise Exception(f"Weird tree leaf mode {item.mode}")

        if not (recursive and item_type == 'tree'):  # This is a leaf
            print("{0} {1} {2}\t{3}".format(
                "0" * (6 - len(item.mode)) + item.mode.decode("ascii"),
                # Git's ls-tree displays the type
                # of the object pointed to.  We can do that too :)
                item_type,
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


def cmd_checkout(args):
    repo = repo_find()

    obj = object_read(repo, object_find(repo, args.commit))

    # If the object is a commit, we grab its tree
    if obj.fmt == b'commit':
        obj = object_read(repo, obj.kvlm[b'tree'].decode("ascii"))

    # Verify that path is an empty directory
    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception("Not a directory {0}!".format(args.path))
        if os.listdir(args.path):
            raise Exception("Not empty {0}!".format(args.path))
    else:
        os.makedirs(args.path)

    tree_checkout(repo, obj, os.path.realpath(args.path))


def tree_checkout(repo: Repository, tree: PitTree, path: str | Path):
    for item in tree.items:
        obj = object_read(repo, item.sha)
        dest = os.path.join(path, item.path)

        if obj.fmt == b'tree':
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif obj.fmt == b'blob':
            # TODO: Support symlinks (identified by mode 12****)
            with open(dest, 'wb') as f:
                f.write(obj.blobdata)


def cmd_show_ref(args):
    repo = repo_find()
    refs = ref_list(repo)
    show_ref(repo, refs, prefix="refs")


def show_ref(repo, refs, with_hash=True, prefix=""):
    for k, v in refs.items():
        if isinstance(v, str):
            print("{0}{1}{2}".format(
                v + " " if with_hash else "",
                prefix + "/" if prefix else "",
                k))
        else:
            show_ref(repo, v, with_hash=with_hash, prefix="{0}{1}{2}".format(
                prefix, "/" if prefix else "", k))


def cmd_tag(args):
    repo = repo_find()

    if args.name:
        tag_create(repo,
                   args.name,
                   args.object,
                   type="object" if args.create_tag_object else "ref")
    else:
        refs = ref_list(repo)
        show_ref(repo, refs["tags"], with_hash=False)


def tag_create(repo, name, ref, create_tag_object=False):
    # get the GitObject from the object reference
    sha = object_find(repo, ref)

    if create_tag_object:
        # create tag object (commit)
        tag = PitTag(repo)
        tag.kvlm = OrderedDict()
        tag.kvlm[b'object'] = sha.encode()
        tag.kvlm[b'type'] = b'commit'
        tag.kvlm[b'tag'] = name.encode()
        # Feel free to let the user give their name!
        # Notice you can fix this after commit, read on!
        tag.kvlm[b'tagger'] = b'Pitter <pit@example.com>'
        # …and a tag message!
        tag.kvlm[None] = b"A tag generated by pit, which won't let you customize the message!"
        tag_sha = object_write(tag)
        # create reference
        ref_create(repo, "tags/" + name, tag_sha)
    else:
        # create lightweight tag (ref)
        ref_create(repo, "tags/" + name, sha)


def ref_create(repo, ref_name, sha):
    with open(repo_file(repo, "refs/" + ref_name), 'w') as fp:
        fp.write(sha + "\n")


def cmd_rev_parse(args):
    if args.type:
        fmt = args.type.encode()
    else:
        fmt = None

    repo = repo_find()

    print(object_find(repo, args.name, fmt, follow=True))
