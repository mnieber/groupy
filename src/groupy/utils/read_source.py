from pathlib import Path


def read_source(path: Path) -> str:
    # Python source files may start with a BOM, which ast.parse rejects
    return path.read_text(encoding="utf-8-sig")
