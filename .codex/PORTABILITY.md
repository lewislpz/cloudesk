# Copy-Paste Adoption

Copy `.codex/` into the root of any repository, then run:

```sh
bash .codex/scripts/bootstrap.sh
```

The bootstrap is idempotent. It:

- checks required tools
- creates configured workspace roots
- installs the managed workflow block into root `AGENTS.md`
- adds portable generated-file exclusions to `.gitignore`
- validates the package and configuration

It preserves existing `AGENTS.md` and `.gitignore` content. Project conventions belong
in `.codex/config.json`; product guidance belongs in root documentation or optional
project skills.

## Start Building

Use `/think` or ask Codex to follow `.codex/workflows/think.md` for non-trivial work.
After approving the resulting plan, use `/forge` or ask Codex to follow
`.codex/workflows/forge.md`.

## Minimum Environment

- Bash
- Python 3.9 or newer
- ripgrep (`rg`)
- Git when Git binding or delivery is required
