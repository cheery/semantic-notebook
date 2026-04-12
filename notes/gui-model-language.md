# GUI and the Model Language Problem

GUI is the ultimate non-pipeline seam. Nothing has solved it satisfactorily.

## Why GUI resists clean patterns

A user can do anything in any order. Click, type, resize, scroll, drag — all simultaneously, all changing shared visual state. You can't pipe the user into the window. The user is an unpredictable external agent poking the system at arbitrary times.

The best pattern so far is recursive model-command-view: a central model, a command language that modifies it, and views that project it. Views themselves are small models with their own command languages — component composition. Elm, Redux, and similar architectures approximate this.

The unsolved part is the relationship between model changes and visual updates. View state — scroll position, focus, animation state, partially typed text — isn't business model state but it matters. Put it all in the model and it bloats. Let the view manage it and the pattern breaks.

## The gap in existing notations

There's no good language for *thinking* about GUI structure between "vague English description" and "working code."

- **Natural language** — too ambiguous
- **UML** — too much ceremony, captures shape but not behavior
- **State diagrams** — work for interaction but say nothing about component tree or visual hierarchy
- **Code** — too concrete, too early, forces implementation decisions during design

## What a model language could be

A notation for expressing GUI architecture: the model, the commands, the view structure, the composition. Formal enough to reveal inconsistencies — "this command modifies state that this view doesn't know about" — but not so formal it requires a PhD.

It wouldn't run, compile, or be formally verifiable by algorithm. It would be a tool for human reasoning, not machine execution.

## Why it hasn't been built, and why that's changing

Tools for humans that don't produce machine output are hard to justify. No demo, no "look it works."

But LLMs change the equation. They can read structured-but-not-rigorous notation and reason about it approximately — find gaps, ask "what happens when this command fires while this view is loading." Not formal verification like [TLA+](pipelines-and-seams.md), but useful reasoning. A specification language that doesn't need to be machine-checkable because an LLM meets you halfway.

This is a new category of tool: designed for human clarity, not algorithmic verification, with an LLM as approximate reasoning partner.

## Connection to logic programming

The notation would be Prolog-shaped in spirit: expressing relationships and constraints without specifying execution. "This command can only fire when this condition holds," "this view depends on this part of the model," "these two commands are mutually exclusive." Logical constraints applied to GUI architecture.
