import zlib
from enum import Enum
from typing import Protocol
import binascii
from collections import OrderedDict
from pathlib import Path
from pit.repo import repo_file, Repository


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


class ObjectType(Enum):
    BLOB = "blob"
    COMMIT = "commit"
    TREE = "tree"

    def __str__(self) -> str:
        return self.name.lower()


class PitObject(Protocol):
    def __init__(self, data=None):
        if data is not None:
            self.deserialize(data)
        else:
            self.init()

    def init(self) -> None:
        pass

    def serialize(self) -> bytes:
        raise NotImplementedError("serialize is not implemented!")

    def deserialize(self) -> None:
        raise NotImplementedError("deserialize is not implemented!")


class PitCommit(PitObject):
    fmt = b'commit'

    def deserialize(self, data):
        self.kvlm = kvlm_parse(data)

    def serialize(self):
        return kvlm_serialize(self.kvlm)

    def init(self):
        self.kvlm = dict()


class PitTreeLeaf:
    def __init__(self, mode: str, path: str | Path, sha: str):
        self.mode = mode
        self.path = Path(path)
        self.sha = sha


def tree_parse_one(raw: bytes, start=0) -> PitTreeLeaf:
    # Find the space terminator of the mode
    x = raw.find(b' ', start)
    assert x-start == 5 or x-start == 6

    # Read the mode
    mode = raw[start:x]
    if len(mode) == 5:
        # Normalize to six bytes.
        mode = b" " + mode

    # Find the NULL terminator of the path
    y = raw.find(b'\x00', x)
    # and read the path
    path = raw[x+1:y]

    # Read the SHA and convert to a hex string
    sha = format(int.from_bytes(raw[y+1:y+21], "big"), "040x")
    return y+21, PitTreeLeaf(mode, path.decode("utf8"), sha)


class PitTree(PitObject):
    fmt = b'tree'

    def deserialize(self, data):
        self.items = tree_parse(data)

    def serialize(self):
        return tree_serialize(self)

    def init(self):
        self.items = []


def tree_parse(raw: bytes):
    pos = 0
    max = len(raw)
    ret = []
    while pos < max:
        pos, data = tree_parse_one(raw, pos)
        ret.append(data)

    return ret


def tree_leaf_sort_key(leaf: PitTreeLeaf) -> str:
    if leaf.mode.startswith(b"10"):
        # file
        return str(leaf.path)
    else:
        # folder
        return str(leaf.path + "/")


def tree_serialize(obj: PitTree):
    obj.items.sort(key=tree_leaf_sort_key)
    ret = b''
    for i in obj.items:
        ret += i.mode
        ret += b' '
        ret += i.path.encode("utf8")
        ret += b'\x00'
        sha = int(i.sha, 16)
        ret += sha.to_bytes(20, byteorder="big")
    return ret


class PitTag(PitObject):
    pass


class PitBlob(PitObject):
    fmt = b'blob'

    def serialize(self):
        return self.data

    def deserialize(self, data):
        self.data = data


def object_read(repo: Repository, sha: str):
    path = repo_file(repo, "objects", sha[0:2], sha[2:])
    if not path.exists():
        return None

    with open(path, "rb") as f:
        data = zlib.decompress(f.read())

        # get obj tye
        x = data.find(b' ')
        fmt = data[:x]

        # validate obj size byu finding null terminator
        y = data.find(b'\x00', x)
        size: int = int(data[x:y].decode("ascii"))
        if size != len(data)-y-1:
            raise Exception("Malformed object {0}: bad length".format(sha))

        # Pick constructor
        match fmt:
            case b'commit': c = PitCommit
            case b'tree': c = PitTree
            case b'tag': c = PitTag
            case b'blob': c = PitBlob
            case _:
                raise Exception("Unknown type {0} for object {1}".format(
                    fmt.decode("ascii"), sha))

        # Call constructor and return object
        return c(data[y+1:])


def object_write(obj: PitObject, repo=None) -> str:
    import os
    import hashlib
    from tempfile import NamedTemporaryFile

    # Serialize object data
    data = obj.serialize()
    # Add header
    result = obj.fmt + b' ' + str(len(data)).encode() + b'\x00' + data
    # Compute hash
    sha = hashlib.sha1(result).hexdigest()

    if repo:
        # Compute path
        path = repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        if not path.exists():
            with NamedTemporaryFile(dir=path.parent, delete=False) as tmpFile:
                tmpFile.write(zlib.compress(result))
                os.rename(tmpFile.name, path)

    return sha


def object_find(
        repo: Repository,
        name: str, fmt: bytes | None = None,
        follow=True):
    return name


def object_hash(fd, fmt, repo=None):
    """ Hash object, writing it to repo if provided."""
    data = fd.read()

    # Choose constructor according to fmt argument
    match fmt:
        case b'commit': obj = PitCommit(data)
        case b'tree': obj = PitTree(data)
        case b'tag': obj = PitTag(data)
        case b'blob': obj = PitBlob(data)
        case _: raise Exception("Unknown type %s!" % fmt)

    return object_write(obj, repo)


def kvlm_parse(raw: bytes, start: int = 0, dct: OrderedDict = None):
    """Key-Value List with Message"""
    if not dct:
        dct = OrderedDict()
        # You CANNOT declare the argument as dct=OrderedDict() or all
        # call to the functions will endlessly grow the same dict.

    # This function is recursive: it reads a key/value pair, then call
    # itself back with the new position.  So we first need to know
    # where we are: at a keyword, or already in the messageQ

    # We search for the next space and the next newline.
    space_index = raw.find(b' ', start)
    newline_index = raw.find(b'\n', start)

    # If space appears before newline, we have a keyword.  Otherwise,
    # it's the final message, which we just read to the end of the file.

    # Base case
    # =========
    # If newline appears first (or there's no space at all, in which
    # case find returns -1), we assume a blank line.  A blank line
    # means the remainder of the data is the message.  We store it in
    # the dictionary, with None as the key, and return.
    if (space_index < 0) or (newline_index < space_index):
        assert newline_index == start
        dct[None] = raw[start+1:]
        return dct

    # Recursive case
    # ==============
    # we read a key-value pair and recurse for the next.
    key = raw[start:space_index]

    # Find the end of the value.  Continuation lines begin with a
    # space, so we loop until we find a "\n" not followed by a space.
    end = start
    while True:
        end = raw.find(b'\n', end+1)
        if raw[end+1] != ord(' '):
            break

    # Grab the value
    # Also, drop the leading space on continuation lines
    value = raw[space_index+1:end].replace(b'\n ', b'\n')

    # Don't overwrite existing data contents
    if key in dct:
        if isinstance(dct[key], list):
            dct[key].append(value)
        else:
            dct[key] = [dct[key], value]
    else:
        dct[key] = value

    return kvlm_parse(raw, start=end+1, dct=dct)


def kvlm_serialize(kvlm: OrderedDict) -> bytes:
    ret = b''

    # Output fields
    for k in kvlm.keys():
        # Skip the message itself
        if k is None:
            continue
        val = kvlm[k]
        # Normalize to a list
        if not isinstance(val, list):
            val = [val]

        for v in val:
            ret += k + b' ' + (v.replace(b'\n', b'\n ')) + b'\n'

    # Append message
    ret += b'\n' + kvlm[None] + b'\n'

    return ret
