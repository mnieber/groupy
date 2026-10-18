from pathlib import Path


def get_module_node_file_path(source_root: Path, module_name: str) -> Path:
    return source_root / f"{module_name}.groupy.yaml"
