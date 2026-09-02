---
name: writing-skills
description: Use when creating new or editing existing skills. Ensures skills are tested, discoverable, and resist agent rationalization.
---

# Writing Skills (TDD for Process)

## Overview

A **Skill** is an executable reference guide. Writing a skill is **Test-Driven Development applied to documentation**.

## The Iron Law

> **NO SKILL WITHOUT A FAILING TEST FIRST.**

1.  **RED**: Add a case under `.codex/evals/cases/` and run a scenario where the agent is likely to fail or rationalize away a rule.
2.  **GREEN**: Write the minimal `SKILL.md` that prevents this specific failure.
3.  **REFACTOR**: Run the scenario again with the skill loaded. Ensure compliance and close loopholes.

## Structure of a Skill

Every skill directory must have:
-   `SKILL.md`: The main executable instruction.
-   `references/`: (Optional) Detailed knowledge loaded only when relevant.
-   `examples/`: (Optional) Before/After code or workflow examples.
-   `scripts/`: (Optional) Automations that support the skill.

## SKILL.md Standard

### 1. YAML Frontmatter
-   `name`: Lowercase, hyphenated (e.g., `writing-robust-tests`).
-   `description`: Start with "Use when...". Describe **triggering conditions**, NOT what the skill does.

### 2. Implementation Rules
-   **No Narratives**: Don't tell stories about how you fixed a bug once.
-   **Anti-Rationalization**: Explicitly forbid common excuses (e.g., "Don't say 'it's too simple to test'").
-   **Exact Paths**: Always use absolute or framework-relative paths.
-   **Context First**: Detect repository conventions before prescribing a stack,
    architecture, dependency, or command.
-   **No Broken Handoffs**: Link only to local references and skills that exist.

## Checklist for New Skills
- [ ] Has a pressure-tested "Failing Test" been performed?
- [ ] Is the regression case recorded under `.codex/evals/cases/`?
- [ ] Description starts with "Use when..."?
- [ ] Forbids common rationalizations?
- [ ] Entrypoint is within the validated word budget?
- [ ] Detailed examples live in selectively loaded references?
