# shelf: contract for agents

## Read first

1. `kb/ACTIVE.md` before anything else: the current objective, track status and next step.
2. `kb/decisions/` before changing direction or the file format. Add a record there for any new decision.

## Where things live

- `shelf/cli.py`: argument parsing and exit codes (0 ok, 1 `ShelfError`, 2 usage)
- `shelf/commands/`: one module per subcommand, discovered automatically
- `shelf/models.py`: `Book` and `STATUSES`
- `shelf/store.py`: reading and writing the shelf file (the on-disk format)
- `tests/support.py`: `ShelfTestCase`, a temporary shelf plus a helper that runs the real CLI
- `scripts/stop_gate.py`: Stop hook that blocks the end of a turn while tests fail
- `.claude/settings.json`: wires the Stop hook
- `kb/`: project knowledge (active work, decisions)

## Commands

Run from the repository root. Use `python3` if `python` is not Python 3.

- Run the tool: `SHELF_PATH=/tmp/shelf-dev.json python3 -m shelf --help`
- Run the tests: `python3 -m unittest` (add `-v` for names)

Always set `SHELF_PATH` when trying the tool by hand, so you never touch the real `~/.shelf.json`.

## Rules for every change

- Standard library only. No new dependencies, in code or in tests.
- Keep it working on Python 3.10 (CI for 3.10 is not set up yet, see issue #8).
- A new command is a new module in `shelf/commands/` with `register(subparsers)`.
  Don't add it to a shared list or edit `cli.py` for it.
- Tests use a temporary `SHELF_PATH`: subclass `ShelfTestCase`, never point at a real file.
- Never break a user's shelf file. Every version of shelf must still read every file
  an older version wrote; a format change needs a version bump, a migration, and a test
  that loads a file in the old format.
- Fix the code, not the tests: don't skip, delete or weaken a test to get green.
- Report user errors as `ShelfError` (exit 1) or `parser.error` (exit 2), never a traceback.

## Done means

- `python3 -m unittest` passes.
- The Stop gate doesn't block.
- Every new behaviour has a test that fails when the change is reverted.
- `kb/ACTIVE.md` reflects the new state if the work moved a track.
