"""Line wrapping that works on an iterable of text chunks instead of a
single in-memory string, so a caller can wrap arbitrarily large input
(a multi-gigabyte log file, a network response body) while only ever
holding one word and one partial line in memory at a time.
"""

DEFAULT_CHUNK_SIZE = 8192


def iter_chunks_from_file(fileobj, chunk_size=DEFAULT_CHUNK_SIZE):
    """Yield fixed-size str chunks read from an open text-mode file object.

    This is the usual producer for wrap_stream: it never reads more than
    chunk_size characters ahead, so the file's total size doesn't matter.
    """
    while True:
        chunk = fileobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def iter_words(chunks):
    """Split an iterable of str chunks into whitespace-delimited words.

    Whitespace runs are collapsed the same way str.split() collapses them.
    A word that straddles a chunk boundary is stitched back together, so
    the caller can pick chunk_size for I/O efficiency without it affecting
    the result. The one thing this can't bound is a single "word" with no
    whitespace in it at all (e.g. a huge base64 blob on one line) - that
    still has to be held in memory whole before it can be yielded.
    """
    carry = ""
    for chunk in chunks:
        if not chunk:
            continue
        data = carry + chunk
        pieces = data.split()
        if not pieces:
            carry = ""
            continue
        if data[-1].isspace():
            carry = ""
        else:
            carry = pieces.pop()
        for word in pieces:
            yield word
    if carry:
        yield carry


def wrap_stream(chunks, width=70, break_long_words=True):
    """Wrap an iterable of text chunks into lines of at most `width`
    characters, yielded one at a time.

    Only the current line's words (and, if break_long_words is set, the
    remainder of the word being split) are held in memory - the input
    is never buffered in full. `chunks` may be a list of strings, a
    generator, or anything else str-iterable, e.g. iter_chunks_from_file().
    """
    if width < 1:
        raise ValueError("width must be at least 1")

    line_words = []
    line_len = 0

    for word in iter_words(chunks):
        while break_long_words and len(word) > width:
            if line_words:
                yield " ".join(line_words)
                line_words = []
                line_len = 0
            yield word[:width]
            word = word[width:]
        if not word:
            continue

        extra = len(word) + (1 if line_words else 0)
        if line_words and line_len + extra > width:
            yield " ".join(line_words)
            line_words = [word]
            line_len = len(word)
        else:
            line_words.append(word)
            line_len += extra

    if line_words:
        yield " ".join(line_words)


def wrap(text, width=70, break_long_words=True):
    """Wrap a single in-memory string into a list of lines.

    Convenience wrapper around wrap_stream for callers who already have
    the whole string and don't care about streaming.
    """
    return list(wrap_stream([text], width=width, break_long_words=break_long_words))
