import io
import unittest

from streamwrap import iter_chunks_from_file, iter_words, wrap, wrap_stream

SAMPLE = (
    "The quick brown fox jumps over the lazy dog.  Pack my box with five "
    "dozen liquor jugs\nand then some extraordinarilylongwordthatneedsbreaking "
    "followed by short ones."
)


def split_every(text, size):
    return [text[i:i + size] for i in range(0, len(text), size)]


class IterWordsTests(unittest.TestCase):
    def test_word_split_across_chunks_is_rejoined(self):
        self.assertEqual(list(iter_words(["hel", "lo wor", "ld"])), ["hello", "world"])

    def test_chunk_ending_on_whitespace(self):
        self.assertEqual(list(iter_words(["hello ", "world"])), ["hello", "world"])

    def test_chunk_starting_with_whitespace(self):
        self.assertEqual(list(iter_words(["hello", " world"])), ["hello", "world"])

    def test_whitespace_only_chunk_separates_words(self):
        self.assertEqual(list(iter_words(["hello", " ", "world"])), ["hello", "world"])

    def test_newline_on_boundary_separates_words(self):
        self.assertEqual(list(iter_words(["hello\n", "world"])), ["hello", "world"])

    def test_empty_chunks_do_not_split_a_word(self):
        self.assertEqual(list(iter_words(["he", "", "llo"])), ["hello"])

    def test_trailing_word_is_flushed(self):
        self.assertEqual(list(iter_words(["abc"])), ["abc"])

    def test_no_input(self):
        self.assertEqual(list(iter_words([])), [])
        self.assertEqual(list(iter_words(["", "  \n "])), [])

    def test_any_chunk_size_matches_str_split(self):
        expected = SAMPLE.split()
        for size in range(1, len(SAMPLE) + 1):
            with self.subTest(size=size):
                self.assertEqual(list(iter_words(split_every(SAMPLE, size))), expected)


class WrapTests(unittest.TestCase):
    def test_readme_example(self):
        self.assertEqual(
            wrap("this is a longer sentence than it needs to be", width=20),
            ["this is a longer", "sentence than it", "needs to be"],
        )

    def test_empty_and_blank_input(self):
        self.assertEqual(wrap(""), [])
        self.assertEqual(wrap("  \n\t "), [])

    def test_word_exactly_width_fits(self):
        self.assertEqual(wrap("abcd ef", width=4), ["abcd", "ef"])

    def test_invalid_width(self):
        with self.assertRaises(ValueError):
            list(wrap_stream(["text"], width=0))


class LongWordTests(unittest.TestCase):
    def test_long_word_is_broken_at_width(self):
        self.assertEqual(wrap("abcdefghij", width=4), ["abcd", "efgh", "ij"])

    def test_length_that_is_a_multiple_of_width(self):
        self.assertEqual(wrap("abcdefgh", width=4), ["abcd", "efgh"])

    def test_pending_line_is_flushed_before_a_long_word(self):
        self.assertEqual(wrap("hi abcdefghij", width=4), ["hi", "abcd", "efgh", "ij"])

    def test_remainder_of_broken_word_starts_the_next_line(self):
        self.assertEqual(wrap("abcdef a", width=4), ["abcd", "ef a"])

    def test_remainder_too_long_to_share_a_line(self):
        self.assertEqual(wrap("abcdefghij ok", width=4), ["abcd", "efgh", "ij", "ok"])

    def test_long_word_left_intact_when_breaking_is_off(self):
        self.assertEqual(
            wrap("a abcdefghij b", width=4, break_long_words=False),
            ["a", "abcdefghij", "b"],
        )

    def test_long_word_split_across_chunks(self):
        chunks = ["abcd", "efgh", "ij kl"]
        self.assertEqual(
            list(wrap_stream(chunks, width=4)), ["abcd", "efgh", "ij", "kl"]
        )

    def test_lines_never_exceed_width_when_breaking(self):
        for width in (1, 2, 5, 11, 40):
            for size in (1, 3, 16):
                with self.subTest(width=width, size=size):
                    lines = list(wrap_stream(split_every(SAMPLE, size), width=width))
                    self.assertTrue(all(len(line) <= width for line in lines))
                    self.assertEqual("".join(lines), "".join(SAMPLE.split()))


class ChunkingInvarianceTests(unittest.TestCase):
    def test_output_does_not_depend_on_chunk_size(self):
        for break_long in (True, False):
            for width in (7, 20, 70):
                expected = wrap(SAMPLE, width=width, break_long_words=break_long)
                for size in (1, 2, 5, 13, 64):
                    with self.subTest(break_long=break_long, width=width, size=size):
                        got = list(
                            wrap_stream(
                                split_every(SAMPLE, size),
                                width=width,
                                break_long_words=break_long,
                            )
                        )
                        self.assertEqual(got, expected)

    def test_input_is_consumed_lazily(self):
        consumed = []

        def source():
            for chunk in ["aaa bbb ", "ccc ddd ", "eee fff ", "ggg hhh "]:
                consumed.append(chunk)
                yield chunk

        lines = wrap_stream(source(), width=7)
        self.assertEqual(next(lines), "aaa bbb")
        self.assertLess(len(consumed), 4)


class IterChunksFromFileTests(unittest.TestCase):
    def test_chunks_have_requested_size(self):
        chunks = list(iter_chunks_from_file(io.StringIO("abcdefg"), chunk_size=3))
        self.assertEqual(chunks, ["abc", "def", "g"])

    def test_empty_file(self):
        self.assertEqual(list(iter_chunks_from_file(io.StringIO(""))), [])

    def test_feeds_wrap_stream(self):
        f = io.StringIO(SAMPLE)
        got = list(wrap_stream(iter_chunks_from_file(f, chunk_size=4), width=20))
        self.assertEqual(got, wrap(SAMPLE, width=20))


if __name__ == "__main__":
    unittest.main()
