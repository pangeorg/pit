from enum import Enum
from hashlib import sha1
from typing import Protocol, List
import binascii


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


class PitNode:
    def __init__(self, data: bytes):
        self._data = data
        self._oid = ""
        self._serialized = False


class Encodable(Protocol):
    oid: str = ""
    name: str = ""
    object_type: ObjectType

    def db_encode(self) -> bytes:
        return b""


class Blob(Encodable):
    def __init__(self, data: bytes, name: str) -> None:
        self.data = data
        self.name = name
        self.object_type = ObjectType.BLOB
        self.oid: str = ""

    def db_encode(self) -> bytes:
        bytesize = len(self.data) + 1
        content = bytes_concat(f"{self.object_type} ", bytesize, "\0", self.data, "\n")
        m = sha1()
        m.update(content)
        self.oid = m.hexdigest()
        return content


def bytes_concat(*args, encoding="ascii") -> bytes:
    b = bytes("", encoding=encoding)
    for a in args:
        if isinstance(a, bytes):
            b += a
        else:
            b += bytes(str(a), encoding=encoding)
    return b


class Tree(Encodable):
    mode: int = 100644

    def __init__(self, name: str) -> None:
        self.oid = ""
        self.name = name
        self._objects: List[Encodable] = []
        self.object_type = ObjectType.TREE

    def add_object(self, obj) -> None:
        self._objects.append(obj)
        pass

    def db_encode(self) -> bytes:
        entries = []
        for obj in self._objects:
            _ = obj.db_encode()
            v = (
                ("%04o" % self.mode).encode("ascii")
                + b" "
                + bytes(obj.name, encoding="ascii")
                + b"\0"
                + hex_to_sha(obj.oid)
            )
            entries.append(v)
        entries = b"".join(entries)
        m = sha1()
        m.update(entries)
        self.oid = m.hexdigest()
        return entries

    def print(self):
        entries = self.db_encode()
        print(self.oid)
        for name, mode, sha in parse_tree(entries):
            print(name, mode, sha)


def parse_tree(text, strict=False):
    """Parse a tree text.

    Args:
      text: Serialized text to parse
    Returns: iterator of tuples of (name, mode, sha)

    Raises:
      ObjectFormatException: if the object was malformed in some way
    """
    count = 0
    length = len(text)
    while count < length:
        mode_end = text.index(b" ", count)
        mode_text = text[count:mode_end]
        if strict and mode_text.startswith(b"0"):
            raise Exception("Invalid mode '%s'" % mode_text)
        try:
            mode = int(mode_text, 8)
        except ValueError as exc:
            raise Exception("Invalid mode '%s'" % mode_text) from exc
        name_end = text.index(b"\0", mode_end)
        name = text[mode_end + 1 : name_end]
        count = name_end + 21
        sha = text[name_end + 1 : count]
        if len(sha) != 20:
            raise Exception("Sha has invalid length")
        hexsha = sha_to_hex(sha)
        yield (name, mode, hexsha)
