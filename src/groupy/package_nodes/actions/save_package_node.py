from pathlib import Path

from groupy.package_nodes.models.package_node import PackageNode
from groupy.utils.dataclass_to_dict import dataclass_to_dict
from groupy.utils.dump_yaml import dump_yaml


def save_package_node(package_node: PackageNode, node_file_path: Path) -> None:
    node_file_path.parent.mkdir(parents=True, exist_ok=True)
    node_file_path.write_text(
        dump_yaml({"package_node": dataclass_to_dict(package_node)})
    )
