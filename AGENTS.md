# AGENTS.md

## Goal
Prepare this repository for a conservative public reproducibility release tied to `paper.pdf`.

## Working style
- Be conservative with all changes.
- Prefer planning, auditing, and proposing changes before editing files.
- Before making any non-trivial change, first explain briefly:
  - what you want to change
  - why it is needed for reproducibility or public release readiness
  - which files/folders will be affected
- Wait for my approval before making edits, moving files, deleting files, or adding new files, except for audit documents in `docs/` when explicitly requested.
- Keep explanations concise and practical.

## Safety rules
- Do not permanently delete uncertain files. Move them to `review_archive/` or propose doing so.
- Flag any potentially non-shareable or sensitive data.
- Flag machine-specific assumptions, logs, caches, virtual environments, duplicate outputs, and generated artifacts.
- Ask for confirmation before adding dependencies, changing execution flow, or removing intermediate results.

## Reproducibility focus
- Tie recommendations to reproducing the paper’s figures, tables, and claims.
- Distinguish clearly between:
  - essential reproducibility artifacts
  - optional convenience artifacts
  - local clutter / non-essential files

## Output conventions
- Save audit/planning outputs in `docs/`.
- When proposing changes, use this format:

  Proposed change:
  Why:
  Affected files:
  Approval needed: yes

- Keep proposals short unless I ask for more detail.