"""High-confidence credential scan for Outpost packet.md files.

Pure module: never mutates the packet and never returns matched secret
text or any derived length of a match. Findings report only a rule name,
1-based line/column, and a static remediation hint.
"""

from __future__ import annotations

import re

MARKER = "OUTPOST_SECRET_SCAN"
EXIT_CODE = 2


class Finding:
    __slots__ = ("rule", "line", "column", "hint")

    def __init__(self, rule: str, line: int, column: int, hint: str) -> None:
        self.rule = rule
        self.line = line
        self.column = column
        self.hint = hint


_PEM_PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----")
_GITHUB_TOKEN = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,})"
)
_ANTHROPIC_KEY = re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")
_OPENAI_KEY = re.compile(
    r"(?:sk-(?:proj-|svcacct-)[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_-])"
    r"|sk-[A-Za-z0-9]{48}(?![A-Za-z0-9]))"
)
_SLACK_TOKEN = re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}")
_GOOGLE_API_KEY = re.compile(r"AIza[0-9A-Za-z\-_]{35}")
_AWS_SECRET_ACCESS_KEY = re.compile(
    r"(?ix)aws_secret_access_key\s*[=:]\s*(?:['\"])?"
    r"([A-Za-z0-9/+=]{40})(?![A-Za-z0-9/+=])(?:['\"])?"
)
_AUTHORIZATION_BEARER = re.compile(
    r"(?i)\bAuthorization[\"']?\s*:\s*[\"']?"
    r"Bearer\s+([A-Za-z0-9._~+/=-]{20,})"
)

_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "pem-private-key",
        _PEM_PRIVATE_KEY,
        "Remove the PEM private key from the packet and load it from a secret store.",
    ),
    (
        "github-token",
        _GITHUB_TOKEN,
        "Remove the GitHub token from the packet and use a scoped secret store.",
    ),
    (
        "anthropic-key",
        _ANTHROPIC_KEY,
        "Remove the Anthropic API key from the packet and load it from a secret store.",
    ),
    (
        "openai-key",
        _OPENAI_KEY,
        "Remove the OpenAI API key from the packet and load it from a secret store.",
    ),
    (
        "slack-token",
        _SLACK_TOKEN,
        "Remove the Slack token from the packet and load it from a secret store.",
    ),
    (
        "google-api-key",
        _GOOGLE_API_KEY,
        "Remove the Google API key from the packet and load it from a secret store.",
    ),
)

_AWS_HINT = (
    "Remove the AWS secret access key from the packet and load it from a secret store."
)
_BEARER_HINT = (
    "Remove the Authorization Bearer credential from the packet "
    "and load it from a secret store."
)


def _is_placeholder(value: str) -> bool:
    trimmed = value.strip().strip("'\"")
    if not trimmed:
        return True
    if "${" in trimmed or "process.env" in trimmed or "os.environ" in trimmed:
        return True
    if re.fullmatch(r"<[^>]+>", trimmed):
        return True
    lowered = trimmed.lower()
    lowered = re.sub(
        r"^(?:sk-(?:proj-|svcacct-)?|github_pat_|gh[pousr]_|xox[baprs]-|aiza)",
        "",
        lowered,
    )
    if lowered.startswith(("redacted", "example", "changeme", "your-", "your_")):
        return True
    return False


def _offset_to_line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    column = offset + 1 if last_newline < 0 else offset - last_newline
    return line, column


def _collect_regex_findings(
    text: str,
    rule: str,
    pattern: re.Pattern[str],
    hint: str,
) -> list[Finding]:
    findings: list[Finding] = []
    for match in pattern.finditer(text):
        if _is_placeholder(match.group(0)):
            continue
        line, column = _offset_to_line_column(text, match.start())
        findings.append(Finding(rule=rule, line=line, column=column, hint=hint))
    return findings


def scan_packet_text(text: str) -> list[Finding]:
    """Return high-confidence credential findings. Does not mutate ``text``."""
    findings: list[Finding] = []
    for rule, pattern, hint in _RULES:
        findings.extend(_collect_regex_findings(text, rule, pattern, hint))
    for match in _AWS_SECRET_ACCESS_KEY.finditer(text):
        if _is_placeholder(match.group(1)):
            continue
        line, column = _offset_to_line_column(text, match.start())
        findings.append(
            Finding(rule="aws-secret-access-key", line=line, column=column, hint=_AWS_HINT)
        )
    for match in _AUTHORIZATION_BEARER.finditer(text):
        if _is_placeholder(match.group(1)):
            continue
        line, column = _offset_to_line_column(text, match.start())
        findings.append(
            Finding(rule="authorization-bearer", line=line, column=column, hint=_BEARER_HINT)
        )
    findings.sort(key=lambda item: (item.line, item.column, item.rule))
    return findings


def format_findings(findings: list[Finding]) -> str:
    lines = [MARKER]
    for item in findings:
        lines.append(f"{item.rule} {item.line}:{item.column} {item.hint}")
    return "\n".join(lines) + "\n"
