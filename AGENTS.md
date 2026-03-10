# Repository Guidelines

## Project Structure & Module Organization

This repository is a research-first workspace, not a compiled application. The main content lives under `research/`:

- `research/strategy-and-theory/` contains numbered domain documents such as `01-swing-trading-fundamentals.md` and `26-latest-research-update-and-evidence-review.md`.
- `research/technical-implementation/` contains implementation-facing design notes such as architecture, hosting, data pipelines, and monitoring.
- `.claude/` contains local tool settings; avoid editing it unless the task explicitly requires it.

Keep related additions in the correct subfolder and follow the existing numbered filename pattern.

## Build, Test, and Development Commands

There is no build system or automated test suite in the repository today. Useful local validation commands:

- `init . --ai codex` — initialize the workspace for Codex-based collaboration.
- `find research -maxdepth 3 -type f | sort` — list the document set.
- `rg -n "^#|^## " research` — inspect heading structure and consistency.
- `markdownlint "**/*.md"` — run Markdown linting if `markdownlint` is installed locally.

If you add scripts or tooling later, document the exact command here.

## Coding Style & Naming Conventions

Use Markdown with short, direct sections and descriptive headings. Match the repository’s conventions:

- English content by default.
- ASCII unless a file already requires other characters.
- Numbered filenames with hyphenated slugs, for example `27-swedish-market-adaptation.md`.
- Prefer concise paragraphs and flat bullet lists over long narrative blocks.

When adding research claims, favor primary or official sources and include links.

## Testing Guidelines

Validation is editorial and structural:

- check links, headings, and file placement
- avoid duplicate topics across files
- verify that new documents cross-reference adjacent research where useful
- for “latest” claims, confirm dates and sources before writing

## Commit & Pull Request Guidelines

No Git history is available in this workspace, so there is no repository-native commit convention to copy. Use clear, imperative commit messages such as:

- `docs: add catalyst event playbook`
- `docs: align execution guidance with SEC sources`

For pull requests, include:

- a short summary of what changed
- affected files or sections
- source notes for any new research
- screenshots only if formatting or rendered output matters

## Contributor Notes

Before creating a new file, check whether the topic already exists in `research/`. Prefer extending the research map or adding a narrowly scoped companion file instead of duplicating coverage.
