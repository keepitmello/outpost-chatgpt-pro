from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "secret_scan.py"
SPEC = importlib.util.spec_from_file_location("outpost_secret_scan_test", SCRIPT)
assert SPEC and SPEC.loader
SCAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCAN)

GITHUB = "ghp_" + ("A" * 36)
GITHUB_PAT = "github_pat_" + ("B" * 22)
ANTHROPIC = "sk-ant-api03-" + ("C" * 24)
OPENAI = "sk-proj-" + ("D" * 24)
OPENAI_STRUCTURED = "sk-proj-" + ("D_-" * 10)
OPENAI_DASH_SUFFIX = "sk-proj-" + ("D" * 19) + "-"
OPENAI_LEGACY = "sk-" + ("L" * 48)
SLACK = "xoxb-1234567890-abcdefghij"
GOOGLE = "AIza" + ("E" * 35)
AWS_SECRET = "F" * 40
BEARER = "tok_live_not_a_real_credential_value"


class SecretScanTest(unittest.TestCase):
    def _rules(self, text: str) -> list[str]:
        return [item.rule for item in SCAN.scan_packet_text(text)]

    def test_positive_pem_github_anthropic_openai(self) -> None:
        packet = "\n".join(
            [
                "# Topic",
                "-----BEGIN RSA PRIVATE KEY-----",
                GITHUB,
                ANTHROPIC,
                OPENAI,
                OPENAI_STRUCTURED,
                OPENAI_DASH_SUFFIX,
                OPENAI_LEGACY,
            ]
        )
        self.assertEqual(
            self._rules(packet),
            [
                "pem-private-key",
                "github-token",
                "anthropic-key",
                "openai-key",
                "openai-key",
                "openai-key",
                "openai-key",
            ],
        )

    def test_positive_slack_google_aws_bearer(self) -> None:
        packet = "\n".join(
            [
                "# Topic",
                SLACK,
                GOOGLE,
                f"aws_secret_access_key = {AWS_SECRET}",
                f"Authorization: Bearer {BEARER}",
                f'Authorization: "Bearer {BEARER}"',
                f"curl -H 'Authorization: Bearer {BEARER}' https://example.com",
            ]
        )
        self.assertEqual(
            self._rules(packet),
            [
                "slack-token",
                "google-api-key",
                "aws-secret-access-key",
                "authorization-bearer",
                "authorization-bearer",
                "authorization-bearer",
            ],
        )

    def test_positive_github_fine_grained_and_quoted_bearer(self) -> None:
        packet = (
            f"# Topic\n{GITHUB_PAT}\n"
            f'headers = {{"Authorization": "Bearer {BEARER}"}}\n'
        )
        self.assertEqual(
            self._rules(packet),
            ["github-token", "authorization-bearer"],
        )

    def test_negative_akia_jwt_generic_placeholders_pii(self) -> None:
        packet = "\n".join(
            [
                "# Topic",
                "aws_access_key_id=AKIAIOSFODNN7EXAMPLE",
                "aws_access_key_id=ASIAIOSFODNN7EXAMPLE",
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.signature",
                'token = "supersecret"',
                "password: hunter2",
                "OPENAI_API_KEY=${OPENAI_API_KEY}",
                "key = process.env.OPENAI_API_KEY",
                'key = os.environ["OPENAI_API_KEY"]',
                "github=<YOUR_GITHUB_TOKEN>",
                f"aws_secret_access_key=${{AWS_SECRET}}",
                "aws_secret_access_key=changemechangemechangemechangemechangeme",
                "Authorization: Bearer <token>",
                "Authorization: Bearer redacted",
                "Authorization: Bearer short-token",
                "xoxb-short-token",
                "sk-notarealkeybutlongenough12345",
                "sk-proj-exampleexampleexampleexample",
                "aws_secret_access_key=" + ("A" * 41),
                f"Authorization: Bearer {BEARER[:0] and BEARER}${{TOKEN}}",
                "Bearer " + BEARER,
                "email: alice@example.com",
                "customer_id: cust_12345 order=42",
            ]
        )
        self.assertEqual(self._rules(packet), [])

    def test_openai_does_not_claim_anthropic_and_public_pem_is_ignored(self) -> None:
        packet = "\n".join(
            [
                "# Topic",
                "-----BEGIN PUBLIC KEY-----",
                "-----BEGIN CERTIFICATE-----",
                ANTHROPIC,
            ]
        )
        self.assertEqual(self._rules(packet), ["anthropic-key"])

    def test_report_never_echoes_match_or_length_and_does_not_mutate(self) -> None:
        original = f"# Topic\n{OPENAI}\n"
        snapshot = original
        findings = SCAN.scan_packet_text(original)
        report = SCAN.format_findings(findings)
        self.assertEqual(original, snapshot)
        self.assertTrue(report.startswith(SCAN.MARKER + "\n"))
        self.assertEqual(findings[0].rule, "openai-key")
        self.assertEqual(findings[0].line, 2)
        self.assertIn("openai-key 2:", report)
        self.assertNotIn(OPENAI, report)
        self.assertNotIn(str(len(OPENAI)), report)
        self.assertNotIn(OPENAI[:8], report)
        self.assertNotRegex(report, r"\blen(?:gth)?\s*[:=]")

    def test_marker_and_exit_code_are_stable(self) -> None:
        self.assertEqual(SCAN.MARKER, "OUTPOST_SECRET_SCAN")
        self.assertEqual(SCAN.EXIT_CODE, 2)
        self.assertFalse(hasattr(SCAN, "ALLOW_SECRETS"))
        self.assertFalse(hasattr(SCAN, "allow_secrets"))


if __name__ == "__main__":
    unittest.main()
