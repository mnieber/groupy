from pathlib import Path


def get_glossary_path(source_root: Path) -> Path:
    return source_root / "glossary.groupy.yaml"
