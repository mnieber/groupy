# Test plan: MS-11 (exclude)

This plan lists the tests for the `exclude` feature of the design doc, in the order in which we want to write them.
See `tests/README.md` for the style of the tests and the fake policies.

The "Exercises" lists name the code units that the tests import or run, as paths relative to `src/groupy/`.

In the examples, the target dir is `myapp`, with the active module `myapp/books.py` and the passive module
`myapp/reports/summary.py` (excluded with `myapp/reports/**`).

## 1. The exclude patterns and the active files

1. `groupy init --exclude=myapp/reports/** --exclude=myapp/legacy.py` writes both patterns to the session file. Without
   the option, `exclude` is `[]`. A pattern that matches no file is written as is.
   - Exercises: `runtime/entrypoints/groupy.py`, `sessions/actions/init_session.py`, `sessions/models/session.py`.
2. `groupy init` still creates node files for the passive modules, and the group file lists them (so that the chunk
   ids are the same with and without `exclude`). The same holds for `groupy sync` and `groupy group`.
3. The active module names: the union of the patterns in the config file and the session file; no patterns means
   every module is active; an edit of `exclude` in the session file takes effect at the next stage.
   - Exercises: `sessions/models/config.py`, `nodes/rules/get_active_module_names.py`.
4. Unit test of the glob matching: `myapp/*.py` matches `myapp/books.py` but not `myapp/reports/summary.py`;
   `myapp/reports/**` matches files at any depth below `myapp/reports`; `**/legacy.py` matches at any depth.
   - Exercises: `utils/matches_glob.py`.

## 2. The chunk filter

1. Unit-level impl tests of the chunk filter: a chunk whose files are all passive is dropped; a chunk with active and
   passive files keeps only its active files; the ids of the remaining chunks are unchanged; without patterns, the
   chunks are unchanged.
   - Exercises: `groups/rules/get_active_chunks.py`.
2. `groupy next` on a stage that works on chunks (e.g. identify-helper-functions) sends no request for a chunk whose
   files are all passive, and the RFA of a chunk with active and passive files only lists the active files.
3. `groupy status` does not list the chunks whose files are all passive as remaining.
   - Exercises: `sessions/rules/get_remaining_request_ids.py`.

## 3. The stages only start from the active files

1. identify-helper-functions: the helpers in passive files are not nested and not renamed; `caller_sources` in the
   RFA still includes a caller in a passive file.
   - Exercises: `functions/actions/identify_helper_functions.py`, `functions/actions/rename_helper_functions.py`.
2. analyze-terminology: the check for unanalyzed nodes ignores the passive nodes.
   - Exercises: `concepts/rules/find_unanalyzed_nodes.py`.
3. propose-module-layout: the request only receives the summaries of the active modules.
   - Exercises: `restructure/rules/get_module_summaries.py`.
4. extract-methods, propose-move-steps-to-caller and propose-code-restructure only take candidates from active files
   (e.g. a candidate in a passive callee of an active function is skipped).
   - Exercises: `functions/rules/find_extract_method_candidates.py`, `functions/rules/find_steps_to_move.py`.
5. The validation of the code restructure does not ask for a `code_unit_type` in a passive module.
   - Exercises: `restructure/rules/validate_code_restructure.py`.

## 4. Rejections and ripple effects

1. A renaming in a passive file is a conflict: propose-renamings retries it, and apply-renamings (after an edit by
   the developer) raises `ProposedRenamingHasConflictError` before anything changes.
   - Exercises: `renamings/rules/validate_renamings.py`.
2. A `move_to_file` or `code_unit_type` proposal in a passive module is a problem in propose-code-restructure (retried)
   and apply-code-restructure (raised).
3. apply-move-steps-to-caller raises `PassiveStepMovesError`, which lists the steps to move in passive files, before
   anything changes.
   - Exercises: `functions/actions/apply_move_steps_to_caller.py`.
4. Ripple effects: a renaming in `myapp/books.py` updates its call site and import in `myapp/reports/summary.py`; a
   step that moves to a caller in a passive file is applied by the RFR, which edits that caller and its node file.
