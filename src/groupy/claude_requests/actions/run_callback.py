import typing as T

from groupy.call_graph.rules.get_callees import get_callees
from groupy.call_graph.rules.get_callers import get_callers
from groupy.call_graph.rules.load_call_graph import load_call_graph
from groupy.claude_requests.models.callback import Callback
from groupy.claude_requests.rules.create_rfr_policy import create_rfr_policy
from groupy.concepts.actions.add_alias import add_alias
from groupy.concepts.actions.add_glossary_alias import add_glossary_alias
from groupy.concepts.actions.add_glossary_entry import add_glossary_entry
from groupy.concepts.actions.merge_glossary_entries import merge_glossary_entries
from groupy.concepts.actions.remove_abbreviation import remove_abbreviation
from groupy.concepts.actions.remove_alias import remove_alias
from groupy.concepts.actions.remove_concept import remove_concept
from groupy.concepts.actions.remove_local_term import remove_local_term
from groupy.concepts.actions.set_abbreviation import set_abbreviation
from groupy.concepts.actions.set_concept import set_concept
from groupy.concepts.actions.set_glossary_abbreviation import set_glossary_abbreviation
from groupy.concepts.actions.set_glossary_description import set_glossary_description
from groupy.concepts.actions.set_local_term import set_local_term
from groupy.concepts.rules.get_glossary_path import get_glossary_path
from groupy.functions.actions.add_responsibility import add_responsibility
from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from groupy.functions.actions.commit_refactoring import commit_refactoring
from groupy.functions.actions.extract_method import extract_method
from groupy.functions.actions.move_function_to_parent import move_function_to_parent
from groupy.functions.actions.remove_responsibility import remove_responsibility
from groupy.functions.actions.remove_step import remove_step
from groupy.functions.actions.remove_step_to_move_to_caller import (
    remove_step_to_move_to_caller,
)
from groupy.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)
from groupy.functions.actions.update_responsibility import update_responsibility
from groupy.functions.actions.update_step import update_step
from groupy.functions.rules.get_source import get_source
from groupy.nodes.actions.set_code_unit_type import set_code_unit_type
from groupy.nodes.actions.set_move_to_file import set_move_to_file
from groupy.nodes.actions.set_rename_to import set_rename_to
from groupy.package_nodes.actions.remove_proposed_module import remove_proposed_module
from groupy.package_nodes.actions.set_proposed_module import set_proposed_module
from groupy.renamings.actions.remove_renaming import remove_renaming
from groupy.renamings.actions.set_renaming import set_renaming
from groupy.sessions.actions.commit_stage_changes import commit_stage_changes
from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config

# Edits of the node files (also the package node files), which take the source
# root as their first argument
NODE_EDITS = {
    action.__name__: action
    for action in (
        add_alias,
        add_responsibility,
        add_step,
        add_step_to_move_to_caller,
        move_function_to_parent,
        remove_abbreviation,
        remove_alias,
        remove_concept,
        remove_local_term,
        remove_proposed_module,
        remove_renaming,
        remove_responsibility,
        remove_step,
        remove_step_to_move_to_caller,
        set_abbreviation,
        set_code_unit_type,
        set_concept,
        set_extract_method_priority,
        set_local_term,
        set_move_to_file,
        set_proposed_module,
        set_rename_to,
        set_renaming,
        update_responsibility,
        update_step,
    )
}

# Edits of the glossary, which take the glossary path as their first argument
GLOSSARY_EDITS = {
    action.__name__: action
    for action in (
        add_glossary_alias,
        add_glossary_entry,
        merge_glossary_entries,
        set_glossary_abbreviation,
        set_glossary_description,
    )
}


def run_callback(callback: Callback, in_rfr: bool = False) -> T.Any:
    # In an RFR, the callbacks don't commit, because the source may be
    # half-refactored while they run
    name, args = callback.name, callback.args
    source_root = get_source_root()

    # Queries of the call graph and the source
    if name in ("get_callers", "get_callees"):
        call_graph = load_call_graph(get_groupy_path("call-graph.yaml"))
        query = get_callers if name == "get_callers" else get_callees
        return query(call_graph, **args)
    if name == "get_source":
        return get_source(source_root, **args)

    if name == "commit_refactoring":
        if not in_rfr:
            raise CallbackNotAllowedError(
                f"The callback {name} is only allowed in an RFR"
            )
        return commit_refactoring(**args)

    if name == "extract_method":
        # A callback that refactors the code makes an RFR, so it is not allowed in
        # an RFR
        if in_rfr:
            raise CallbackNotAllowedError(
                f"The callback {name} is not allowed in an RFR"
            )
        rfr_policy = create_rfr_policy(load_config(get_groupy_path("config.yaml")))
        run_edit = lambda: extract_method(  # noqa: E731
            source_root, **args, rfr_policy=rfr_policy
        )
    elif name in NODE_EDITS:
        run_edit = lambda: NODE_EDITS[name](source_root, **args)  # noqa: E731
    elif name in GLOSSARY_EDITS:
        run_edit = lambda: GLOSSARY_EDITS[name](  # noqa: E731
            get_glossary_path(source_root), **args
        )
    else:
        raise UnknownCallbackError(f"There is no callback {name}")

    if in_rfr:
        return run_edit()

    # A failed action is undone, so that the working tree matches the last commit
    try:
        result = run_edit()
    except Exception:
        restore_working_tree()
        raise
    commit_stage_changes(name)
    return result


class UnknownCallbackError(Exception):
    pass


class CallbackNotAllowedError(Exception):
    pass
