# Active work

State as of 2026-11-27, from `gh issue list` and `gh pr list`. Merged tracks are not listed.

## Current objective

Make shelf ready for book clubs (S7), starting with tags, without ever breaking a user's shelf file.

## Next step

Open the C2 issue (version the shelf file format), with acceptance criteria, and start it.
C2 goes before C1: see [D-0001](decisions/D-0001-storage-change-order.md).

## Active tracks

| Track | Issue | PR | State | Next gate |
| --- | --- | --- | --- | --- |
| C2: version the file format | none | none | Not started | Issue opened; PR adds the version field, migrates unversioned files, tests load an old file |
| C1: tags | none | none | Not started, waits for C2 ([D-0001](decisions/D-0001-storage-change-order.md)) | C2 merged; PR makes format version 3 with its own migration |
| CI on Python 3.10 | #8 | none | Issue open | PR whose workflow runs `python3 -m unittest` on 3.10 and passes |
| S4 | none | none | Not started | Issue opened with acceptance criteria |
| S5 | none | none | Not started | Issue opened with acceptance criteria |
| S7: book clubs | none | none | Objective, not started | C1 merged; issue opened |

## Blockers

- C1 is blocked until C2 is merged.
- S7 depends on C1 (tags).
- C1, C2, S4, S5 and S7 have no GitHub issues yet, so their scope lives only in these notes.
- Until #8 lands, nothing checks Python 3.10 compatibility automatically.

## Links

- Issues: https://github.com/arturochavez-monkeys/shelf/issues
- Pull requests: https://github.com/arturochavez-monkeys/shelf/pulls
- Decisions: [kb/decisions/](decisions/)
- Agent contract: [AGENTS.md](../AGENTS.md)
