from pathlib import Path

from groupy.call_graph.rules.create_call_graph import create_call_graph
from groupy.utils.dataclass_to_dict import dataclass_to_dict
from groupy.utils.dump_yaml import dump_yaml


def build_call_graph(source_root: Path, call_graph_path: Path) -> None:
    call_graph = create_call_graph(source_root)
    call_graph_path.parent.mkdir(parents=True, exist_ok=True)
    call_graph_path.write_text(dump_yaml(dataclass_to_dict(call_graph)))
