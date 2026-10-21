import typing as T
from pathlib import Path, PurePosixPath

from groupy.nodes.rules.get_module_names import get_module_names
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.restructure.models.proposed_code_unit import ProposedCodeUnit
from groupy.restructure.rules.find_delegation_problem import find_delegation_problem
from groupy.restructure.rules.find_passive_proposals import find_passive_proposals
from groupy.restructure.rules.get_location_rule import get_location_rule
from groupy.restructure.rules.get_proposed_code_units import get_proposed_code_units

# The code units of which a target file may have only one
PUBLIC_CODE_UNIT_TYPES = ("action", "rule", "model", "entrypoint", "policy")


def validate_code_restructure(
    source_root: Path, module_names: T.List[str], passive_module_names: T.List[str]
) -> T.List[str]:
    # Validates the proposal of all node files, and returns the problems of the
    # nodes in the modules, as sorted lines <module>:<location>: <description>. A
    # proposal in a passive file is also a problem.
    all_module_names = get_module_names(source_root)
    code_units = get_proposed_code_units(source_root, all_module_names)
    problems = []
    for code_unit in code_units:
        if code_unit.module_name in module_names:
            for description in _find_problems(
                source_root, code_unit, code_units, module_names
            ):
                problems.append(
                    f"{code_unit.module_name}:{code_unit.location}: {description}"
                )
    problems.extend(find_passive_proposals(source_root, passive_module_names))
    return sorted(problems)


def _find_problems(
    source_root: Path,
    code_unit: ProposedCodeUnit,
    code_units: T.List[ProposedCodeUnit],
    module_names: T.List[str],
) -> T.List[str]:
    node = code_unit.node
    if code_unit.kind == "helper":
        return []
    if code_unit.kind == "method" and not code_unit.is_delegating:
        return []
    if code_unit.code_unit_type is None:
        return ["has no code_unit_type"]

    problems = []
    if code_unit.is_delegating:
        if code_unit.code_unit_type not in ("action", "rule", "util"):
            problems.append(
                f"a {code_unit.code_unit_type} cannot be the target of a delegating"
                " method"
            )
        class_name, method_name = code_unit.source_location.split(":")[1].split(".")
        delegation_problem = find_delegation_problem(
            source_root, code_unit.module_name, class_name, method_name
        )
        if delegation_problem:
            problems.append(delegation_problem)

    # The target file must match the location rule of the code unit type
    name = node.name
    location_rule = get_location_rule(code_unit.code_unit_type, name)
    if location_rule and not location_rule[0](PurePosixPath(code_unit.target_file)):
        problems.append(
            f"a {code_unit.code_unit_type} goes to {location_rule[1]}, not"
            f" {code_unit.target_file}"
        )

    # A target file receives one public code unit. A clash with a node of another
    # chunk is reported for the node of this chunk.
    if code_unit.code_unit_type in PUBLIC_CODE_UNIT_TYPES:
        index = code_units.index(code_unit)
        for other_index, other in enumerate(code_units):
            is_reported_here = (
                other_index < index or other.module_name not in module_names
            )
            if (
                other is not code_unit
                and is_reported_here
                and other.target_file == code_unit.target_file
                and other.code_unit_type in PUBLIC_CODE_UNIT_TYPES
                and other.kind != "helper"
                and (other.kind != "method" or other.is_delegating)
            ):
                problems.append(
                    f"{code_unit.target_file} already receives"
                    f" {other.module_name}:{other.location}"
                )
                break

    # Python cannot import a package and a module with the same name
    problems += _find_package_clashes(source_root, code_unit.target_file)
    return problems


def _find_package_clashes(source_root: Path, target_file: str) -> T.List[str]:
    problems = []
    module_names = get_module_names(source_root)
    for package_dir in PurePosixPath(target_file).parents:
        module_name = f"{package_dir}.py"
        if module_name not in module_names:
            continue
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        if module_node.rename_to in (None, module_name):
            problems.append(
                f"the target package {package_dir} clashes with the module"
                f" {module_name}"
            )
    return problems
