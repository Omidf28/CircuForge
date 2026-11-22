import pytest

from circuforge.evaluation.acceptance import AcceptanceError, evidence_file, validate_junit


@pytest.mark.parametrize("body", ["<testsuites/>",
    '<testsuites><testsuite tests="1"><testcase><skipped/></testcase></testsuite></testsuites>',
    '<testsuite tests="1"><testcase><failure/></testcase></testsuite>',
    '<testsuite tests="1" errors="1"><testcase/></testsuite>'])
def test_incomplete_or_nonpassing_test_evidence_is_blocked(tmp_path, body):
    path = tmp_path / "test.xml"
    path.write_text(body)
    with pytest.raises(AcceptanceError):
        validate_junit(path)


def test_valid_test_xml_and_unsafe_artifact_path(tmp_path):
    # Synthetic XML exercises validation only; it is not a test-run record.
    path = tmp_path / "test.xml"
    path.write_text('<testsuite tests="1"><testcase name="xml-fixture"/></testsuite>')
    assert validate_junit(path) == 1
    inside = tmp_path / "inside"
    inside.mkdir()
    with pytest.raises(AcceptanceError):
        evidence_file(inside, "../test.xml")
