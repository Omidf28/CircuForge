"""Reject common credential signatures in staged blobs without printing values."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b"),
    "API token": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "credential assignment": re.compile(
        r'''(?i)["']?\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|auth[_-]?token)["']?\s*[:=]\s*["'][^"'\r\n]{8,}["']'''
    ),
}


def findings(content: bytes) -> list[tuple[str, int]]:
    text = content.decode("utf-8", errors="replace")
    return [(label, text.count("\n", 0, match.start()) + 1)
            for label, pattern in PATTERNS.items() for match in pattern.finditer(text)]


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], stderr=subprocess.PIPE)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true", required=True)
    parser.parse_args(argv)
    try:
        names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split(b"\0")
        count = 0
        failed = False
        for raw_name in names:
            if not raw_name:
                continue
            name = raw_name.decode("utf-8", errors="surrogateescape")
            count += 1
            for label, line in findings(git("show", ":" + name)):
                # Only paths, line numbers and finding categories reach stdout.
                print(f"{name}:{line}: possible {label}; remove the credential before committing", file=sys.stderr)
                failed = True
        if failed:
            return 1
        print(f"Staged credential scan: {count} files checked; no common credential signatures found.")
        return 0
    except subprocess.CalledProcessError:
        print("Credential scan could not read the Git index; commit blocked.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
