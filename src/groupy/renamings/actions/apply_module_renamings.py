import ast
from pathlib import Path

from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.renamings.policies.refactoring_policy import RefactoringPolicy
from groupy.renamings.rules.find_scope_def import find_scope_def
from groupy.renamings.rules.get_scope_renamings import get_scope_renamings
from groupy.renamings.rules.get_scope_symbols import get_scope_symbols
from groupy.renamings.rules.order_renamings import order_renamings
from groupy.renamings.utils.rename_keys import rename_keys
from groupy.utils.read_source import read_source


def apply_module_renamings(
    source_root: Path, module_name: str, refactoring_policy: RefactoringPolicy
) -> bool:
    # Applies the renamings of the module node file to the source and to the node
    # file. Returns whether the module had renamings.
    node_file_path = get_module_node_file_path(source_root, module_name)
    module_node = load_module_node(node_file_path)
    scopes = get_scope_renamings(module_node)
    if not scopes:
        return False

    # The symbols in a function are renamed before the function itself, and the
    # attributes and methods of a class before the class itself
    scopes.sort(key=lambda scope: _get_scope_rank(scope.scope_location, module_node))
    for scope in scopes:
        for name, new_name in order_renamings(scope.renamings):
            # A renaming of something that is not a symbol in the source (e.g. a
            # concept) only renames the keys in the node file
            tree = ast.parse(read_source(source_root / module_name))
            scope_def = find_scope_def(tree, scope.scope_location)
            if scope_def and name in get_scope_symbols(scope_def):
                refactoring_policy.rename_symbol(
                    source_root, module_name, scope.scope_location, name, new_name
                )

    _update_nodes(module_node)
    save_module_node(module_node, node_file_path)
    return True


def _get_scope_rank(scope_location: str, module_node) -> int:
    if scope_location == "@module":
        return 2
    class_names = [class_node.name for class_node in module_node.class_nodes]
    return 1 if scope_location in class_names else 0


def _update_nodes(module_node) -> None:
    # A renaming of a module-level symbol (or of a method in the renamings of its
    # class) also renames the node of that symbol
    for located_node in get_located_nodes(module_node):
        node = located_node.node
        if located_node.location == "@module":
            continue
        if isinstance(located_node.parent, ClassNode):
            scope_renamings = located_node.parent.renamings
        else:
            scope_renamings = module_node.renamings
        if node.name in scope_renamings:
            node.name = scope_renamings[node.name]

    module_node.concepts = rename_keys(module_node.concepts, module_node.renamings)
    module_node.renamings = {}
    for located_node in get_located_nodes(module_node):
        node = located_node.node
        if located_node.location == "@module":
            continue
        if node.rename_to:
            node.name = node.rename_to
            node.rename_to = None
        if isinstance(node, (FunctionNode, ClassNode)) and node.renamings:
            node.concepts = rename_keys(node.concepts, node.renamings)
            if isinstance(node, FunctionNode):
                node.local_terms = rename_keys(node.local_terms, node.renamings)
                node.abbreviations = rename_keys(node.abbreviations, node.renamings)
                # The aliases are gone
                node.aliases = {}
            node.renamings = {}
