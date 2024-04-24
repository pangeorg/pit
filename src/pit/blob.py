from enum import Enum
from hashlib import sha1


class ObjectType(Enum):
    BLOB = "blob"
    COMMIT = "commit"

    def __str__(self) -> str:
        return self.name.lower()


class Blob:
    def __init__(self, data: bytes, object_type: ObjectType = ObjectType.BLOB) -> None:
        self.data = data
        self.object_type = object_type
        self.oid: str = ""

    def db_encode(self):
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
