import typing as T

from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.renamings.models.scope_renamings import ScopeRenamings


def get_scope_renamings(module_node: ModuleNode) -> T.List[ScopeRenamings]:
    # The renamings of a scope are the renamings of its node, and the rename_to of
    # the nodes that are defined in the scope
    module_scope = ScopeRenamings(
        scope_location="@module", renamings=list(module_node.renamings.items())
    )
    class_scopes: T.Dict[str, ScopeRenamings] = {}
    function_scopes = []
    for located_node in get_located_nodes(module_node):
        node = located_node.node
        if isinstance(node, ClassNode):
            class_scopes[node.name] = ScopeRenamings(
                scope_location=node.name, renamings=list(node.renamings.items())
            )
    for located_node in get_located_nodes(module_node):
        node = located_node.node
        if located_node.location == "@module":
            continue
        if node.rename_to:
            # A method is defined in its class; other nodes are defined in the module
            if isinstance(located_node.parent, ClassNode):
                scope = class_scopes[located_node.parent.name]
            else:
                scope = module_scope
            scope.renamings.append((node.name, node.rename_to))
        if isinstance(node, FunctionNode) and node.renamings:
            function_scopes.append(
                ScopeRenamings(
                    scope_location=located_node.location,
                    renamings=list(node.renamings.items()),
                )
            )
    scopes = [module_scope, *class_scopes.values(), *function_scopes]
    return [scope for scope in scopes if scope.renamings]
