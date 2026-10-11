# Test plan

This plan lists the tests that we still need to write, in the order in which we want to write them. All tests follow
the workflow-test style (a workflow test per main scenario in `test_<feature>/`, impl tests for edge cases in
`test_<feature>_impl/`). Each test package has its own `conftest.py` and Env.

The "Exercises" lists name the code units that the tests import or run, as paths relative to `src/breaker/`.
Together they describe the code structure that the tests imply. Code units that only appear indirectly (e.g. a rule
that is only called by an action under test) are listed where they are first needed.

Feature packages:

- `sessions`: the session file, `breaker init`, commits.
- `nodes`: node files (create, load, save, find, sync) and edits of fields that every kind of node has.
- `functions`: edits and refactorings of function nodes and functions (helpers, steps, extract method).
- `concepts`: terminology fields of nodes and the glossary.
- `renamings`: proposing and applying renamings.
- `call_graph`: the call graph and its views.
- `claude_requests`: RFAs, RFRs, callbacks and incremental accumulation.
- `groups`: grouping and chunking.
- `stages`: `breaker next` and the stage runner.
- `restructure`: the module layout and the code restructure.
- `utils`: generic helpers (e.g. git).

## Done

1. `breaker init` (MS-1): session file, branch, node files, clean working tree, existing session, namespace packages.
   - Exercises: `runtime/entrypoints/breaker.py`, `sessions/actions/init_session.py` (with `DirtyWorkingTreeError` and
     `SessionExistsError`), `sessions/models/session.py` (`Session`, `get_session`, `reset_session`).
   - Implied: `sessions/actions/save_session.py`, `nodes/actions/create_node_files.py`, `nodes/rules/find_packages.py`,
     `utils/git_utils.py`.
2. Node files.
   - Exercises: `nodes/actions/create_module_node_file.py`, `nodes/actions/create_package_node_file.py`,
     `nodes/rules/load_module_node.py`, `nodes/actions/save_module_node.py`, `nodes/rules/load_package_node.py`,
     `nodes/models/module_node.py`, `nodes/models/package_node.py`.
   - Implied: `nodes/models/function_node.py`, `nodes/models/class_node.py`, `nodes/models/variable_node.py`,
     `nodes/actions/save_package_node.py`.
3. `move_function_to_parent`.
   - Exercises: `functions/actions/move_function_to_parent.py` (with `InvalidParentError`),
     `nodes/utils/exceptions.py` (`NodeNotFoundError`).
4. Node file edits (batch 1, in `tests/node_edits_tests/`): finding edit locations, and setting the scalar, dict and
   list fields of nodes.
   - Exercises: `nodes/rules/find_node.py`, `nodes/actions/set_rename_to.py`, `nodes/actions/set_move_to_file.py`,
     `nodes/actions/set_code_unit_type.py`, `functions/actions/set_extract_method_priority.py`,
     `functions/actions/add_responsibility.py`, `functions/actions/update_responsibility.py`,
     `functions/actions/remove_responsibility.py`, `functions/actions/add_step.py`, `functions/actions/update_step.py`,
     `functions/actions/remove_step.py`, `concepts/actions/set_concept.py`, `concepts/actions/remove_concept.py`,
     `concepts/actions/set_local_term.py`, `concepts/actions/remove_local_term.py`, `concepts/actions/add_alias.py`,
     `concepts/actions/remove_alias.py`, `concepts/actions/set_abbreviation.py`,
     `concepts/actions/remove_abbreviation.py`, `renamings/actions/set_renaming.py`,
     `renamings/actions/remove_renaming.py`.
   - Exercises: `nodes/utils/exceptions.py` (`NodeNotFoundError`, `AmbiguousLocationError`, `FieldNotSupportedError`,
     `InvalidValueError`, `InvalidIndexError`, `EntryNotFoundError`).

## Test infrastructure for Claude requests

1. Every request to Claude has a deterministic id that is derived from what it is about:
   1. RFA: `<stage-id>/<chunk-id>`, e.g. `identify-helper-functions/chunk-1`.
   2. Incremental accumulation: `<task>/batch-<n>`, e.g. `create-glossary/batch-2`.
   3. RFR: `<action>/<location>`, e.g. `extract_method/myapp/books.py:create_book`.
   4. The real policy uses the id for logging and as the key of finished chunks in the session file (for resuming
      an interrupted stage).
2. The tests use fake policies (in a `fake_policies.py` next to the tests):
   1. `FakeRfaPolicy` maps each RFA id onto a list of scripted callbacks (an action name plus its arguments). It runs
      these callbacks through the same callback dispatcher that the real policy uses.
   2. `FakeRfrPolicy` maps each RFR id onto scripted file edits.
   3. `FakeGroupingPolicy` (for smart grouping with Haiku) maps each batch id onto a scripted answer.
   4. Every fake records the requests that it receives (id, prompt and context), so that tests can assert on the
      context that Breaker pre-computed (e.g. the call-graph view).
   5. A request without a script raises an error, so that unexpected requests fail the test.
3. Tests use the `simple` grouping strategy with a large group size, so that the chunk ids are predictable, except
   in the tests of the grouping strategies themselves.
4. Exercises: `claude_requests/models/rfa.py`, `claude_requests/models/rfr.py`, `claude_requests/models/callback.py`,
   `claude_requests/actions/run_callback.py` (the dispatcher, with `UnknownCallbackError`),
   `claude_requests/policies/rfa_policy.py`, `claude_requests/policies/rfr_policy.py`,
   `groups/policies/grouping_policy.py` (the abstract policies that the fakes implement).
   - Implied: `claude_requests/policies/claude_rfa_policy.py`, `claude_requests/policies/claude_rfr_policy.py`,
     `groups/policies/claude_grouping_policy.py` (the real implementations, which the tests don't run).

## 2. Call graph

The tests write a few small modules, build the call graph, and assert on its edges and views.

1. Building: edges between functions and methods across modules, with the call location; nodes are named as
   `<file>:<qualified name>`; calls to methods of an unknown type are uncertain; test code is ignored.
   - Exercises: `call_graph/actions/build_call_graph.py` (writes `.breaker/call-graph.yaml`),
     `call_graph/rules/load_call_graph.py`, `call_graph/models/call_graph.py`, `call_graph/models/call_edge.py`.
2. Updating: after a module changes, only that module is re-analyzed, and the edges match a full rebuild.
   - Exercises: `call_graph/actions/update_call_graph.py`.
   - Implied: `call_graph/rules/find_calls_in_module.py`.
3. The view: callers and callees labelled as same module / other module in the chunk / outside the chunk; a one-line
   responsibility for functions outside the chunk; a summary when there are many callers.
   - Exercises: `call_graph/rules/get_call_graph_view.py`, `call_graph/models/call_graph_view.py`.
4. The query callbacks (read-only, so they are rules).
   - Exercises: `call_graph/rules/get_callers.py`, `call_graph/rules/get_callees.py`, `functions/rules/get_source.py`.

## 3. `breaker next` and the stage runner

The tests use the sessions Env (git repo) plus the fake policies.

1. `breaker next` runs the stage in `next_stage`, commits after each action with the stage id as the commit-message
   prefix, and updates `next_stage`.
   - Exercises: `runtime/entrypoints/breaker.py`, `stages/actions/run_next_stage.py`, `stages/enums.py` (`Stages`),
     `sessions/actions/commit_changes.py`.
2. An interrupted stage resumes at the first chunk that is not recorded as finished in the session file.
   - Exercises: `sessions/actions/record_finished_chunk.py`, `stages/rules/get_unfinished_chunks.py`.
3. `breaker next` refuses to run when the working tree is not clean (`DirtyWorkingTreeError`), or when there is no
   session (`NoSessionError`).
   - Exercises: `stages/actions/run_next_stage.py`, `sessions/utils/exceptions.py`.
   - Note: `DirtyWorkingTreeError` is then shared by `init_session` and `run_next_stage`, so it moves from
     `sessions/actions/init_session.py` to `sessions/utils/exceptions.py`.

## 4. Chunking

1. The `simple` and `package` grouping strategies: which node files end up in which group, and how a large group is
   split into chunks.
   - Exercises: `groups/rules/create_simple_groups.py`, `groups/rules/create_package_groups.py`,
     `groups/rules/split_group_into_chunks.py`, `groups/models/group.py`, `groups/models/chunk.py`,
     `groups/enums.py` (`GroupingStrategies`).
2. Smart grouping with `FakeGroupingPolicy`: the index file, the group description file and the group file;
   Breaker rejects renumbered, merged or deleted groups, discards malformed lines and retries unassigned node files.
   - Exercises: `groups/actions/create_index_file.py`, `groups/actions/create_smart_groups.py`,
     `groups/rules/load_group_file.py`, `groups/actions/save_group_file.py`,
     `groups/rules/validate_group_descriptions.py`.
3. Incremental accumulation as a generic mechanism: batches of K items, validation of the state file after each
   batch, unprocessed items are added to the next batch.
   - Exercises: `claude_requests/actions/run_incremental_accumulation.py`.
4. The group file is updated when an action renames a file or splits off a new file.
   - Exercises: `groups/actions/rename_file_in_group_file.py`, `groups/actions/add_file_to_group.py`.

## 5. The stages

One workflow test per stage, plus impl tests for its validations. Each workflow test runs `breaker next` with
scripted callbacks and checks the node files, the source, the commits and `next_stage`. Every stage is an action
that `stages/actions/run_next_stage.py` calls.

1. `identify-helper-functions` (MS-2): helper candidates are marked from the call graph; the scripted callbacks
   nest helpers with `move_function_to_parent`; Breaker renames the helpers to start with an underscore in the node
   file and in the source (including call sites).
   - Exercises: `functions/actions/identify_helper_functions.py`, `functions/actions/mark_helper_candidates.py`,
     `functions/actions/rename_helper_functions.py`, `renamings/actions/rename_symbol.py` (rope).
2. `analyze-terminology` (MS-3): the callbacks fill concepts, local terms, responsibilities, steps, aliases and
   `extract_method_priority`; the RFA context contains the module source and the call-graph view.
   - Exercises: `concepts/actions/analyze_terminology.py`, the actions of section 1.
3. `create-glossary` (MS-4): incremental accumulation with the glossary as state file; merging of synonyms into
   aliases; conflicts for one name with different meanings.
   - Exercises: `concepts/actions/create_glossary.py`, `concepts/rules/collect_terms.py`,
     `concepts/rules/load_glossary.py`, `concepts/actions/save_glossary.py`, `concepts/models/glossary.py`,
     `concepts/rules/validate_glossary_update.py`.
4. `propose-renamings` (MS-5): renamings are recorded; Breaker reports a new name that clashes with an existing
   name in the same scope.
   - Exercises: `renamings/actions/propose_renamings.py`, `renamings/rules/find_renaming_conflicts.py`.
5. `apply-renamings` (MS-6): `rename_symbol` (rope) renames local symbols, functions and module-level symbols,
   including their call sites in other modules.
   - Exercises: `renamings/actions/apply_renamings.py`, `renamings/actions/rename_symbol.py`.
6. `extract-methods` (MS-7): the extract-method RFR (via `FakeRfrPolicy`) changes the source; the action creates a
   node for the extracted function; the callbacks fill its analysis and update the parent.
   - Exercises: `functions/actions/extract_methods.py` (the stage), `functions/actions/extract_method.py` (the
     callback), `functions/rules/get_extract_method_candidates.py`.
7. `move-steps-to-caller` (MS-8): the RFA context contains the callers of F with their source; the scripted RFR
   moves the call.
   - Exercises: `functions/actions/move_steps_to_caller.py` (the stage), `functions/actions/move_step_to_caller.py`
     (the callback).
8. `propose-module-layout` and `propose-code-restructure` (MS-9): `proposed_modules` in the root package node file;
   the validations (missing `code_unit_type`, location rule per code unit type, one public code unit per file,
   dependency direction).
   - Exercises: `restructure/actions/propose_module_layout.py`, `nodes/actions/set_proposed_module.py`,
     `nodes/actions/remove_proposed_module.py`, `restructure/actions/propose_code_restructure.py`,
     `restructure/rules/validate_code_restructure.py`, `restructure/rules/get_expected_location.py`,
     `restructure/rules/find_dependency_violations.py`.

## 6. `breaker sync`

1. No differences after `breaker init`.
2. A function, class or variable that was added, removed or renamed in the source is reported.
3. A helper function that is nested in the node file but top-level in the source is not a difference.

- Exercises: `runtime/entrypoints/breaker.py`, `nodes/actions/sync_node_files.py`,
  `nodes/rules/find_node_file_differences.py`.

## Open points in the design

1. MS-9 sets `next_stage` to `apply-code-restructure`, but there is no milestone for that stage yet.
2. How the user resolves the differences that `breaker sync` reports (edit the node file by hand, or let Breaker
   update the node file?).
