# Git Workflow

A clean git workflow keeps the codebase manageable.

Branch strategy:
- `main` — stable, deployable code
- `feature/*` — new features
- `fix/*` — bug fixes

Always write meaningful commit messages. Squash WIP commits before merging.
Rebase feature branches onto main to keep history linear.
