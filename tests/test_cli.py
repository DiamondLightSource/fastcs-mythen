import subprocess
import sys

from fastcs_mythen import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "fastcs_mythen", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
