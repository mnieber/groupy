import typing as T
from pathlib import Path

from groupy.call_graph.models.call_graph import CallGraph
from groupy.nodes.rules.get_module_names import get_module_names
from groupy.restructure.rules.get_proposed_code_units import get_proposed_code_units

# Dependencies point in one direction: entrypoints -> actions -> rules -> utils.
# Other code units (e.g. models) may be used by all, but only use utils.
_RANK_BY_CODE_UNIT_TYPE = {"entrypoint": 0, "action": 1, "rule": 2, "util": 3}
_LOWEST_RANK = 3


def find_dependency_violations(source_root: Path, call_graph: CallGraph) -> T.List[str]:
    # Returns a line per call that goes against the dependency direction, sorted
    code_units = get_proposed_code_units(source_root, get_module_names(source_root))
    type_by_location = {
        code_unit.source_location: code_unit.code_unit_type for code_unit in code_units
    }

    violations = set()
    for edge in call_graph.edges:
        caller_type = type_by_location.get(edge.caller)
        callee_type = type_by_location.get(edge.callee)
        if not edge.is_certain or caller_type is None:
            continue
        if callee_type not in _RANK_BY_CODE_UNIT_TYPE:
            continue
        caller_rank = _RANK_BY_CODE_UNIT_TYPE.get(caller_type, _LOWEST_RANK)
        if _RANK_BY_CODE_UNIT_TYPE[callee_type] < caller_rank:
            violations.add(
                f"{edge.caller} ({caller_type}) calls {edge.callee} ({callee_type})"
            )
    return sorted(violations)
