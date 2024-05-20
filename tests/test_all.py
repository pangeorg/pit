from pit.objects import Blob
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
    import subprocess

    os.makedirs(Path(path), exist_ok=True)
    create_file(Path(path) / Path("a.txt"), "This is A")
    create_file(Path(path) / Path("b.txt"), "This is B")
    create_file(Path(path) / Path("c.txt"), "This is C")
    create_file(Path(path) / Path(".gitignore"), ".pit/")
    os.makedirs(Path(path) / Path("folder"))
    create_file(Path(path) / Path("folder") / Path("d.txt"), "This is D")
    create_file(Path(path) / Path("folder") / Path("e.txt"), "This is E")

    cwd = os.getcwd()
    os.chdir(path)
    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", ".gitignore"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", '"initial"'])
    os.chdir(cwd)


def test_encode():
    data = bytes("world", encoding="ascii")
    blob = Blob(name="world.txt", data=data)
    content = blob.db_encode()
    assert blob.oid == "04fea06420ca60892f73becee3614f6d023a4b7f"
    assert str(content, encoding="ascii") == "blob 5\x00world"


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


def test_add():
    from pit.commands import add

    pass


def test_commit():
    from pit.commands import commit, init

    test_dir = current_file / Path(test_commit.__name__)
    cleanup(Path(test_dir))
    os.makedirs(test_dir)
    setup(test_dir)

    r = init(test_dir)
    assert r == 0
    commit(test_dir)
    assert False

    # cleanup(Path(test_dir))
