from pit.blob import Blob
import os
from pathlib import Path
import shutil

current_file = Path(__file__).parent.absolute()


def cleanup(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def create_file(path: str | Path, content: str):
    with open(path, "w") as f:
        f.write(content)


def setup(path):
    create_file(Path(path) / Path("a.txt"), "This is A")
    create_file(Path(path) / Path("b.txt"), "This is B")
    create_file(Path(path) / Path("c.txt"), "This is C")
    os.makedirs(Path(path) / Path("folder"))
    create_file(Path(path) / Path("folder") / Path("d.txt"), "This is D")


def test_encode():
    data = bytes("world", encoding="ascii")
    blob = Blob(data)
    content = blob.db_encode()
    assert blob.oid == "cc628ccd10742baea8241c5924df992b5c019f71"
    assert str(content, encoding="ascii") == "blob 6\x00world\n"


def test_init():
    from pit.commands import init

    test_dir = current_file / Path(test_init.__name__)
    cleanup(Path(test_dir))
    os.makedirs(test_dir)

    r = init(test_dir)
    assert r == 0
    assert os.path.exists(Path(test_dir) / Path(".pit"))
    assert os.path.exists(Path(test_dir) / Path(".pit") / Path("objects"))
    assert os.path.exists(Path(test_dir) / Path(".pit") / Path("refs"))

    cleanup(Path(test_dir))


def test_commit():
    from pit.commands import commit, init

    test_dir = current_file / Path(test_commit.__name__)
    cleanup(Path(test_dir))
    os.makedirs(test_dir)
    setup(test_dir)

    r = init(test_dir)
    assert r == 0
    commit(test_dir)

    cleanup(Path(test_dir))
