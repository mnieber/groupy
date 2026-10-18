import typing as T

from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.located_node import LocatedNode
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.models.variable_node import VariableNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.utils.get_changed_fields import get_changed_fields


def sync_module_node(
    module_node: ModuleNode, source_module_node: ModuleNode
) -> T.List[T.Tuple[str, str]]:
    # Updates the structure of the module node so that it matches the source
    # module node. Returns the (location, description) pairs of the changes.
    changes = []
    module_node.line_count = source_module_node.line_count

    # Helper function nodes are top-level functions in the source. The helper
    # function nodes of a removed node take its place.
    source_function_names = [node.name for node in source_module_node.function_nodes]
    while True:
        removed = _find_removed_function(module_node, source_function_names)
        if removed is None:
            break
        changes.append(_describe_removal(removed.location, removed.node))
        index = removed.siblings.index(removed.node)
        removed.siblings[index : index + 1] = removed.node.helper_function_nodes

    function_names = [
        located_node.node.name
        for located_node in get_located_nodes(module_node)
        if isinstance(located_node.node, FunctionNode)
        and not isinstance(located_node.parent, ClassNode)
    ]
    for name in source_function_names:
        if name not in function_names:
            changes.append(_describe_addition(name))
            _insert_in_source_order(
                module_node.function_nodes,
                FunctionNode(name=name),
                source_function_names,
            )

    changes += _sync_classes(module_node, source_module_node)

    # Variables
    source_variable_names = [node.name for node in source_module_node.variable_nodes]
    for variable_node in list(module_node.variable_nodes):
        if variable_node.name not in source_variable_names:
            changes.append(_describe_removal(variable_node.name, variable_node))
            module_node.variable_nodes.remove(variable_node)
    variable_names = [node.name for node in module_node.variable_nodes]
    for name in source_variable_names:
        if name not in variable_names:
            changes.append(_describe_addition(name))
            _insert_in_source_order(
                module_node.variable_nodes,
                VariableNode(name=name),
                source_variable_names,
            )
    return changes


def _sync_classes(
    module_node: ModuleNode, source_module_node: ModuleNode
) -> T.List[T.Tuple[str, str]]:
    changes = []
    source_class_nodes = {node.name: node for node in source_module_node.class_nodes}
    for class_node in list(module_node.class_nodes):
        if class_node.name not in source_class_nodes:
            # The helper functions of the methods are top-level functions
            changes.append(_describe_removal(class_node.name, class_node))
            for method_node in class_node.method_nodes:
                module_node.function_nodes += method_node.helper_function_nodes
            module_node.class_nodes.remove(class_node)
            continue

        source_method_names = [
            node.name for node in source_class_nodes[class_node.name].method_nodes
        ]
        for method_node in list(class_node.method_nodes):
            if method_node.name not in source_method_names:
                changes.append(
                    _describe_removal(
                        f"{class_node.name}.{method_node.name}", method_node
                    )
                )
                module_node.function_nodes += method_node.helper_function_nodes
                class_node.method_nodes.remove(method_node)
        method_names = [node.name for node in class_node.method_nodes]
        for name in source_method_names:
            if name not in method_names:
                changes.append(_describe_addition(f"{class_node.name}.{name}"))
                _insert_in_source_order(
                    class_node.method_nodes,
                    FunctionNode(name=name),
                    source_method_names,
                )

    class_names = [node.name for node in module_node.class_nodes]
    source_class_names = list(source_class_nodes)
    for name in source_class_names:
        if name not in class_names:
            changes.append(_describe_addition(name))
            _insert_in_source_order(
                module_node.class_nodes, source_class_nodes[name], source_class_names
            )
    return changes


def _find_removed_function(
    module_node: ModuleNode, source_function_names: T.List[str]
) -> T.Optional[LocatedNode]:
    for located_node in get_located_nodes(module_node):
        is_function = isinstance(located_node.node, FunctionNode)
        is_method = isinstance(located_node.parent, ClassNode)
        if (
            is_function
            and not is_method
            and located_node.node.name not in source_function_names
        ):
            return located_node
    return None


def _describe_removal(location: str, node: T.Any) -> T.Tuple[str, str]:
    # The fields of the removed node hint at the analysis that may need to move
    changed_fields = get_changed_fields(node)
    if changed_fields:
        return (location, f"removed {location} (it had {', '.join(changed_fields)})")
    return (location, f"removed {location}")


def _describe_addition(location: str) -> T.Tuple[str, str]:
    return (location, f"added {location}")


def _insert_in_source_order(
    nodes: T.List[T.Any], new_node: T.Any, source_names: T.List[str]
) -> None:
    # The new node goes before the first node that follows it in the source
    following_names = source_names[source_names.index(new_node.name) + 1 :]
    for index, node in enumerate(nodes):
        if node.name in following_names:
            nodes.insert(index, new_node)
            return
    nodes.append(new_node)
