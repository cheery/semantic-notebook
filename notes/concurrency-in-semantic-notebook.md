# Concurrency in Semantic Notebook

A concrete example of the [pipelines-and-seams](pipelines-and-seams.md) problem, found in this project.

## The setup

Two processes access the same `notes/` directory simultaneously:
- **The TUI** — reads notes into memory, displays them, keeps a history stack
- **An external editor or LLM** — writes, modifies, and deletes note files

Neither process knows the other exists. No coordination mechanism.

## What actually happens

### Staleness

The TUI loads notes once on mount. After that, it only reloads on explicit user actions: editing a note, pressing `r` to re-index, or creating a new note. If an external process changes a file, the TUI shows stale content until the user manually triggers a refresh.

### Ghost notes

The TUI keeps a history stack of `Note` objects in memory. If an external process deletes a file that's in the history, pressing `b` to go back loads the stale `Note` from memory — its content is still there but the file no longer exists on disk. The note list and the filesystem are two views of the same truth that have drifted apart.

### Why it doesn't corrupt

`read_note` uses `path.read_text()` and `write_note` uses `path.write_text()` — single syscalls on Linux. No partial writes visible. The operating system handles byte-level consistency. The problem isn't corruption, it's coherence.

## The fix

Use `inotify` (via the `watchdog` Python library) to watch `notes/` for filesystem events. When a file changes or is deleted, the TUI reloads the affected note or removes it from the list and history. Standard pattern — every modern editor does this.

The technical fix is straightforward. The design decisions are harder: silently reload vs. notify, what to do if the user is actively editing the same file, how to handle the history stack when a note disappears.

## Why this is the seams problem

The notebook is mostly pipelines: read file → embed → store, embed query → search → display. Clean, stateless, reproducible. But the TUI layer is where state lives — the current note, the history stack, the display. That state can become inconsistent with the filesystem. The seam is between the pipeline (file operations) and the interactive state (what the user sees).
