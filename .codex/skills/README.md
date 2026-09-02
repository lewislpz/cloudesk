# Skill System

Skills are portable decision and execution guides. They improve agent performance
without replacing repository evidence or the active workflow.

## Precedence

Apply guidance in this order:

1. user intent, tool permissions, and security constraints
2. active workflow and control-plane rules
3. verified repository documentation and established patterns
4. stack-specific skill guidance
5. generic skill guidance

Stop and record the conflict when a lower-priority skill contradicts a higher-priority
source.

## Progressive Disclosure

`SKILL.md` is the operational entrypoint. Read it first and load only the references
needed for the current decision. References preserve detailed knowledge and examples;
they are not automatically binding conventions.

## Portable Skill Contract

Every skill must:

- describe a precise `Use when...` trigger
- detect repository context before prescribing tools or structure
- state when not to use the skill
- prefer existing project commands and conventions
- distinguish required safety constraints from advisory defaults
- link only to existing local references and available skills
- keep `SKILL.md` within the validated entrypoint budget

Repository-specific conventions belong outside the reusable package or in an
explicitly project-scoped skill.
