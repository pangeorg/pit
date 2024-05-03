import os
from pathlib import Path


class Workspace:
    def __init__(self, path):
        current_path = Path(os.path.abspath(path))
        while ".pit" not in [p.name for p in list(current_path.iterdir())]:
            current_path = current_path.parent
            if current_path == Path("/"):
                raise Exception("We are not in a .pit repository")
        self.basepath = current_path

    def list_files(self):
        from glob import glob

        paths = glob(str(self.basepath) + "/**/*", recursive=True)
        for path in paths:
            yield self.basepath / Path(path)

    def read_file(self, filepath: str | Path):
        if isinstance(filepath, str):
            filepath = Path(filepath)
        with open(filepath, "rb") as f:
            return f.read()
