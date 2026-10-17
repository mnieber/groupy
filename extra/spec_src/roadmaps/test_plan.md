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
11. `analyze-terminology` (batch 8, in `tests/analyze_terminology_tests/`): filling the analysis and the glossary
    via callbacks, the RFA context (module sources, call-graph view, glossary so far), a second meaning of a name,
    the consolidation RFA as a final pseudo-chunk, the follow-up RFA for unanalyzed nodes, and resuming at the
    consolidation.
12. `propose-renamings` (batch 9, in `tests/propose_renamings_tests/`): recording renamings via callbacks, the RFA
    context (module sources, glossary), the conflicts per scope (clashes, same new name, cycles; chains are
    allowed), the follow-up RFA for conflicts, and the error when conflicts remain.
13. `apply-renamings` (batch 10, in `tests/apply_renamings_tests/`): applying the renamings with the refactoring
    policy (rope), including call sites in other modules, updating the node files, ordering chains, renaming
    non-symbols in the node file only, rechecking conflicts, and resuming after a failed rename.
14. `extract-methods` (batch 11, in `tests/extract_methods_tests/`): the candidates, the `extract_method` callback
    with its RFR (`FakeRfrPolicy`), the node of the extracted function (renamed when nested), the follow-up RFA for
    unfinished candidates, and a failed RFR.

## Test infrastructure for Claude requests

1. Every request to Claude has a deterministic id that is derived from what it is about:
   1. RFA: `<stage-id>/<chunk-id>`, e.g. `identify-helper-functions/group-1/chunk-1`.
   2. Incremental accumulation: `<task>/batch-<n>`, e.g. `assign-groups/batch-2`.
   3. RFR made by a callback: `<action>/<location>/<name>`, e.g.
      `extract_method/myapp/books.py:create_book/_validate_title`. RFR made by a stage: `<stage-id>/<chunk-id>`, as
      for an RFA.
   4. The real policy uses the id for logging and as the key of finished chunks in the session file (for resuming
      an interrupted stage).
2. The tests use fake policies (in a `fake_policies.py` next to the tests). The config file of a test refers to a
   function in that module that returns the fake policy (e.g. `get_fake_rfa_policy`), and the test scripts the fake
   before it runs `breaker next`. A fake is only added once a test needs it.
   1. `FakeRfaPolicy` maps each RFA id onto a list of scripted callbacks (an action name plus its arguments). It runs
      these callbacks through the same callback dispatcher that the real policy uses.
   2. `FakeRfrPolicy` maps each RFR id onto a list of scripted steps: file writes (`file_write`, the new text of a
      module) and callbacks (run in RFR mode, so that they don't commit).
   3. `FakeGroupingPolicy` (for smart grouping with Haiku) maps each batch id onto a scripted answer.
   4. `FakeRefactoringPolicy` subclasses `RopeRefactoringPolicy`: it refactors with rope, records the renames and
      raises `FakeRefactoringError` for the renames that a test lets fail.
   5. Every fake records the requests that it receives (id, prompt and context), so that tests can assert on the
      context that Breaker pre-computed (e.g. the call-graph view).
   6. A request without a script raises an error, so that unexpected requests fail the test.
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

1. `propose-move-steps-to-caller` (MS-7, in `tests/propose_move_steps_to_caller_tests/`): an RFA per chunk with
   candidates (`move_step_candidates`, `module_sources`, `caller_sources`); the callbacks record the steps to move
   (`add_step_to_move_to_caller`) and the source is unchanged. The node edits of `steps_to_move_to_caller` (adding, withdrawing,
   following `update_step` and `remove_step`, and the validations) are tested in `tests/node_edits_tests/`.
   - Exercises: `functions/actions/propose_move_steps_to_caller.py` (the stage),
     `functions/rules/get_move_step_candidates.py`, `functions/actions/add_step_to_move_to_caller.py`,
     `functions/actions/remove_step_to_move.py`, the `steps_to_move_to_caller` field of `FunctionNode`, and the changes of
     `update_step` and `remove_step`.
2. `apply-move-steps-to-caller` (MS-7, in `tests/apply_move_steps_to_caller_tests/`): an RFR per chunk with steps
   to move (`steps_to_move_to_caller`, `module_sources`, `caller_sources`); the scripted RFR edits the source and the steps
   (via callbacks) and commits with `commit_refactoring`; a follow-up RFR for unapplied moves and
   `UnappliedStepMovesError`; uncommitted changes after the RFR, code that does not parse, and a refactoring
   callback in an RFR are rejected, and the working tree is restored.
   - Exercises: `functions/actions/apply_move_steps_to_caller.py` (the stage, with `UncommittedRefactoringError`
     and `UnappliedStepMovesError`), `functions/actions/commit_refactoring.py` (with
     `RefactoringDoesNotParseError`), `claude_requests/actions/run_callback.py` (`in_rfr`, with
     `CallbackNotAllowedError`).
3. `propose-module-layout` and `propose-code-restructure` (MS-8): `proposed_modules` in the root package node file;
   the validations (missing `code_unit_type`, location rule per code unit type, one public code unit per file,
   dependency direction).
   - Exercises: `restructure/actions/propose_module_layout.py`, `nodes/actions/set_proposed_module.py`,
     `nodes/actions/remove_proposed_module.py`, `restructure/actions/propose_code_restructure.py`,
     `restructure/rules/validate_code_restructure.py`, `restructure/rules/get_expected_location.py`,
     `restructure/rules/find_dependency_violations.py`.

## 10. Smart grouping and the group file

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
