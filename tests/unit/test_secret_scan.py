import importlib.util
from pathlib import Path

import pytest

module_spec = importlib.util.spec_from_file_location(
    "secret_scan", Path(__file__).resolve().parents[2] / "scripts/check_secrets.py"
)
scanner = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(scanner)


@pytest.mark.parametrize("content", [
    "gh" + "p_" + "a" * 36,
    "github_" + "pat_" + "a" * 50,
    "sk-" + "a" * 32,
    "AK" + "IA" + "A" * 16,
    "-----BEGIN " + "PRIVATE KEY-----",
    '"api_' + 'key": "' + "a" * 20 + '"',
    "password" + " = '" + "a" * 20 + "'",
])
def test_credential_signatures_are_detected_without_values(content):
    found = scanner.findings(("safe line\n" + content).encode())
    assert found
    assert all(line == 2 and content not in label for label, line in found)


def test_documentation_and_environment_variable_reference_are_allowed():
    assert not scanner.findings(b"Do not commit API keys. os.environ.get('API_KEY')")
