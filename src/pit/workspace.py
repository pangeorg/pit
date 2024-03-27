import os
from pathlib import Path

class Workspace:
    def __init__(self, basepath):
        self.basepath = Path(os.path.abspath(basepath))

    def list_files(self):
        from glob import glob
        paths = glob(str(self.basepath) + "/**/*", recursive=True)
        return [self.basepath / Path(filepath) for filepath in paths]
