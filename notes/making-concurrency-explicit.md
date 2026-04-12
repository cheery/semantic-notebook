# Making Concurrency Explicit

Tools for making assumptions visible so bugs become catchable before they happen. These don't fix [POSIX](posix-and-accidental-concurrency.md), but they make the problems visible at the program level.

## Algebraic types

Make invalid states unrepresentable. If `Note` is `ExistingNote(path, content, mtime)` or `DeletedNote(path)`, you can't accidentally treat a deleted note as if it still has content. The type system enforces handling both cases.

Example from the [semantic notebook](semantic-notebook-specification.md): the TUI's history stack holds `Note` objects. If an external process deletes the file, the Note in memory is a ghost. An algebraic type would force code to handle the deleted case at every point where a Note is used.

Languages with algebraic types: Rust (enum + match), Haskell (ADTs), OCaml, Swift, Kotlin (sealed classes).

## Pre and post-conditions

Specify what an operation requires and what it guarantees. Design by Contract (Eiffel, Dafny).

- **Precondition**: what must be true before the operation runs
- **Postcondition**: what is guaranteed to be true after

Example: `sync_index` has an implicit precondition that no other process is writing to ChromaDB. Making that explicit turns a latent concurrency bug into a visible design question: "how do we ensure this precondition holds?"

Pre/post-conditions make the seams between components visible. If a precondition is hard to guarantee, that's where the concurrency problem lives.

## Invariants

Properties that must always hold. Already present in the [specification](semantic-notebook-specification.md) but implicit in the code.

Example invariant: "TUIState.note_list reflects files in notes/ at time of last load." The qualifier "at time of last load" is honest about the weakness — and that honesty is what reveals the [staleness seam](concurrency-in-semantic-notebook.md).

Stating invariants explicitly means you can check them. If an invariant is expensive to maintain, that's a design signal.

## State machines

Model legal transitions between states. Illegal transitions are bugs by definition.

Example from the TUI: modes are browse, search, clusters. Right now the mode is a string — any string is valid. A state machine would define legal transitions: browse→search, search→browse, browse→clusters, clusters→browse. The transition search→clusters would be a bug.

State machines are especially useful for UI, protocol handling, and any system where the set of valid operations depends on current state.

## The chain

These four constructs share a principle: **make assumptions explicit, make them checkable, let the machine help find the gaps.**

1. Algebraic types → the data model can't represent invalid states
2. Pre/post-conditions → the seams between components have visible contracts
3. Invariants → the consistency rules are stated, not implicit
4. State machines → the legal behaviors are enumerated, not assumed

A semi-formal specification using these constructs is something an LLM can reason about. Not formally verify, but read and check: "You said the precondition for sync_index is no concurrent writers, but the TUI calls it from a background thread while the user might also run CLI sync. Is that a problem?"

## Relation to the bigger picture

These tools address the symptom (bugs from implicit assumptions) even if they don't fix the root cause ([POSIX shared mutable state](posix-and-accidental-concurrency.md)). They make the [seams](pipelines-and-seams.md) visible so programmers can focus attention where it matters. The [GUI model language](gui-model-language.md) idea would use these same constructs.
