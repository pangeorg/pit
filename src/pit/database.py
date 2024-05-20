import os
from pathlib import Path
from pit.objects import Encodable
import tempfile
import zlib


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(os.path.abspath(path))

    def store(self, obj: Encodable):
        content = obj.db_encode()
        self.write_object(obj.oid, content)

    def write_object(self, oid: str, content: bytes):
        obj_path = Path(self.path) / Path(oid[:2]) / Path(oid[2:])
        dirname = Path(os.path.dirname(obj_path))
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with tempfile.NamedTemporaryFile(dir=dirname, delete=False) as tmp_file:
            compressed = zlib.compress(content)
            tmp_file.write(compressed)
            os.rename(tmp_file.name, obj_path)
