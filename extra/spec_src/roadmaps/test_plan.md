# Test plan

This plan lists the tests that we still need to write, in the order in which we want to write them. All tests follow
the workflow-test style (a workflow test per main scenario in `test_<feature>/`, impl tests for edge cases in
`test_<feature>_impl/`). Each test package has its own `conftest.py` and Env.

## Done

1. `breaker init` (MS-1): session file, branch, node files, clean working tree, existing session, namespace packages.
2. `create_module_node_file`, `create_package_node_file`, `load_module_node` and `save_module_node`.
3. `move_function_to_parent`.

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

## 1. Node file edits

These are plain edits of a module node file (like `move_function_to_parent`). The tests create a node file from
a small module, run the action, reload the node file, and check that the module itself is unchanged.

1. `find_node` (rule): resolves an edit location (`@module`, `create_book`, `create_book._validate`,
   `Book.add_chapter`) and raises `NodeNotFoundError` for an unknown location.
2. Actions that set the analysis fields of a node, used in the analysis stages:
   1. scalar fields (`rename_to`, `move_to_file`, `code_unit_type`, `extract_method_priority`), with validation of the
      allowed values.
   2. dict fields (`concepts`, `local_terms`, `renamings`, `aliases`, `abbreviations`): add, change and remove an entry.
   3. list fields (`responsibilities`, `steps`): add, change (by index) and remove an item; an invalid index raises.
3. Open question: one generic action per field kind (e.g. `set_dict_entry(location, field, key, value)`) or one action
   per field (e.g. `set_concept(location, name, description)`)? Per field gives Claude a clearer tool list; generic
   needs fewer tests.

## 2. Call graph

The tests write a few small modules, build the call graph, and assert on its edges and views.

1. `build_call_graph`: edges between functions and methods across modules, with the call location; nodes are named
   as `<file>:<qualified name>`; calls to methods of an unknown type are uncertain; test code is ignored.
2. `update_call_graph`: after a module changes, only that module is re-analyzed, and the edges match a full rebuild.
3. `get_call_graph_view`: callers and callees labelled as same module / other module in the chunk / outside the
   chunk; a one-line responsibility for functions outside the chunk; a summary when there are many callers.
4. The query actions `get_callers`, `get_callees` and `get_source`.

## 3. `breaker next` and the stage runner

The tests use the sessions Env (git repo) plus the fake policies.

1. `breaker next` runs the stage in `next_stage`, commits after each action with the stage id as the commit-message
   prefix, and updates `next_stage`.
2. An interrupted stage resumes at the first chunk that is not recorded as finished in the session file.
3. `breaker next` refuses to run when the working tree is not clean, or when there is no session.

## 4. Chunking

1. The `simple` and `package` grouping strategies: which node files end up in which group, and how a large group is
   split into chunks.
2. Smart grouping with `FakeGroupingPolicy`: the index file, the group description file and the group file;
   Breaker rejects renumbered, merged or deleted groups, discards malformed lines and retries unassigned node files.
3. Incremental accumulation as a generic mechanism: batches of K items, validation of the state file after each
   batch, unprocessed items are added to the next batch.
4. The group file is updated when an action renames a file or splits off a new file.

## 5. The stages

One workflow test per stage, plus impl tests for its validations. Each workflow test runs `breaker next` with
scripted callbacks and checks the node files, the source, the commits and `next_stage`.

1. `identify-helper-functions` (MS-2): helper candidates are marked from the call graph; the scripted callbacks
   nest helpers with `move_function_to_parent`; Breaker renames the helpers to start with an underscore in the node
   file and in the source (including call sites).
2. `analyze-terminology` (MS-3): the callbacks fill concepts, local terms, responsibilities, steps, aliases and
   `extract_method_priority`; the RFA context contains the module source and the call-graph view.
3. `create-glossary` (MS-4): incremental accumulation with the glossary as state file; merging of synonyms into
   aliases; conflicts for one name with different meanings.
4. `propose-renamings` (MS-5): renamings are recorded; Breaker reports a new name that clashes with an existing
   name in the same scope.
5. `apply-renamings` (MS-6): `rename_symbol` (rope) renames local symbols, functions and module-level symbols,
   including their call sites in other modules.
6. `extract-methods` (MS-7): the extract-method RFR (via `FakeRfrPolicy`) changes the source; the action creates a
   node for the extracted function; the callbacks fill its analysis and update the parent.
7. `move-steps-to-caller` (MS-8): the RFA context contains the callers of F with their source; the scripted RFR
   moves the call.
8. `propose-module-layout` and `propose-code-restructure` (MS-9): `proposed_modules` in the root package node file;
   the validations (missing `code_unit_type`, location rule per code unit type, one public code unit per file,
   dependency direction).

## 6. `breaker sync`

1. No differences after `breaker init`.
2. A function, class or variable that was added, removed or renamed in the source is reported.
3. A helper function that is nested in the node file but top-level in the source is not a difference.

## Open points in the design

1. MS-9 sets `next_stage` to `apply-code-restructure`, but there is no milestone for that stage yet.
2. How the user resolves the differences that `breaker sync` reports (edit the node file by hand, or let Breaker
   update the node file?).
