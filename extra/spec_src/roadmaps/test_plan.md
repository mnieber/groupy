# Test plan

This plan lists the tests that we still need to write, in the order in which we want to write them. See `tests/README.md`
for the style of the tests and the fake policies.

The "Exercises" lists name the code units that the tests import or run, as paths relative to `src/groupy/`.
Together they describe the code structure that the tests imply. Code units that only appear indirectly (e.g. a rule
that is only called by an action under test) are listed where they are first needed.

Feature packages:

- `sessions`: the session file, `groupy init`, commits, the stages (`Stages`) and the finished chunks.
- `nodes`: node files (create, load, save, find, sync) and edits of fields that every kind of node has.
- `functions`: edits and refactorings of function nodes and functions (helpers, steps, extract method).
- `concepts`: terminology fields of nodes and the glossary.
- `renamings`: proposing and applying renamings.
- `call_graph`: the call graph and its views.
- `claude_requests`: RFAs, RFRs, callbacks and incremental accumulation.
- `groups`: grouping and chunking.
- `restructure`: the module layout and the code restructure.
- `runtime`: the CLI entrypoint and `run_next_stage` (which dispatches `groupy next` to the stage actions).
- `utils`: generic helpers (e.g. git).

## 10. Smart grouping and the group file

1. Smart grouping with `FakeGroupingPolicy` (which maps each batch id, e.g. `assign-groups/batch-2`, onto a scripted
   answer): the index file, the group description file and the group file;
   Groupy rejects renumbered, merged or deleted groups, discards malformed lines and retries unassigned node files.
   - Exercises: `groups/actions/create_index_file.py`, `groups/actions/create_smart_groups.py`,
     `groups/rules/load_group_file.py` (malformed lines), `groups/rules/validate_group_descriptions.py`.
2. Incremental accumulation as a generic mechanism: batches of K items, validation of the state file after each
   batch, unprocessed items are added to the next batch.
   - Exercises: `claude_requests/actions/run_incremental_accumulation.py`.
3. The group file is updated when an action renames a file or splits off a new file.
   - Exercises: `groups/actions/rename_file_in_group_file.py`, `groups/actions/add_file_to_group.py` (first needed
     by `groupy sync`).
4. `groupy group` recreates the group file with the grouping strategy and the sizes of the (changed) config file,
   and commits it.
   - Exercises: `runtime/entrypoints/groupy.py`, `groups/actions/create_group_file.py`.

## Open points in the design

1. Should `done` be followed by a new round (e.g. `groupy group` and `analyze-terminology` on the
   restructured code)?
