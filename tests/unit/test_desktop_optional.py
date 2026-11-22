"""GUI dependencies must stay optional for core and API users."""
import os
from pathlib import Path
import subprocess
import sys

from circuforge import __version__
from circuforge.api import create_app


def without_tk(code):
    source = Path(__file__).resolve().parents[2] / "src"
    prefix = """
import sys
class NoTk:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'tkinter' or fullname.startswith('tkinter.'):
            raise ImportError('controlled absence of optional Tk')
sys.meta_path.insert(0, NoTk())
"""
    return subprocess.run([sys.executable, "-c", prefix + code], capture_output=True, text=True,
                          env={**os.environ, "PYTHONPATH": str(source)}, timeout=15, shell=False)


def test_core_and_api_can_import_without_tkinter():
    result = without_tk("\nimport circuforge.application, circuforge.api\nprint('core available')\n")
    assert result.returncode == 0 and "core available" in result.stdout


def test_gui_reports_missing_tk_as_a_dependency_error():
    result = without_tk("\nfrom circuforge.desktop.app import main\nraise SystemExit(main([]))\n")
    assert result.returncode == 2 and "install Python Tk support" in result.stderr
    assert "Traceback" not in result.stderr


def test_api_version_tracks_the_installed_package():
    assert create_app().openapi()["info"]["version"] == __version__
