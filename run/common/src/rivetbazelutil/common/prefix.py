import contextlib
import hashlib
import subprocess
import sys
import threading

COLORS = [str(i) for i in range(31, 38)]


def _prefix(name, color):
    return f"[ \033[{color}m{name}\033[0m ] "


def _prepend(stream, output, prefix):
    for line in stream:
        output.write(prefix + line)


def _color(name):
    hash = hashlib.md5()
    hash.update(name.encode("utf-8"))
    digest = hash.digest()
    i = int.from_bytes(digest, byteorder="little")
    return COLORS[i % len(COLORS)]


@contextlib.contextmanager
def run_process(args, name, width, display_code=False, process_options={}):
    color = _color(name)
    prefix = _prefix(name.ljust(width), color)
    try:
        process = subprocess.Popen(
            args,
            bufsize=1,
            encoding="utf-8",
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            **process_options,
        )
    except OSError as e:
        print(_prefix + str(e), file=sys.stderr)
        raise e
    stdout_thread = threading.Thread(
        target=_prepend, args=(process.stdout, sys.stdout, prefix)
    )
    stdout_thread.start()
    stderr_thread = threading.Thread(
        target=_prepend, args=(process.stderr, sys.stderr, prefix)
    )
    stderr_thread.start()
    yield process
    code = process.wait()
    stdout_thread.join()
    stderr_thread.join()
    if display_code and code:
        print(prefix + f"Exit {code}", file=sys.stderr)
