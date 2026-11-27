"""shelf stats"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from shelf.models import STATUSES, Book
from shelf.store import Store


def register(subparsers) -> None:
    parser = subparsers.add_parser("stats", help="show how your reading is going")
    parser.set_defaults(handler=run)


@dataclass
class Stats:
    counts: dict[str, int] = field(default_factory=lambda: dict.fromkeys(STATUSES, 0))
    finished_this_year: int = 0
    # Books whose status is not one of STATUSES, by status.
    unknown: Counter = field(default_factory=Counter)
    # Done books whose finished_at is missing or cannot be read.
    undated_done: int = 0


def parse_timestamp(value: object) -> datetime | None:
    """An ISO 8601 timestamp in UTC, or None if it cannot be read.

    Accepts a trailing ``Z``, which ``fromisoformat`` only understands from
    Python 3.11. A timestamp without an offset is taken to be UTC, the time
    zone shelf stores timestamps in.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text[-1:] in ("Z", "z"):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def summarize(books: list[Book], today: date | None = None) -> Stats:
    """Count the books by status and those finished in today's year (UTC)."""
    if today is None:
        today = datetime.now(timezone.utc).date()
    stats = Stats()
    for book in books:
        if book.status not in stats.counts:
            stats.unknown[book.status] += 1
            continue
        stats.counts[book.status] += 1
        if book.status != "done":
            continue
        finished = parse_timestamp(book.finished_at)
        if finished is None:
            stats.undated_done += 1
        elif finished.year == today.year:
            stats.finished_this_year += 1
    return stats


def plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def run(args: argparse.Namespace, store: Store) -> int:
    stats = summarize(store.load())
    for status in STATUSES:
        print(f"{status}: {stats.counts[status]}")
    print(f"finished this year: {stats.finished_this_year}")
    if stats.unknown:
        total = sum(stats.unknown.values())
        names = ", ".join(f"'{name}'" for name in sorted(map(str, stats.unknown)))
        print(
            f"warning: {plural(total, 'book')} not counted: unknown status {names}",
            file=sys.stderr,
        )
    if stats.undated_done:
        print(
            f"warning: {plural(stats.undated_done, 'done book')} not counted this year: "
            "missing or invalid finished_at",
            file=sys.stderr,
        )
    return 0
