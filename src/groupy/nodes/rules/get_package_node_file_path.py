from pathlib import Path


def get_package_node_file_path(source_root: Path, package_name: str) -> Path:
    return source_root / package_name / "package-node.groupy.yaml"
