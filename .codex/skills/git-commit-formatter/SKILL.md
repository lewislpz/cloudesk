---
name: git-commit-formatter
description: Use when the user asks to write or validate a Conventional Commit message.
---

# Git Commit Formatter Skill

When writing a git commit message, you MUST follow the Conventional Commits specification.

## Format
`<type>[optional scope]: <description>`

## Common Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries such as documentation generation
- **build**: Build system or dependency changes
- **ci**: Continuous integration changes
- **revert**: Reverts a previous commit

Prefer the repository's established Conventional Commit types and scopes. The
specification permits project-defined types beyond this common list.

## Instructions
1. Analyze the changes to determine the primary `type`.
2. Identify the `scope` if applicable (e.g., specific component or file).
3. Write a concise `description` in imperative mood (e.g., "add feature" not "added feature").
4. If there are breaking changes, add a footer starting with `BREAKING CHANGE:`.

## Example
`feat(auth): implement login with google`
