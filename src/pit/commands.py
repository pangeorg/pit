import os
from glob import glob
from pathlib import Path
from pit.workspace import Workspace
from pit.database import Database
from pit.objects import Blob, Tree
import logging
from typing import List

logger = logging.getLogger(__name__)

# NOTE
# refactor all commands to receive the workspace


def build_tree(path):
    t = Tree(name=Path(path).name)
    for p in glob(str(path) + "/*"):
        if os.path.isdir(p):
            t.add_object(build_tree(p))
        else:
            with open(p, "rb") as f:
                blob = Blob(data=f.read(), name=Path(p).name)
            t.add_object(blob)
    return t


def cat_file(id_: str, cwd: str | Path | None = None):
    if not cwd:
        cwd = Path(os.getcwd())
    if len(id_) < 6:
        logger.error("Need at least 5 characters")
        return 1
    folder = Path(cwd) / Path(".git") / Path("objects") / Path(id_[:2])
    if not os.path.exists(folder):
        logger.error(f"Cannot find object with id {id_}")
        return 1

    import zlib
    import sys
    from glob import glob

    files = glob(str(folder / Path(id_[2:])) + "*")
    if not files:
        logger.error(f"Cannot find object with id {id_}")
        return 1

    with open(files[0], "rb") as fb:
        data = zlib.decompress(fb.read())
        sys.stdout.buffer.write(data.split(b"\x00")[-1])
    return 0


def init(cwd: str | Path | None = None):
    if not cwd:
        cwd = Path(os.getcwd())
    if os.path.exists(Path(cwd) / Path(".pit")):
        print("This already seems to be a pit repo")
        return 1
    os.makedirs(Path(cwd) / Path(".pit") / Path("objects"))
    os.makedirs(Path(cwd) / Path(".pit") / Path("refs"))
    return 0


def add(cwd: str | Path | None = None, files: List[str] = []):
    pass


def commit(cwd: str | Path | None = None):
    if not cwd:
        cwd = Path(os.getcwd())
    ws = Workspace(cwd)
    pit_path = Path(ws.basepath) / Path(".pit")

    db_path = pit_path / Path("objects")
    db = Database(db_path)
    for f in ws.list_files():
        if os.path.isdir(f):
            tree = build_tree(ws.basepath)
            db.store(tree)
            continue
        else:
            with open(f, "rb") as fi:
                blob = Blob(data=fi.read(), name=Path(f).name)
            db.store(blob)

    return 0
