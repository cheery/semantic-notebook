# Python Async Programming

Asyncio is Python's built-in library for writing concurrent code using async/await syntax.

Key concepts:
- Event loop manages execution of coroutines
- `async def` creates a coroutine function
- `await` suspends execution until the awaited task completes
- `asyncio.gather()` runs multiple coroutines concurrently

Use cases: I/O-bound tasks like HTTP requests, database queries, file operations.
