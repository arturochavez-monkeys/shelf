import json
from datetime import date, datetime, timedelta, timezone
from unittest import mock

from shelf.commands.stats import summarize
from shelf.models import Book
from tests.support import ShelfTestCase

# A fixed "today" for the unit tests: they never read the real clock.
TODAY = date(2021, 6, 1)

# Fixed timestamps for the CLI tests. The year 2000 is never the current
# year, so "finished this year" is always 0 there, whatever day they run.
LONG_AGO = "2000-05-01T12:00:00+00:00"


def book(book_id, status, finished_at=None):
    return Book(
        id=book_id,
        title=f"Book {book_id}",
        author="Author",
        status=status,
        added_at=LONG_AGO,
        finished_at=finished_at,
    )


class SummarizeTest(ShelfTestCase):
    def test_counts_every_status_and_this_years_finished_books(self):
        stats = summarize([
            book(1, "to-read"),
            book(2, "to-read"),
            book(3, "reading"),
            book(4, "done", "2021-03-01T10:00:00+00:00"),
            book(5, "done", "2021-01-01T00:00:00+00:00"),
            book(6, "done", "2020-12-31T23:59:59+00:00"),
        ], today=TODAY)

        self.assertEqual(stats.counts, {"to-read": 2, "reading": 1, "done": 3})
        self.assertEqual(stats.finished_this_year, 2)

    def test_the_first_second_of_the_year_counts(self):
        stats = summarize([book(1, "done", "2021-01-01T00:00:00+00:00")], today=TODAY)

        self.assertEqual(stats.finished_this_year, 1)

    def test_the_last_second_of_last_year_does_not_count(self):
        stats = summarize([book(1, "done", "2020-12-31T23:59:59+00:00")], today=TODAY)

        self.assertEqual(stats.finished_this_year, 0)

    def test_the_last_second_of_this_year_counts(self):
        stats = summarize(
            [book(1, "done", "2021-12-31T23:59:59+00:00")], today=date(2021, 12, 31)
        )

        self.assertEqual(stats.finished_this_year, 1)

    def test_the_year_is_taken_in_utc(self):
        # 00:30 on 1 January at +01:00 is still 31 December in UTC.
        stats = summarize([book(1, "done", "2021-01-01T00:30:00+01:00")], today=TODAY)

        self.assertEqual(stats.finished_this_year, 0)

    def test_a_negative_offset_can_move_into_this_year(self):
        # 23:30 on 31 December at -01:00 is already 1 January in UTC.
        stats = summarize([book(1, "done", "2020-12-31T23:30:00-01:00")], today=TODAY)

        self.assertEqual(stats.finished_this_year, 1)

    def test_a_z_suffix_is_read_as_utc(self):
        stats = summarize([book(1, "done", "2021-03-01T00:00:00Z")], today=TODAY)

        self.assertEqual(stats.finished_this_year, 1)
        self.assertEqual(stats.undated_done, 0)

    def test_a_book_added_as_done_counts_by_its_finished_at(self):
        added_as_done = Book(
            id=1, title="Dune", author="Frank Herbert", status="done",
            added_at="2021-02-02T09:00:00+00:00", finished_at="2021-02-02T09:00:00+00:00",
        )

        stats = summarize([added_as_done], today=TODAY)

        self.assertEqual(stats.counts["done"], 1)
        self.assertEqual(stats.finished_this_year, 1)

    def test_unknown_statuses_are_not_counted_but_reported(self):
        stats = summarize([
            book(1, "paused"),
            book(2, "dropped"),
            book(3, "paused"),
            book(4, "reading"),
        ], today=TODAY)

        self.assertEqual(stats.counts, {"to-read": 0, "reading": 1, "done": 0})
        self.assertEqual(stats.unknown, {"paused": 2, "dropped": 1})

    def test_a_done_book_without_a_valid_finished_at_counts_as_done_only(self):
        stats = summarize([
            book(1, "done", None),
            book(2, "done", "not a date"),
            book(3, "done", 20210301),
            book(4, "done", "2021-03-01T00:00:00+00:00"),
        ], today=TODAY)

        self.assertEqual(stats.counts["done"], 4)
        self.assertEqual(stats.finished_this_year, 1)
        self.assertEqual(stats.undated_done, 3)

    def test_today_defaults_to_the_current_date(self):
        # Only checks that the default works; the counting is tested above
        # with a fixed date.
        stats = summarize([book(1, "done", LONG_AGO)])

        self.assertEqual(stats.counts["done"], 1)
        self.assertEqual(stats.finished_this_year, 0)

    def test_today_defaults_to_the_current_date_in_utc_not_local_time(self):
        # A clock in Mexico City (UTC-6) on 31 December 2025 at 23:30, when
        # it is already 1 January 2026 at 05:30 in UTC.
        moment = datetime(2025, 12, 31, 23, 30, tzinfo=timezone(timedelta(hours=-6)))

        class LocalClockDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return moment.replace(tzinfo=None)  # naive local time
                return moment.astimezone(tz)

        class LocalClockDate(date):
            @classmethod
            def today(cls):
                return moment.date()  # the local date

        books = [
            book(1, "done", "2026-01-01T02:00:00+00:00"),
            book(2, "done", "2026-01-01T04:00:00+00:00"),
            book(3, "done", "2025-06-01T12:00:00+00:00"),
        ]
        with mock.patch("shelf.commands.stats.datetime", LocalClockDatetime), \
                mock.patch("shelf.commands.stats.date", LocalClockDate):
            stats = summarize(books)

        # In UTC the year is 2026, so books 1 and 2 count. Taking the local
        # date (2025) would count only book 3, and the result would be 1.
        self.assertEqual(stats.finished_this_year, 2)


class StatsCommandTest(ShelfTestCase):
    def write_shelf(self, books):
        self.shelf_path.write_text(
            json.dumps([b.to_dict() for b in books], indent=2) + "\n", encoding="utf-8"
        )

    def test_stats_prints_the_four_lines_in_order(self):
        self.write_shelf([
            book(1, "to-read"),
            book(2, "to-read"),
            book(3, "reading"),
            book(4, "done", LONG_AGO),
            book(5, "done", LONG_AGO),
            book(6, "done", LONG_AGO),
        ])

        result = self.shelf("stats")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, (
            "to-read: 2\n"
            "reading: 1\n"
            "done: 3\n"
            "finished this year: 0\n"
        ))
        self.assertEqual(result.stderr, "")

    def test_an_empty_shelf_prints_zeros_and_is_not_created(self):
        result = self.shelf("stats")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, (
            "to-read: 0\n"
            "reading: 0\n"
            "done: 0\n"
            "finished this year: 0\n"
        ))
        self.assertEqual(result.stderr, "")
        self.assertFalse(self.shelf_path.exists())

    def test_stats_does_not_modify_the_shelf(self):
        self.write_shelf([
            book(1, "reading"),
            book(2, "done", LONG_AGO),
            book(3, "paused"),
            book(4, "done", None),
        ])
        before = self.shelf_path.read_bytes()

        self.shelf("stats")

        self.assertEqual(self.shelf_path.read_bytes(), before)

    def test_unknown_statuses_are_left_out_with_a_warning(self):
        self.write_shelf([
            book(1, "reading"),
            book(2, "paused"),
            book(3, "dropped"),
            book(4, "paused"),
        ])

        result = self.shelf("stats")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, (
            "to-read: 0\n"
            "reading: 1\n"
            "done: 0\n"
            "finished this year: 0\n"
        ))
        self.assertEqual(
            result.stderr,
            "warning: 3 books not counted: unknown status 'dropped', 'paused'\n",
        )

    def test_one_unknown_status_uses_the_singular(self):
        self.write_shelf([book(1, "paused")])

        result = self.shelf("stats")

        self.assertEqual(
            result.stderr, "warning: 1 book not counted: unknown status 'paused'\n"
        )

    def test_a_done_book_without_a_valid_finished_at_is_warned_about(self):
        self.write_shelf([
            book(1, "done", None),
            book(2, "done", "yesterday"),
            book(3, "done", LONG_AGO),
        ])

        result = self.shelf("stats")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, (
            "to-read: 0\n"
            "reading: 0\n"
            "done: 3\n"
            "finished this year: 0\n"
        ))
        self.assertEqual(
            result.stderr,
            "warning: 2 done books not counted this year: missing or invalid finished_at\n",
        )
