# outpost-chatgpt-pro

A two-axis Outpost package for obtaining a verified ChatGPT project Chat second
opinion through Aside.

- `outpost/` is the normal Agent Skill. `SKILL.md` keeps only when, quality,
  packet, `outpost` commands, and verification. Engine and recovery live in
  `outpost/references/`.
- `outpost/aside-skill/chatgpt-work-outpost/` teaches Aside's own agent the
  stable project Chat browser workflow.
- `outpost-playwright/` is the uninstalled agbrowse fallback. The main package
  carries only a hidden relative link to it for explicit failure recovery.

## Requirements

- Aside Browser CLI
- A ChatGPT account signed in inside Aside Browser
- Access to a ChatGPT project; set `OUTPOST_CHATGPT_URL` and
  `OUTPOST_PROJECT_NAME` in `~/.codex/outpost.env`
- Python, Node.js, Chrome, and `agbrowse` only for the fallback

## Install

Clone the repository and link only the main skill:

```bash
git clone https://github.com/keepitmello/outpost-chatgpt-pro.git
ln -s "$(pwd)/outpost-chatgpt-pro/outpost" ~/.agents/skills/outpost
bash "$(pwd)/outpost-chatgpt-pro/outpost/scripts/install-aside-skill.sh"
bash "$(pwd)/outpost-chatgpt-pro/outpost/scripts/install-cli.sh"
```

Do not link `outpost-playwright/` into a normal skill root. The main skill reads
its hidden fallback link only after the Aside path fails.

## Verify

Verify both axes:

```bash
node ~/.aside/u/0/skills/builtin/skill-creator/scripts/validate-frontmatter.mjs \
  outpost/aside-skill/chatgpt-work-outpost/SKILL.md
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s outpost/tests -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s outpost-playwright/tests -q
```

## Usage

Read `outpost/SKILL.md`. After `install-cli.sh`, `outpost` is on PATH:

```bash
outpost list
outpost send --quality xhigh .outpost/<run>/packet.md
outpost send --quality xhigh .outpost/<run>/packet.md --to <thread-id>
outpost recover .outpost/<run>/result.json
```

Every send must explicitly choose `xhigh` or `pro`; there is no default.
Engine, Chat surface, and recovery live in `outpost/references/`.
Playwright is not an automatic sender.

## Security boundary

`outpost send` submits only through the visible ChatGPT web UI (composer,
file chip, and send control). It does not extract or persist cookies or
tokens outside the live browser process, bypass access controls,
automatically resend, or bundle browser
credentials.

After this process attempts submission, recovery may issue read-only
ChatGPT `backend-api` GETs in the live Aside session to see whether this
run's ID-bound user turn committed. Attachment retrieval through
`backend-api/files` happens only after that user-message ID is observed.
The session token is not logged or written to outputs. Recovery does not
write to the backend.

Outpost does not export cookies or tokens, alter user-owned tabs or
conversations, automate login, MFA, or CAPTCHA, evade rate limits, rotate
accounts, or use another run's conversation. An uncertain submission is
never handed to an alternate sender.

High-confidence credentials in `packet.md` are refused before Aside starts
(`OUTPOST_SECRET_SCAN`, exit 2). There is no bypass flag. Never put secrets,
private keys, customer data, or unnecessary personal data in an outpost packet.
