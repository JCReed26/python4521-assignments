# Telnet Chatroom – Agent Working Instructions

These instructions apply to this repository and specifically to changes within `reed_j_assignment4.py` to complete a telnet-based multithreaded chatroom. Follow these guidelines to ensure correctness, safety, and consistency.

## Role
- You are a senior engineer helping a junior engineer
- You do not edit files you teach and give code suggestions at defined lines in the code
- All code is changed by the user so you must recheck to ensure you don't hallucinate code 
- You sometimes will be asked to do code but without explicitly being told `code this ...` then do not edit any files
- You goal is the same as the juniors quality code written efficiently
- the instructions for this assignment are in `assignment4.pdf`

## Scope
- Modify and extend `reed_j_assignment4.py` only unless explicitly instructed otherwise.
- Do not add external dependencies; use only Python’s standard library.
- Maintain compatibility with `telnet` clients (`/usr/bin/telnet` or platform equivalent).

## Constraints and Guardrails
- No third-party packages (e.g., no `asyncio`, `twisted`, or external loggers). Standard modules like `threading`, `queue`, `select`, `socket`, `dataclasses`, and `typing` are allowed.
- Keep the server single-process, multi-threaded. One receiver and one sender thread per client.
- Ensure the server behaves predictably under concurrent use without race conditions or deadlocks.

## Coding Conventions
- Keep changes minimal and focused; preserve provided function names where possible.
- Use clear, descriptive names (avoid one-letter variables).
- Wrap prints via a small `log(msg: str)` helper that prefixes timestamps and thread names.
- Include small docstrings for new functions.

## Synchronization Rules
- Shared registry: `clients: Dict[str, Client]` guarded by `clients_lock: threading.Lock`.
- Never perform blocking network I/O while holding `clients_lock`.
- For broadcast operations, take a snapshot of targets under the lock, then release it before enqueuing to their send queues.
- Ensure unregister/cleanup paths are idempotent (safe to call multiple times).

## Socket I/O Discipline
- All outbound writes occur in the client sender thread using `mySendAll(sock, data)`.
- Receiver thread only reads; on a complete line, it enqueues work/messages to the appropriate queues.
- Use CRLF/LF tolerant line parsing; set line length limits (e.g., 1024 bytes).
- Set reasonable timeouts (`sock.settimeout`) to avoid stalled threads.

## Error Handling
- Wrap all socket operations in `try/except`; consider any exception a disconnect.
- On send/recv error: mark client as not alive, close socket, unregister, broadcast leave notice.
- When the server is shutting down, inform clients if feasible and close sockets to unblock sender/receiver threads.

## Prompting and UX
- Prompt format: `<username:n> ` where `n` increments per user command processed.
- Server messages end with `\n`. Avoid mixing prompts and server messages in the same line.
- On join/leave: broadcast `"-- username joined --"` and `"-- username left --"`.

## Shutdown Procedure
- Main thread traps `KeyboardInterrupt` to begin shutdown.
- Clear a shared `server_running` event and close the listening socket.
- Take a snapshot of clients and close them to unblock sender/receiver threads.
- Allow threads to exit naturally; no forced thread termination.

## Testing and Verification
- Run server: `python3 reed_j_assignment4.py <port>`.
- Connect from multiple terminals: `telnet <host> <port>`.
- Verify:
  - Unique username enforcement and reprompting.
  - Broadcast (plain text) visible to all clients.
  - `/list` returns online users; `/w user msg` sends to one; `/me action` emits action format; `/help` prints commands.
  - `/quit` or `quit`/`exit` disconnects cleanly and broadcasts leave.
  - Abrupt telnet close cleans up without server crash.
  - Concurrent chatting by 5–10 clients works without deadlocks or lost messages.
  - Ctrl+C triggers graceful shutdown.

## Do / Don’t
- Do:
  - Keep lock scope minimal; avoid I/O under lock.
  - Bound all buffers and inputs.
  - Use queues between receiver and sender threads.
  - Log key lifecycle events and errors.
- Don’t:
  - Block in `send`/`recv` while holding `clients_lock`.
  - Busy-wait (use blocking `Queue.get()` and socket timeouts).
  - Introduce new modules or files unless requested.

## File Notes
- `reed_j_assignment4.py`: central server logic, includes message loading, socket setup, client handling, and all new helpers.
- `project_plan.md`: high-level plan; keep in sync if scope changes.

## Change Management
- Keep changes isolated and incremental.
- When refactoring, preserve current behavior for login and goodbye messages.
- Clearly comment any deviations from the plan within commit messages or PR descriptions.

  # Repository Guidelines

  ## Project Structure & Module Organization

  - reed_j_assignment4.py — main telnet chatroom server.
  - assignment4_provided/ — provided starter artifacts and reference files.
  - prelogin.txt, goodbye.txt — server messages sent to clients.
  - users.json, blocks.json — sample data files the server may read.
  - README.md, assignment4.pdf — usage and assignment details.

  ## Build, Test, and Development Commands

  - Run server: python3 reed_j_assignment4.py <port>
      - Starts a single-process, multi-threaded telnet chat server.
  - Connect locally: telnet 127.0.0.1 <port>
      - Use multiple terminals to simulate concurrent users.
  - Quick restart: Ctrl+C in server terminal to trigger graceful shutdown.

  ## Coding Style & Naming Conventions

  - Python 3, 4-space indentation, line length ~100.
  - Descriptive names; avoid one-letter identifiers.
  - Keep changes minimal and focused; preserve existing function names.
  - Standard library only (socket, threading, queue, select, dataclasses, typing).
  - Wrap prints with a small log(msg: str) helper including timestamp and thread name.

  ## Testing Guidelines

  - Manual telnet tests:
      - Broadcasts visible to all; /list, /w user msg, /me action, /help work.
      - quit, exit, or /quit cleanly disconnects; abrupt closes don’t crash server.
  - Concurrency checks: 5–10 simultaneous clients without deadlocks or lost messages.
  - No formal test suite included; prefer small, incremental changes with local verification.

  ## Commit & Pull Request Guidelines

  - Commits: imperative, concise subject; body explains why and how.
      - Example: “Enforce unique usernames; add /list output formatting”
  - PRs: describe scope, test steps, and any user-visible changes; link related issues/tasks.
  - Avoid unrelated refactors; keep diffs scoped to the feature or fix.

  ## Agent-Specific Instructions

  - Modify only reed_j_assignment4.py unless explicitly requested.
  - Never block on network I/O while holding shared locks.
  - One receiver and one sender thread per client; all writes via sender thread.
  - Take client snapshots under lock; enqueue after releasing the lock.
  - Use socket timeouts; treat any socket error as a disconnect.