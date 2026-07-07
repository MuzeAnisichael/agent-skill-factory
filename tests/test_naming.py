import unittest

from skill_factory.naming import normalize_skill_name


class NamingTests(unittest.TestCase):
    def test_normalizes_titles_to_skill_names(self) -> None:
        self.assertEqual(normalize_skill_name("Plan Mode!"), "plan-mode")
        self.assertEqual(normalize_skill_name("  GH Address Comments  "), "gh-address-comments")

    def test_rejects_empty_names(self) -> None:
        with self.assertRaises(ValueError):
            normalize_skill_name("!!!")


if __name__ == "__main__":
    unittest.main()
