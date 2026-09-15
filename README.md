# streamwrap

Text wrapping for input that doesn't fit in memory.

The standard library's `textwrap` module is fine, but it works on a
single string: to wrap a 4GB log file you'd have to read the whole
thing into memory first. `streamwrap` wraps an iterable of text
chunks instead, so the memory it uses is bounded by the line width,
not the input size.

## Usage

Wrapping a string you already have:

```python
from streamwrap import wrap

lines = wrap("this is a longer sentence than it needs to be", width=20)
for line in lines:
    print(line)
```

```
this is a longer
sentence than it
needs to be
```

Wrapping a file without loading it:

```python
from streamwrap import wrap_stream, iter_chunks_from_file

with open("huge_report.txt") as f:
    for line in wrap_stream(iter_chunks_from_file(f), width=80):
        print(line)
```

`iter_chunks_from_file` reads the file in fixed-size chunks (8KB by
default), and `wrap_stream` only ever holds the current line's words
in memory. Chunk size can be tuned for I/O, and it won't change the
wrapped output:

```python
iter_chunks_from_file(f, chunk_size=1 << 20)  # 1MB reads
```

`wrap_stream` also accepts any iterable of strings, so it works just
as well on chunks arriving from a socket or a subprocess pipe, not
just a file.

## Behavior

- Whitespace runs are collapsed, same as `str.split()` / `textwrap`.
- Words longer than `width` are broken to fit, unless you pass
  `break_long_words=False`, in which case they're left intact and
  will overflow the width.
- There's one case that can't be bounded by chunk size: a single
  "word" with no whitespace in it at all (a huge base64 blob on one
  line, say) has to be buffered whole before it can be wrapped, since
  there's nowhere earlier to break it.

## Status

Early skeleton. No hyphenation, no paragraph/indent handling, no CLI.
See the repo for what's planned next.

## License

MIT, see LICENSE.
