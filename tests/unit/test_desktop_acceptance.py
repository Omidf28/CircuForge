"""Incomplete/duplicate desktop evidence cannot satisfy the read-only gate."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest
from PIL import Image

from circuforge.desktop.model import FormValues, build_request

REPO = Path(__file__).resolve().parents[2]


def command():
    spec = importlib.util.spec_from_file_location("desktop_acceptance_tests", REPO / "scripts/accept_desktop.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("count", [0, 2])
def test_incomplete_gui_run_set_blocks(tmp_path, count):
    checker = command()
    for index in range(count):
        (tmp_path / str(index)).mkdir()
    with pytest.raises(ValueError, match="incomplete"):
        checker.audit_gui_runs(tmp_path, checker.SOURCE_CASES)


def test_duplicate_case_cannot_replace_missing_topology_or_target_miss(tmp_path, monkeypatch):
    checker = command()
    request = build_request(FormValues())
    for index in range(3):
        path = tmp_path / str(index)
        path.mkdir()
        (path / "request.json").write_text(request.model_dump_json())
        (path / "report.json").write_text("fixture, not electrical evidence")
    fixture = SimpleNamespace(status="passed", simulator_calls=1,
                              best=SimpleNamespace(measured_cutoff_hz=2300., relative_error=0.))
    monkeypatch.setattr(checker, "audit_design", lambda *args: fixture)
    with pytest.raises(ValueError, match="duplicate"):
        checker.audit_gui_runs(tmp_path, checker.SOURCE_CASES)


@pytest.mark.parametrize("suffix,format", [(".jpg", "JPEG"), (".png", "PNG")])
def test_native_screenshot_encodings_are_verified_without_transcoding(tmp_path, suffix, format):
    path = tmp_path / ("synthetic-fixture" + suffix)
    Image.new("RGB", (1100, 720), "white").save(path, format=format)
    checker = command()
    assert checker.audit_screenshot(path) == checker.digest(path)


@pytest.mark.parametrize("mode", ["small", "mislabeled", "truncated"])
def test_invalid_or_mislabeled_screenshot_evidence_blocks(tmp_path, mode):
    path = tmp_path / "synthetic-fixture.png"
    size = (200, 200) if mode == "small" else (1100, 720)
    Image.new("RGB", size, "white").save(path, format="JPEG" if mode == "mislabeled" else "PNG")
    if mode == "truncated":
        path.write_bytes(path.read_bytes()[:40])
    with pytest.raises((ValueError, OSError)):
        command().audit_screenshot(path)


@pytest.mark.parametrize("corrupt_installed", [False, True])
def test_install_provenance_tracks_the_wheel_not_a_screenshot(tmp_path, monkeypatch, corrupt_installed):
    checker = command()
    project = tmp_path / "project"
    source = project / "src/circuforge/__init__.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"# package metadata fixture, not a runnable circuit engine\n")
    interface = tmp_path / "interface"
    (interface / "wheels").mkdir(parents=True)
    installed = interface / "installed/site-packages/circuforge/__init__.py"
    installed.parent.mkdir(parents=True)
    installed.write_bytes(b"modified" if corrupt_installed else source.read_bytes())
    wheel = interface / "wheels/circuforge-fixture.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("circuforge/__init__.py", source.read_bytes())
    screenshot = tmp_path / "screenshot.jpg"
    Image.new("RGB", (1100, 720), "white").save(screenshot)
    monkeypatch.setattr(checker, "ROOT", project)
    if corrupt_installed:
        with pytest.raises(ValueError, match="package bytes differ"):
            checker.audit_installed_package(interface, installed, checker.digest(wheel))
    else:
        proof = checker.audit_installed_package(interface, installed, checker.digest(wheel))
        checker.audit_screenshot(screenshot)
        assert proof == {"wheel_sha256": checker.digest(wheel), "package_python_files": 1}
        assert proof["wheel_sha256"] != checker.digest(screenshot)
