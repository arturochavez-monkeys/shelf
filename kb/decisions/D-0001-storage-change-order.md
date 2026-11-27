---
id: D-0001
title: Version the shelf file format (C2) before adding tags (C1)
status: accepted
decided_on: 2026-11-27
---

# D-0001: Storage change order

## Context

C1 (tags) and C2 (file format versioning) both change what shelf writes to disk.
The code shows the current format has no room for that without breaking something:

- `tests/test_store.py:29` (`test_the_file_is_a_json_list_of_books`) pins the exact
  stored shape: the file is a JSON list (line 34) and each book has exactly the fields
  `id`, `title`, `author`, `status`, `added_at`, `finished_at` (line 36).
  C1 adds a field and C2 wraps or marks the list, so both issues must change this test.
- `shelf/store.py:41-42` reads the file as a bare list, and `shelf/models.py:35`
  builds each book with `cls(**data)`. A copy of shelf from before a format change
  cannot recognise a newer file: it fails with a traceback on any unknown field,
  and nothing in the file tells it which format it is looking at.

The objective is to reach book clubs (S7) through tags without ever breaking a user's
shelf file.

## Options considered

1. **C1 first.** Add `tags` to the unversioned list now and version later. The first
   real format change ships with no version to check, and versioning later has to
   guess which unversioned files have tags.
2. **C2 first, then C1.** Introduce an explicit format version before any real change.
   The current bare list becomes version 1, C2 writes version 2, and C1 becomes
   version 3 with its own migration.
3. **C1 and C2 in one change.** One PR, one edit to the pinned test, but two risky
   changes reviewed and reverted together.

## Decision

Option 2: C2 first, then C1. Version the file format before its first real change,
so an older copy of shelf can never misread a newer file.

## Consequences

- C1 is blocked until C2 is merged.
- The pinned-shape test in `tests/test_store.py` changes twice: once in C2, once in C1.
- Every format change from now on bumps the version and ships a migration from the
  previous version, with a test that loads a file written in the old format.
- Files written before C2 (version 1, a bare list) must keep loading forever.
- A shelf that meets a version newer than it knows must refuse with a clear
  `ShelfError` rather than guess.
