# POSIX and Accidental Concurrency

The Unix filesystem is shared mutable global state with no coordination mechanism. This is not a bug — it's the reason Unix programmers could ship software at all.

## The tradeoff

POSIX gives you `open()`, `read()`, `write()`, `close()` — no concept of ownership, no obligation to coordinate. The filesystem is a bag of bytes any process can touch at any time. File locks are advisory. `inotify` is a Linux afterthought, not part of the programming model.

This permissiveness is a feature, not a defect. If every file access required declaring intent, acquiring a lock, coordinating with other processes, most software simply wouldn't have been built. The friction would have killed it. Zero-friction shared state is what allowed [pipelines](pipelines-and-seams.md) and standalone tools to compose into systems.

Unix solved the coordination problem once: the pipe. Data flows one direction, no mutation, no coordination. That's the clean part. But the filesystem as universal shared state has no such protection. The assumption baked into everything: one human, one process, one thing at a time.

## Why it worked for fifty years

Humans are slow. You don't open the same file in two editors by accident, and if you do, you notice. The human is the coordination mechanism. The OS doesn't need to help because you're the one doing the helping.

This pattern repeats everywhere:
- Git ignores locks, relies on humans to resolve conflicts after the fact
- Databases offer transactions but most web apps hope the race condition doesn't happen
- Webservers serve stale cached content and nobody notices because humans can't click fast enough

The pattern: tolerate inconsistency, compensate with human awareness.

## Why it's breaking now

LLMs can write to your files a hundred times per session. Background indexers scan directories every few seconds. Sync daemons pull remote changes while you edit locally. Automated agents next to interactive programs. All separate processes hitting the same shared state with no coordination.

Every program that touches the filesystem while an LLM might also be touching it has an accidental concurrency bug waiting to happen. Which is, increasingly, every program. See [concurrency in semantic notebook](concurrency-in-semantic-notebook.md) for a concrete example.

## No obvious solution

The two goals conflict: zero-friction access so people can build things easily, and coordination guarantees so things don't break with multiple actors. Every real system picks a point on that spectrum. Unix picked maximum permissiveness. That point is shifting.

Possible directions, none satisfying:
- A layer that watches for conflicting access and surfaces it (like `git status` for filesystem access)
- Ownership models where files have owner processes and others request access
- Mutation as events on a bus rather than direct writes
- The LLM itself as coordination mechanism — but that makes AI responsible for system correctness, which is not a foundation to build on

## Connection to the bigger picture

This connects to the [human vs machine](human-vs-machine-learning.md) question. The Unix programming model assumed serial human-scale access to shared resources. That assumption is no longer valid. The systems we've built on that assumption — which is most of them — have a latent concurrency problem that becomes visible as the ratio of automated agents to humans increases.
