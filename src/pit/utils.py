import os
from pathlib import Path
from collections import OrderedDict
import binascii
from pit.repo import (
    Repository,
    repo_file,
    repo_dir,
)


def ref_resolve(repo: Repository, ref: str):
    path = repo_file(repo, ref)
    if not os.path.isfile(path):
        return None

    with open(path, 'r') as f:
        data = f.read()[:-1]
    if data.startswith("ref: "):
        return ref_resolve(repo, data[5:])
    return data


def ref_list(repo: Repository, path: str | Path | None = None):
    if not path:
        path = repo_dir(repo, "refs")
    ret = OrderedDict()
    # Git shows refs sorted.  To do the same, we use
    # an OrderedDict and sort the output of listdir
    for f in sorted(os.listdir(path)):
        can = os.path.join(path, f)
        if os.path.isdir(can):
            ret[f] = ref_list(repo, can)
        else:
            ret[f] = ref_resolve(repo, can)

    return ret


def sha_to_hex(sha):
    """Takes a string and returns the hex of the sha within."""
    hexsha = binascii.hexlify(sha)
    assert len(hexsha) == 40, "Incorrect length of sha1 string: %r" % hexsha
    return hexsha


def hex_to_sha(hex):
    """Takes a hex sha and returns a binary sha."""
    assert len(hex) == 40, "Incorrect length of hexsha: %s" % hex
    try:
        return binascii.unhexlify(hex)
    except TypeError as exc:
        if not isinstance(hex, bytes):
            raise
        raise ValueError(exc.args[0]) from exc
