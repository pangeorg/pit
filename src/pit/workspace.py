import os
from pathlib import Path

class Workspace:
    def __init__(self, basepath):
        self.basepath = Path(os.path.abspath(basepath))

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
