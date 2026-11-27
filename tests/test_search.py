from tests.support import ShelfTestCase


class SearchCommandTest(ShelfTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.shelf("add", "Dune", "Frank Herbert")
        self.shelf("add", "One Hundred Years of Solitude", "Gabriel García Márquez")
        self.shelf("add", "Children of Dune", "Frank Herbert", "--status", "reading")

    def test_search_finds_a_title_match(self):
        result = self.shelf("search", "Solitude")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "#2 [to-read] One Hundred Years of Solitude by Gabriel García Márquez",
        ])

    def test_search_finds_an_author_match_in_list_order(self):
        result = self.shelf("search", "Herbert")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "#1 [to-read] Dune by Frank Herbert",
            "#3 [reading] Children of Dune by Frank Herbert",
        ])

    def test_search_ignores_case(self):
        result = self.shelf("search", "dUNE")

        self.assertEqual(result.stdout.splitlines(), [
            "#1 [to-read] Dune by Frank Herbert",
            "#3 [reading] Children of Dune by Frank Herbert",
        ])

    def test_search_ignores_case_of_accented_letters(self):
        result = self.shelf("search", "GARCÍA")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "#2 [to-read] One Hundred Years of Solitude by Gabriel García Márquez",
        ])

    def test_search_matches_decomposed_accents(self):
        # "i" followed by a combining acute accent, instead of the single "í".
        result = self.shelf("search", "garcía")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("García Márquez", result.stdout)

    def test_no_match_prints_a_message_and_succeeds(self):
        result = self.shelf("search", "Tolkien")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'No books match "Tolkien".\n')

    def test_search_without_text_is_a_usage_error(self):
        result = self.shelf("search")

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("usage: shelf search", result.stderr)

    def test_search_does_not_modify_the_shelf(self):
        before = self.shelf_path.read_bytes()

        self.shelf("search", "Dune")
        self.shelf("search", "Tolkien")

        self.assertEqual(self.shelf_path.read_bytes(), before)


class SearchEmptyShelfTest(ShelfTestCase):
    def test_an_empty_shelf_has_no_matches_and_is_not_created(self):
        result = self.shelf("search", "Dune")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'No books match "Dune".\n')
        self.assertFalse(self.shelf_path.exists())
