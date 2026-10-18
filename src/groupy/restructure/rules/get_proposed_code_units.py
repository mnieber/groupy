import typing as T
from pathlib import Path

from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.get_source_qualified_name import get_source_qualified_name
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.restructure.models.proposed_code_unit import ProposedCodeUnit


def get_proposed_code_units(
    source_root: Path, module_names: T.List[str]
) -> T.List[ProposedCodeUnit]:
    result = []
    for module_name in module_names:
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        module_target_file = module_node.rename_to or module_name
        info_by_node_id: T.Dict[int, T.Tuple[T.Optional[str], T.Optional[str]]] = {}

        for located_node in get_located_nodes(module_node):
            node = located_node.node
            if located_node.location == "@module":
                continue
            parent = located_node.parent
            if isinstance(parent, ClassNode):
                kind = "method"
            elif isinstance(parent, FunctionNode):
                kind = "helper"
            else:
                kind = "top-level"

            # The target file of a node is its move_to_file, or else the target file
            # of its parent (or of its module)
            is_delegating = kind == "method" and bool(node.move_to_file)
            if kind == "top-level":
                code_unit_type = node.code_unit_type
                target_file = node.move_to_file or module_target_file
            elif is_delegating:
                code_unit_type = node.code_unit_type
                target_file = node.move_to_file
            else:
                code_unit_type, target_file = info_by_node_id[id(parent)]
            info_by_node_id[id(node)] = (code_unit_type, target_file)

            result.append(
                ProposedCodeUnit(
                    module_name=module_name,
                    location=located_node.location,
                    source_location=(
                        f"{module_name}:{get_source_qualified_name(located_node)}"
                    ),
                    node=node,
                    kind=kind,
                    code_unit_type=code_unit_type,
                    target_file=target_file,
                    is_delegating=is_delegating,
                )
            )
    return result
