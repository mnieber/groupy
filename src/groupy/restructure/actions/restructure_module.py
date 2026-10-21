import ast
import typing as T
from pathlib import Path, PurePosixPath

from groupy.groups.actions.add_file_to_group import add_file_to_group
from groupy.groups.actions.remove_file_from_group import remove_file_from_group
from groupy.groups.actions.rename_file_in_group_file import rename_file_in_group_file
from groupy.nodes.actions.create_module_node_file import create_module_node_file
from groupy.nodes.actions.move_module_node_file import move_module_node_file
from groupy.nodes.actions.move_node_to_module import move_node_to_module
from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_module_names import get_module_names
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.get_target_module_names import get_target_module_names
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.package_nodes.actions.sync_package_node_files import sync_package_node_files
from groupy.renamings.policies.refactoring_policy import RefactoringPolicy
from groupy.renamings.rules.get_scope_symbols import get_scope_symbols
from groupy.restructure.actions.localize_import import localize_import
from groupy.restructure.actions.record_delegation import record_delegation
from groupy.restructure.rules.has_code import has_code
from groupy.utils.read_source import read_source


def restructure_module(
    source_root: Path,
    module_name: str,
    refactoring_policy: RefactoringPolicy,
    group_file_path: Path,
) -> bool:
    # Applies the proposed restructure of the module. Returns whether the module had
    # a proposal.
    module_node = load_module_node(get_module_node_file_path(source_root, module_name))
    module_names_before = set(get_module_names(source_root))
    changed = False

    # Rename the module, so that the code units that stay end up in their final file
    current_name = module_name
    if module_node.rename_to and module_node.rename_to != module_name:
        refactoring_policy.move_module(source_root, module_name, module_node.rename_to)
        move_module_node_file(source_root, module_name, module_node.rename_to)
        rename_file_in_group_file(group_file_path, module_name, module_node.rename_to)
        current_name = module_node.rename_to
        changed = True

    if _delegate_methods(source_root, current_name, refactoring_policy):
        changed = True
    if _move_nodes(source_root, current_name, refactoring_policy):
        changed = True

    if not changed:
        return False
    _add_new_modules(source_root, module_names_before, current_name, group_file_path)

    # A module without code is deleted, together with its node file
    if PurePosixPath(current_name).name != "__init__.py" and not has_code(
        source_root, current_name
    ):
        (source_root / current_name).unlink()
        get_module_node_file_path(source_root, current_name).unlink()
        remove_file_from_group(group_file_path, current_name)

    _refresh_line_counts(source_root)
    sync_package_node_files(source_root)
    return True


def _delegate_methods(
    source_root: Path, module_name: str, refactoring_policy: RefactoringPolicy
) -> bool:
    # A method with a move_to_file delegates to a new function in that file, which
    # takes the helper functions of the method with it
    module_node = load_module_node(get_module_node_file_path(source_root, module_name))
    delegations = [
        (class_node.name, method_node)
        for class_node in module_node.class_nodes
        for method_node in class_node.method_nodes
        if method_node.move_to_file
    ]
    for class_name, method_node in delegations:
        target_module_name = method_node.move_to_file
        function_name = _get_function_name(method_node)
        refactoring_policy.delegate_method(
            source_root, module_name, class_name, method_node.name, function_name
        )
        refactoring_policy.move_symbol(
            source_root, module_name, function_name, target_module_name
        )
        for helper_name in _get_helper_names(method_node):
            refactoring_policy.move_symbol(
                source_root, module_name, helper_name, target_module_name
            )
        localize_import(
            source_root,
            module_name,
            class_name,
            method_node.name,
            function_name,
            target_module_name,
        )
        record_delegation(
            source_root,
            module_name,
            f"{class_name}.{method_node.name}",
            function_name,
            target_module_name,
        )
    return bool(delegations)


def _get_function_name(method_node: FunctionNode) -> str:
    # The new function is named after its target file, or after the rename_to of the
    # method when the target is a util group file
    target_name = PurePosixPath(method_node.move_to_file).stem
    if method_node.rename_to and target_name != method_node.rename_to:
        if PurePosixPath(method_node.move_to_file).parent.name == "utils":
            return method_node.rename_to
    return target_name


def _get_helper_names(function_node: FunctionNode) -> T.List[str]:
    result = []
    for helper_function_node in function_node.helper_function_nodes:
        result.append(helper_function_node.name)
        result += _get_helper_names(helper_function_node)
    return result


def _move_nodes(
    source_root: Path, module_name: str, refactoring_policy: RefactoringPolicy
) -> bool:
    # The top-level nodes with a move_to_file are moved in source order. A function
    # moves with its helper functions, and a class with its methods.
    module_node = load_module_node(get_module_node_file_path(source_root, module_name))
    nodes = [
        *module_node.function_nodes,
        *module_node.class_nodes,
        *module_node.variable_nodes,
    ]
    source_names = list(
        get_scope_symbols(ast.parse(read_source(source_root / module_name)))
    )
    nodes_to_move = sorted(
        (node for node in nodes if node.move_to_file),
        key=lambda node: (
            source_names.index(node.name)
            if node.name in source_names
            else len(source_names)
        ),
    )
    for node in nodes_to_move:
        target_module_name = node.move_to_file
        refactoring_policy.move_symbol(
            source_root, module_name, node.name, target_module_name
        )
        if isinstance(node, FunctionNode):
            for helper_name in _get_helper_names(node):
                refactoring_policy.move_symbol(
                    source_root, module_name, helper_name, target_module_name
                )
        move_node_to_module(source_root, module_name, node.name, target_module_name)
    return bool(nodes_to_move)


def _add_new_modules(
    source_root: Path,
    module_names_before: T.Set[str],
    module_name: str,
    group_file_path: Path,
) -> None:
    # New modules (e.g. target modules and the __init__.py of new packages) get a
    # node file, and go into the group of the module that their code came from
    module_names = set(get_module_names(source_root))
    for target_module_name in get_target_module_names(source_root):
        if target_module_name not in module_names:
            create_module_node_file(source_root, target_module_name)
            module_names.add(target_module_name)
    for new_module_name in sorted(module_names - module_names_before):
        if new_module_name != module_name:
            add_file_to_group(group_file_path, new_module_name, module_name)


def _refresh_line_counts(source_root: Path) -> None:
    for module_name in get_module_names(source_root):
        node_file_path = get_module_node_file_path(source_root, module_name)
        module_node = load_module_node(node_file_path)
        line_count = len(read_source(source_root / module_name).splitlines())
        if module_node.line_count != line_count:
            module_node.line_count = line_count
            save_module_node(module_node, node_file_path)
