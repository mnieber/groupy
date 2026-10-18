from pathlib import Path

import yaml

from groupy.package_nodes.models.package_node import PackageNode


def load_package_node(node_file_path: Path) -> PackageNode:
    data = yaml.safe_load(node_file_path.read_text())["package_node"] or {}
    return PackageNode(
        **{key: value for key, value in data.items() if value is not None}
    )
