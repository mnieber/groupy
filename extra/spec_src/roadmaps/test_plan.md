# Test plan

This plan lists the tests that we still need to write, in the order in which we want to write them. All tests follow
the workflow-test style (a workflow test per main scenario in `test_<feature>/`, impl tests for edge cases in
`test_<feature>_impl/`). Each test package has its own `conftest.py` and Env.

The "Exercises" lists name the code units that the tests import or run, as paths relative to `src/breaker/`.
Together they describe the code structure that the tests imply. Code units that only appear indirectly (e.g. a rule
that is only called by an action under test) are listed where they are first needed.

Feature packages:

- `sessions`: the session file, `breaker init`, commits, the stages (`Stages`) and the finished chunks.
- `nodes`: node files (create, load, save, find, sync) and edits of fields that every kind of node has.
- `functions`: edits and refactorings of function nodes and functions (helpers, steps, extract method).
- `concepts`: terminology fields of nodes and the glossary.
- `renamings`: proposing and applying renamings.
- `call_graph`: the call graph and its views.
- `claude_requests`: RFAs, RFRs, callbacks and incremental accumulation.
- `groups`: grouping and chunking.
- `restructure`: the module layout and the code restructure.
- `runtime`: the CLI entrypoint and `run_next_stage` (which dispatches `breaker next` to the stage actions).
- `utils`: generic helpers (e.g. git).

## Done

1. `breaker init` (MS-1): session file, branch, node files, clean working tree, existing session, namespace packages.
2. Node files.
3. `move_function_to_parent`.
4. Node file edits (batch 1, in `tests/node_edits_tests/`): finding edit locations, and setting the scalar, dict and
   list fields of nodes.
5. Call graph (batch 2, in `tests/call_graph_tests/`): building (also after the code has changed), the view for
   a chunk, and the query callbacks.
6. Groups and chunks (batch 3, in `tests/groups_tests/`): the `simple` and `package` grouping strategies, and
   splitting a group into chunks with per-group chunk ids.
7. `breaker next` and the stage runner (batch 4, in `tests/breaker_next_tests/` and `tests/sessions_tests/`): the
   config file, the group file in `breaker init`, the preconditions of `breaker next`, running a (fake) stage with
   commits per action, and resuming an interrupted stage.
8. Glossary (batch 5, in `tests/glossary_tests/`): loading and saving the glossary, and the glossary edits (also for
   names with several meanings).
9. `breaker sync` (batch 6, in `tests/breaker_sync_tests/`): updating the node files, the package node files and the
   group file after the source changed, the report of the changes, and keeping the helpers of a removed node.
10. `identify-helper-functions` (batch 7, in `tests/identify_helper_functions_tests/`): marking the helper
    candidates per chunk, nesting the helpers via callbacks, renaming them with rope (also the call sites in other
    modules), and the name clash error.

## Test infrastructure for Claude requests

1. Every request to Claude has a deterministic id that is derived from what it is about:
   1. RFA: `<stage-id>/<chunk-id>`, e.g. `identify-helper-functions/group-1/chunk-1`.
   2. Incremental accumulation: `<task>/batch-<n>`, e.g. `assign-groups/batch-2`.
   3. RFR: `<action>/<location>`, e.g. `extract_method/myapp/books.py:create_book`.
   4. The real policy uses the id for logging and as the key of finished chunks in the session file (for resuming
      an interrupted stage).
2. The tests use fake policies (in a `fake_policies.py` next to the tests). The config file of a test refers to a
   function in that module that returns the fake policy (e.g. `get_fake_rfa_policy`), and the test scripts the fake
   before it runs `breaker next`. A fake is only added once a test needs it.
   1. `FakeRfaPolicy` maps each RFA id onto a list of scripted callbacks (an action name plus its arguments). It runs
      these callbacks through the same callback dispatcher that the real policy uses.
   2. `FakeRfrPolicy` maps each RFR id onto scripted file edits.
   3. `FakeGroupingPolicy` (for smart grouping with Haiku) maps each batch id onto a scripted answer.
   4. Every fake records the requests that it receives (id, prompt and context), so that tests can assert on the
      context that Breaker pre-computed (e.g. the call-graph view).
   5. A request without a script raises an error, so that unexpected requests fail the test.
3. Tests use the `simple` grouping strategy with a large group and chunk size (set in the config file), so that the
   chunk ids are predictable, except in the tests of the grouping strategies themselves.
4. Exercises: `claude_requests/models/rfa.py`, `claude_requests/models/rfr.py`, `claude_requests/models/callback.py`,
   `claude_requests/actions/run_callback.py` (the dispatcher, with `UnknownCallbackError`),
   `claude_requests/policies/rfa_policy.py`, `claude_requests/policies/rfr_policy.py`,
   `groups/policies/grouping_policy.py` (the abstract policies that the fakes implement).
   - Implied: `claude_requests/policies/claude_rfa_policy.py`, `claude_requests/policies/claude_rfr_policy.py`,
     `groups/policies/claude_grouping_policy.py` (the real implementations, which the tests don't run).

## 9. The stages

One workflow test per stage, plus impl tests for its validations. Each workflow test runs `breaker next` with
scripted callbacks and checks the node files, the source, the commits and `next_stage`. Every stage is an action
that `runtime/actions/run_next_stage.py` calls.

Each stage runs its own loop over its chunks (the stages chunk different things, and some run an extra RFA after the
last chunk), using the shared helper `sessions/actions/process_chunks.py` that skips finished chunks and records them.

1. `analyze-terminology` (MS-3, in `tests/analyze_terminology_tests/`): the callbacks fill concepts, local terms,
   responsibilities, steps, aliases and `extract_method_priority`, and update the glossary; the RFA context contains
   the module sources, the call-graph view (callers and callees) and the glossary so far; a second chunk that uses a
   known name with another meaning adds a second entry with that name; the consolidation RFA (a final pseudo-chunk
   `analyze-terminology/consolidate-glossary`) merges two entries with the same meaning; a follow-up RFA
   (`<rfa-id>/retry-1`) for unanalyzed nodes, and `UnanalyzedNodesError` when nodes are still unanalyzed; resuming
   at the consolidation. Scripts use the generic `callback(name, **args)` helper of `breaker_next_test_env`.
   - Exercises: `concepts/actions/analyze_terminology.py` (the stage, with `UnanalyzedNodesError`),
     `concepts/actions/consolidate_glossary.py`, the RFA context keys `module_sources`, `call_graph_view`,
     `glossary` and `unanalyzed_nodes`, and the node edits (batch 1) and glossary edits (batch 5) as callbacks.
2. `propose-renamings` (MS-4): renamings are recorded; the RFA context contains the glossary; Breaker reports a new
   name that clashes with an existing name in the same scope.
   - Exercises: `renamings/actions/propose_renamings.py`, `renamings/rules/find_renaming_conflicts.py`.
3. `apply-renamings` (MS-5): `rename_symbol` (rope) renames local symbols, functions and module-level symbols,
   including their call sites in other modules.
   - Exercises: `renamings/actions/apply_renamings.py`, `renamings/actions/rename_symbol.py`.
4. `extract-methods` (MS-6): the extract-method RFR (via `FakeRfrPolicy`) changes the source; the action creates a
   node for the extracted function; the callbacks fill its analysis and update the parent.
   - Exercises: `functions/actions/extract_methods.py` (the stage), `functions/actions/extract_method.py` (the
     callback), `functions/rules/get_extract_method_candidates.py`.
5. `move-steps-to-caller` (MS-7): the RFA context contains the callers of F with their source; the scripted RFR
   moves the call.
   - Exercises: `functions/actions/move_steps_to_caller.py` (the stage), `functions/actions/move_step_to_caller.py`
     (the callback).
6. `propose-module-layout` and `propose-code-restructure` (MS-8): `proposed_modules` in the root package node file;
   the validations (missing `code_unit_type`, location rule per code unit type, one public code unit per file,
   dependency direction).
   - Exercises: `restructure/actions/propose_module_layout.py`, `nodes/actions/set_proposed_module.py`,
     `nodes/actions/remove_proposed_module.py`, `restructure/actions/propose_code_restructure.py`,
     `restructure/rules/validate_code_restructure.py`, `restructure/rules/get_expected_location.py`,
     `restructure/rules/find_dependency_violations.py`.

## 10. Smart grouping and the group file

These tests don't affect the stage runner. They can also move to just before the stages that need them (item 3
depends on actions that rename or split off files, which arrive with the later stages).

1. Smart grouping with `FakeGroupingPolicy`: the index file, the group description file and the group file;
   Breaker rejects renumbered, merged or deleted groups, discards malformed lines and retries unassigned node files.
   - Exercises: `groups/actions/create_index_file.py`, `groups/actions/create_smart_groups.py`,
     `groups/rules/load_group_file.py` (malformed lines), `groups/rules/validate_group_descriptions.py`.
2. Incremental accumulation as a generic mechanism: batches of K items, validation of the state file after each
   batch, unprocessed items are added to the next batch.
   - Exercises: `claude_requests/actions/run_incremental_accumulation.py`.
3. The group file is updated when an action renames a file or splits off a new file.
   - Exercises: `groups/actions/rename_file_in_group_file.py`, `groups/actions/add_file_to_group.py` (first needed
     by `breaker sync`).
4. `breaker group` recreates the group file with the grouping strategy and the sizes of the (changed) config file,
   and commits it.
   - Exercises: `runtime/entrypoints/breaker.py`, `groups/actions/create_group_file.py`.

## Open points in the design

1. MS-8 sets `next_stage` to `apply-code-restructure`, but there is no milestone for that stage yet.
