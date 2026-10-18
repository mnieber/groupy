from groupy.call_graph.models.call_graph import CallGraph


def is_helper_candidate(call_graph: CallGraph, location: str) -> bool:
    # A function is a helper candidate when it has exactly one caller, which is a
    # function or method in the same module that calls it through a certain edge.
    # Dunder methods are called by Python.
    module_name, qualified_name = location.split(":", 1)
    name = qualified_name.split(".")[-1]
    if name.startswith("__") and name.endswith("__"):
        return False
    edges = [edge for edge in call_graph.edges if edge.callee == location]
    callers = {edge.caller for edge in edges}
    if len(callers) != 1:
        return False
    caller_module_name, caller_name = next(iter(callers)).split(":", 1)
    return (
        caller_module_name == module_name
        and caller_name != "@module"
        and all(edge.is_certain for edge in edges)
    )
