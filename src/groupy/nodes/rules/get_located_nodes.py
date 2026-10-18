import typing as T

from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.located_node import LocatedNode
from groupy.nodes.models.module_node import ModuleNode


def get_located_nodes(module_node: ModuleNode) -> T.List[LocatedNode]:
    # Each node is located by its qualified name, e.g. Book.save or
    # create_book._validate. The module node is located at @module.
    result = [LocatedNode(location="@module", node=module_node)]
    for function_node in module_node.function_nodes:
        result += _get_located_function_nodes(
            function_node, "", module_node.function_nodes, None
        )
    for class_node in module_node.class_nodes:
        result.append(
            LocatedNode(
                location=class_node.name,
                node=class_node,
                siblings=module_node.class_nodes,
            )
        )
        for method_node in class_node.method_nodes:
            result += _get_located_function_nodes(
                method_node, f"{class_node.name}.", class_node.method_nodes, class_node
            )
    for variable_node in module_node.variable_nodes:
        result.append(
            LocatedNode(
                location=variable_node.name,
                node=variable_node,
                siblings=module_node.variable_nodes,
            )
        )
    return result


def _get_located_function_nodes(
    function_node: FunctionNode,
    prefix: str,
    siblings: T.List[FunctionNode],
    parent: T.Any,
) -> T.List[LocatedNode]:
    location = prefix + function_node.name
    result = [
        LocatedNode(
            location=location, node=function_node, siblings=siblings, parent=parent
        )
    ]
    for helper_function_node in function_node.helper_function_nodes:
        result += _get_located_function_nodes(
            helper_function_node,
            f"{location}.",
            function_node.helper_function_nodes,
            function_node,
        )
    return result
