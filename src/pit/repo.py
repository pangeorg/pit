from pathlib import Path
from configparser import ConfigParser
import os


class Repository:
    """The git repo"""

    def __init__(self, path: str | Path, force=False):
        self.worktree: Path = Path(path)
        self.gitdir: Path = Path(path) / Path(".pit")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception("Not a pit repo, %s", path)

        self.conf = self._read_config(force=force)

    def _read_config(self, force=False):

        config_file = repo_file(self, "config")

        conf = ConfigParser()
        if config_file and os.path.exists(config_file):
            conf.read([config_file])
        elif not force:
            raise Exception("Config file missing!")
        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(
                    "Unsupported repositoryformatversion %s" % vers)
        return conf


def repo_create(path: str):
    """Create a new repository at path."""

    repo = Repository(path, True)

    # First, we make sure the path either doesn't exist or is an
    # empty dir.

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception("%s is not a directory!" % path)
        if os.path.exists(repo.gitdir) and os.listdir(repo.gitdir):
            raise Exception("%s is not empty!" % path)
    else:
        os.makedirs(repo.worktree)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    # .git/description
    with open(repo_file(repo, "description"), "w") as f:
        f.write(
            "Unnamed repository; edit this file to name the repository.\n")

    # .git/HEAD
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo


def repo_default_config():
    ret = ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret


def repo_path(repo, *path) -> Path:
    """Compute path under repo's gitdir."""
    return Path(os.path.join(repo.gitdir, *path))


def repo_dir(repo, *path, mkdir=False):
    """Same as repo_path, but mkdir *path if absent if mkdir."""

    path = repo_path(repo, *path)

    if os.path.exists(path):
        if (os.path.isdir(path)):
            return path
        else:
            raise Exception("Not a directory %s" % path)

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None


def repo_file(repo, *path, mkdir=False) -> Path:
    """Same as repo_path, but create dirname(*path) if absent.  For
example, repo_file(r, \"refs\", \"remotes\", \"origin\", \"HEAD\") will create
.git/refs/remotes/origin."""

    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


def repo_find(path=Path("."), required=True) -> Repository:
    path = Path(os.path.realpath(path))

    if (path / Path(".git")).exists():
        return Repository(path)

    # If we haven't returned, recurse in parent, if w
    parent = path.parent

    if parent == path:
        if required:
            raise Exception("No git directory.")
        else:
            return None

    # Recursive case
    return repo_find(parent, required)
