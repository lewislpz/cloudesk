# Review Context

Use this context for task reviews and code-review style checks.

## Behavior

- Prioritize bugs, regressions, security issues, and missing tests.
- Be explicit about severity and affected files.
- Prefer concrete evidence over style opinions.

## Review Order

1. Spec compliance
2. Security and safety
3. Architecture and boundary discipline
4. Tests, docs, and maintainability

## Preferred Tools

- `git diff`
- `rg`
- `sed -n`
- focused build or test commands when needed
