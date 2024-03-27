from pit.workspace import Workspace
import logging
import os

logger = logging.getLogger(__name__)

TEST_DIR = "test_data/"

def test_workspace_listfiles():
    wd = Workspace(TEST_DIR)
    files = [os.path.basename(f) for f in wd.list_files()]
    assert "a.txt" in files
