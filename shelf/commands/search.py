"""shelf search TEXT"""

from __future__ import annotations

import argparse
import unicodedata

from shelf.store import Store


def register(subparsers) -> None:
    parser = subparsers.add_parser("search", help="find books by title or author")
    parser.add_argument("text", help="text to look for in titles and authors (case-insensitive)")
    parser.set_defaults(handler=run)


def fold(text: str) -> str:
    """Normalize to NFC and casefold, so 'GARCÍA' matches 'García'.

    Accents are kept: 'garcia' does not match 'García'.
    """
    return unicodedata.normalize("NFC", text).casefold()


def run(args: argparse.Namespace, store: Store) -> int:
    wanted = fold(args.text)
    matches = [
        book for book in store.load()
        if wanted in fold(book.title) or wanted in fold(book.author)
    ]
    if not matches:
        print(f'No books match "{args.text}".')
        return 0
    for book in matches:
        print(book)
    return 0
