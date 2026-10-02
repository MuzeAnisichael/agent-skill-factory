import unittest

from skill_factory.frontmatter import parse_frontmatter, render_frontmatter


class FrontmatterTests(unittest.TestCase):
    def test_multiline_description_and_optional_metadata(self) -> None:
        parsed = parse_frontmatter(
            '---\nname: csv-review\ndescription: >-\n'
            '  检查实验数据: 缺失值和异常记录。\n  用于分析前的数据质量核查。\n'
            'metadata:\n  version: "1.0"\nlicense: MIT\n---\n\n# Review\n'
        )
        self.assertFalse(parsed.errors)
        self.assertIn("用于", parsed.string("description"))
        self.assertEqual(parsed.data["metadata"], {"version": "1.0"})
        self.assertEqual(parsed.body, "# Review")

    def test_indented_delimiter_in_literal_is_not_end_of_header(self) -> None:
        parsed = parse_frontmatter('---\nname: sample\ndescription: |\n  ---\n  when reading\n---\nBody')
        self.assertFalse(parsed.errors)
        self.assertEqual(parsed.string("description"), "---\nwhen reading\n")
        self.assertEqual(parsed.body, "Body")

    def test_duplicate_keys_report_original_line(self) -> None:
        for header in ('name: a\nname: b', 'metadata:\n  version: a\n  version: b'):
            with self.subTest(header=header):
                parsed = parse_frontmatter(f"---\n{header}\n---\nBody")
                self.assertIn("duplicate key", parsed.errors[0])
                self.assertIn("line", parsed.errors[0])
                self.assertEqual(parsed.body, "Body")

    def test_invalid_roots_keys_and_tags_are_rejected(self) -> None:
        for header in ('[a, b]', '1: value', 'name: !!python/object/apply:os.system [echo unsafe]',
                       'metadata: !!map wrong', ''):
            with self.subTest(header=header):
                self.assertTrue(parse_frontmatter(f"---\n{header}\n---\nBody").errors)

    def test_missing_delimiters(self) -> None:
        for text in ('Body only', '---\nname: sample'):
            self.assertTrue(parse_frontmatter(text).errors)

    def test_non_string_accessor_is_safe(self) -> None:
        parsed = parse_frontmatter('---\nname: 42\ndescription: [wrong]\n---\nBody')
        self.assertFalse(parsed.errors)
        self.assertEqual(parsed.string("name"), "")
        self.assertEqual(parsed.string("description"), "")

    def test_round_trip_unicode_quotes_colons_and_newlines(self) -> None:
        data = {"name": "sample", "description": '用于检查数据: "结果" # 不丢失\n第二行',
                "metadata": {"version": "1.0", "enabled": "true"}}
        parsed = parse_frontmatter(render_frontmatter(data, "# Instructions\n"))
        self.assertFalse(parsed.errors)
        self.assertEqual(parsed.data, data)

    def test_bom_and_crlf(self) -> None:
        parsed = parse_frontmatter('\ufeff---\r\nname: sample\r\ndescription: "When checking data"\r\n---\r\nBody')
        self.assertFalse(parsed.errors)
        self.assertEqual(parsed.string("name"), "sample")


if __name__ == "__main__":
    unittest.main()
