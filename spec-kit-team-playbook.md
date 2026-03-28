# Spec Kit Team Playbook

## Purpose

This playbook defines a safe team workflow for using `github/spec-kit` with multiple coding agents such as Claude, Codex, and Copilot in the same repository.

The key rule is simple:

- treat `specify init --ai <agent> --force` as an **agent-specific setup step**
- treat files under `specs/` as **shared project artifacts**

## Recommended Model

Use **one worktree per agent**. Do not run different `specify init` commands in the same active checkout if multiple people are working in parallel.

### Example worktree layout

- `../SwingTrader-claude`
- `../SwingTrader-codex`
- `../SwingTrader-copilot`

## Setup Workflow

### Claude worktree

```bash
git worktree add ../SwingTrader-claude -b spec-claude
cd ../SwingTrader-claude
specify init --here --ai claude --force
```

### Codex worktree

```bash
git worktree add ../SwingTrader-codex -b spec-codex
cd ../SwingTrader-codex
specify init --here --ai codex --force
```

### Copilot worktree

```bash
git worktree add ../SwingTrader-copilot -b spec-copilot
cd ../SwingTrader-copilot
specify init --here --ai copilot --force
```

## What Is Safe To Share

These files should be treated as shared team assets:

- `specs/**`
- source code
- research documents
- implementation notes

These files can usually be merged and reviewed like normal project work.

## What Is Not Safe To Share Blindly

These files may be rewritten by `specify init --force` and should be treated as agent-local or setup-sensitive:

- `.specify/**`
- agent-specific command or prompt files
- generated integration files tied to one AI tool

Do not assume a Claude init and a Codex init will coexist cleanly in the same checkout.

## Team Rules

1. Run `specify init --force` only at the start of your own agent worktree setup.
2. Do not rerun `specify init` in a teammate’s active checkout.
3. Commit shared spec changes from `specs/**`, not agent-specific setup churn, unless the team explicitly wants to update the canonical setup.
4. If the team wants one official repository setup, nominate one primary agent and standardize on that in the main branch.
5. If you must switch agents in one checkout, do it intentionally and expect setup files to change.

## Merge Strategy

- Merge `specs/**` and code changes normally through pull requests.
- Review `.specify/**` changes separately.
- If `.specify/**` changes are only agent-specific noise, do not merge them to the main branch.
- If the team decides to change the canonical agent, make that a dedicated PR with a clear description.

## Default Recommendation

For parallel teamwork:

- keep `specs/**` shared
- keep agent setup isolated per worktree
- use one canonical agent setup on `main`

This gives each contributor a reliable local environment without forcing the whole team to use the same AI tool every day.
