from pathlib import Path

from groupy.nodes.models.module_node import ModuleNode
from groupy.utils.dataclass_to_dict import dataclass_to_dict
from groupy.utils.dump_yaml import dump_yaml


def save_module_node(module_node: ModuleNode, node_file_path: Path) -> None:
    node_file_path.parent.mkdir(parents=True, exist_ok=True)
    node_file_path.write_text(
        dump_yaml({"module_node": dataclass_to_dict(module_node)})
    )
