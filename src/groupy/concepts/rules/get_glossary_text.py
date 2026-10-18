from pathlib import Path


def get_glossary_text(glossary_path: Path) -> str:
    # A missing glossary is empty
    return glossary_path.read_text() if glossary_path.exists() else ""
