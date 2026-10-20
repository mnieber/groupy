import subprocess
import typing as T


def try_run_git(*args: str) -> T.Optional[str]:
    # Returns None when git fails (e.g. for a revision that doesn't exist)
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.rstrip()
