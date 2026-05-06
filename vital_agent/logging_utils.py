from __future__ import annotations

import builtins
import sys


def safe_print(*args, **kwargs) -> None:
    sep = kwargs.pop("sep", " ")
    end = kwargs.pop("end", "\n")
    file = kwargs.pop("file", sys.stdout)
    flush = kwargs.pop("flush", False)

    text = sep.join(str(arg) for arg in args) + end

    try:
        file.write(text)
    except UnicodeEncodeError:
        encoding = getattr(file, "encoding", None) or "utf-8"
        fallback = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        file.write(fallback)

    if flush:
        file.flush()


print = safe_print
