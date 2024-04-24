import os
from pathlib import Path
from pit.workspace import Workspace
from pit.database import Database
from pit.blob import Blob
import logging

logger = logging.getLogger(__name__)

# NOTE
# refactor all commands to receive the workspace


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


def commit(cwd: str | Path | None = None):
    if not cwd:
        cwd = Path(os.getcwd())
    pit_path = Path(cwd) / Path(".pit")

    if not os.path.exists(pit_path):
        print("Not a pit repo")
        return 1

    db_path = pit_path / Path("objects")
    ws = Workspace(cwd)
    db = Database(db_path)

    for path in ws.list_files():
        if os.path.isdir(path):
            print("Folders are not yet supported...")
            continue
        else:
            with open(path, "rb") as f:
                data = Blob(f.read())
                print(type(data))
        db.store(data)

    return 0
