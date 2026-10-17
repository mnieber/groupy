# Scenarios

This list guides the replacement of the implemented parts of `design.md` (including `chunking.md` and
`call-graph.md`) and of `test_plan.md` by scenario files. The parts that are not implemented yet stay in
`design.md`. Each scenario covers a main
workflow and the considerations that help a developer understand the design. Detailed rules and edge cases are
left to the test-suite (the workflow tests in `tests/<feature>_tests/test_<feature>/` and the impl tests in
`tests/<feature>_tests/test_<feature>_impl/`).

Each scenario becomes a directory `extra/spec_src/scenarios/<id>/` with a `scenario.py` (see
`instructions/examples/bookie/extra/spec_src/scenarios/`).

## Merging scenarios

Usually separation is good, but if you find out - in the process of writing - that combining two scenarios is helpful
then you can do so.

## The session and its mechanics

1. `s01_a_developer_starts_a_session` (written)
   The developer runs `groupy init`. Groupy creates a branch, the session file, the config file (if missing), a node
   file per module and package, and the group file, and commits them. The developer can review the node files and
   the group file before the first stage.

2. `s02_a_developer_runs_the_next_stage` (written)
   The developer runs `groupy next`. Groupy checks the preconditions (a session, a group file and a clean working
   tree), splits the groups into chunks, and makes an RFA per chunk. Claude answers with callbacks that run
   actions; Groupy commits after each action and after each chunk, and finally sets `next_stage`. Shows how the
   policies from the config file plug in, and why Groupy pre-computes context (e.g. the call graph view) instead of
   letting Claude derive it.

3. `s03_a_developer_resumes_an_interrupted_stage` (written)
   An action fails halfway through a stage. Groupy restores the working tree to the last commit and stops. The
   developer repairs the state and runs `groupy next` again; Groupy skips the finished chunks, and the stage derives
   its remaining work from the node files so that nothing is done twice.

4. `s04_claude_refactors_code_in_an_rfr` (written)
   A stage (or a callback) makes an RFR, in which Claude edits the source directly. Only node file edits, glossary
   edits and `commit_refactoring` are allowed as callbacks. `commit_refactoring` checks that the code parses and
   commits the source and node files together; uncommitted work after the RFR is rejected.

5. `s05_a_developer_syncs_the_node_files` (written)
   After editing the code by hand, the developer runs `groupy sync`. Groupy adds and removes nodes and node files so
   that they reflect the source again, updates the group file, and reports the changes (with hints for moving the
   analysis of renamed nodes). The developer reviews and commits the changes.

## The stages

6. `s06_groupy_identifies_helper_functions` (written)
   Per chunk, Groupy marks helper candidates from the call graph, Claude nests the actual helpers under their parent
   function in the node file, and Groupy renames the helpers to start with an underscore (in the source too, via
   the refactoring policy).

7. `s07_groupy_analyzes_the_terminology` (written)
   Per chunk, Claude fills in the concepts, local terms, responsibilities, steps, aliases and extract-method
   priority of each node, and adds the concepts to the project glossary. Groupy retries nodes that were not
   analyzed. After the last chunk, Claude consolidates the glossary; the developer then resolves names with several
   meanings.

8. `s08_groupy_proposes_renamings`
   Per chunk, Claude proposes renamings that replace aliases by canonical names from the glossary (and that shorten
   names with abbreviations). Groupy validates the renamings per scope (clashes, duplicate new names, cycles) and
   asks Claude once to fix conflicts.

9. `s09_groupy_applies_renamings`
   After the developer's review, Groupy rechecks the renamings and applies them per module with the refactoring
   policy (including call sites in other modules), ordering chains so that they work, and updates the node files.
   No Claude requests.

10. `s10_groupy_extracts_methods`
    Per chunk, Claude handles the high and medium priority candidates. Each `extract_method` callback makes an RFR
    that adds a new top-level function; Groupy verifies it, adds a node for it, and Claude updates the analysis
    (nesting the new function if it is a helper). Groupy retries unfinished candidates.

11. `s11_groupy_proposes_to_move_steps_to_the_caller`
    Per chunk, Claude proposes steps of a function that its callers should perform instead (using the callers'
    sources). The source does not change; the developer reviews the proposals.

12. `s12_groupy_moves_steps_to_the_caller`
    Per chunk, Groupy makes an RFR in which Claude moves the proposed steps to the callers, updates the analysis, and
    commits each move with `commit_refactoring` (or withdraws a proposal). Groupy retries unapplied moves.

13. `s13_groupy_proposes_the_module_layout`
    In a single RFA for the whole code-base, Claude receives condensed module summaries and the glossary, and
    proposes the feature packages of the application in the root package node file. The developer reviews them.

14. `s14_groupy_proposes_the_code_restructure`
    Per chunk, Claude assigns a code unit type and target file to every top-level node (and optionally lets methods
    delegate to new functions), following the target code structure (actions, rules, utils, models, ...). Groupy
    validates the proposal, asks Claude once to fix problems, and reports dependency violations.

15. `s15_groupy_restructures_the_code`
    After the developer's review, Groupy revalidates the proposal and applies it per module with the refactoring
    policy: it renames the module, lets methods delegate, moves the code units with their helpers, and deletes
    emptied modules. The node files, package node files and group file follow. No Claude requests. The developer
    fixes remaining circular imports and failing tests.

## Not implemented yet (these stay in `design.md`)

- `groupy group`, smart grouping and incremental accumulation (`chunking.md`).
- MS-10: `groupy sync` detects changed and renamed functions.
- MS-11: the developer restricts the refactoring to a part of the target code.
- The open points in `test_plan.md` (namespace packages, package/module name clashes, a new round after `done`).

## Reference material

Reference material goes into the scenario that really depends on understanding it. An earlier scenario that only
touches it gives a brief reference.

- The glossary of Groupy's own terms (RFA, RFR, chunk, node file, ...): briefly in s01 and s02, where the terms are
  first used.
- The config file fields: s01 (creating the config file) and s02 (the policies and the grouping settings).
- Groups and chunks (`chunking.md`): s02.
- The node file schema: s01 introduces the structural fields; each stage scenario explains the fields that it fills.
- The edit locations that callbacks use (`@module`, `Book.save`, ...): s02.
- How methods and nested functions are treated: s06 (helper functions are top-level functions in the source, and
  nested functions have no node), with a brief reference in s01.
- The call graph (`call-graph.md`), including uncertain edges for method calls: s06.
- The glossary file format: s07.
- The target code structure guidelines (code unit types, file locations, dependency direction) and methods that
  delegate: s14, with a brief reference in s15.
