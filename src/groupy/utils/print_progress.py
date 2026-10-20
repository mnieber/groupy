import sys


def print_progress(message: str) -> None:
    # Progress messages go to stderr, so that they stay apart from the output
    print(message, file=sys.stderr, flush=True)
