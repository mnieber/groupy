## Smart grouping

1. Groupy creates an index file (`.groupy/index.yaml`) from the node files.
   1. Per node file, it contains the line count, the package, the module name, the modules that it imports
      (within the target code) and the list of function-names for that module.
   2. The index file does not involve Claude, so Groupy can rebuild it cheaply at any time.
2. Groupy asks Claude Haiku to assign each node file to a group.
   1. The node files within a group are semantically related (e.g. they cover the same feature area).
   2. The assignment uses incremental accumulation (see above), in batches of K node files,
      with the group description file as the state file.
      1. Groupy sorts the node files by path, so that related files tend to end up in the same batch.
      2. For each batch, Haiku receives the group description file (`.groupy/group-descriptions.md`) and an index
         file that only contains the K node files of the batch.
      3. Haiku returns the group numbers for these K node files and the updated group description file.
   3. The group description file contains one line per group, with the group number and a one-line description.
      1. Haiku may add new groups or refine the description of an existing group (when the new files clearly
         widen the topic of the group).
      2. Haiku may not renumber, merge or delete groups. Groupy checks this after each batch.
   4. The group numbers are stored in the group file (`.groupy/groups.txt`), where every line contains a node file
      path and a group number.
      1. Groupy discards malformed lines, and lines that assign a node file to more than one group.
      2. Node files that did not get a group number are added to the next batch.
      3. If node files are still unassigned after the last batch, Groupy asks the user to assign them.
3. Groups may grow arbitrarily large.
   1. A group is a semantic unit. A chunk is a unit of work.
   2. Groupy splits a large group into several chunks (e.g. by subpackage, then by sorted path).
   3. If a group turns out to be a catch-all (e.g. "misc utilities") then we may later decide to re-run the
      incremental assignment for the files of that group.
4. Groupy keeps the group file up-to-date.
   1. When an action renames a file, it also renames it in the group file.
   2. When an action splits off code into a new file, the new file goes into the same group as the original file.
   3. `groupy sync` adds a new module to the group of a module in the same dir (or else to a new group), and
      removes a deleted module from its group.
   4. For stages where we know that the structure may have changed a lot (e.g. after the code restructure),
      `groupy next` first recreates the group file. It only does this at the start of a stage, and not when it
      resumes an interrupted stage, so that the finished chunks in the session file stay valid.
5. An RFA refers to the group file.
   1. Each chunk is a fresh Claude session that receives the group description and the pre-computed context.
   2. Chunks are usually not independent. How work is handed over from one chunk to the next (e.g. via a
      summary that is passed to the next chunk) is defined per RFA.
   3. Groupy records each finished chunk in the session file, so that an interrupted stage can be resumed.
   4. Stages that need a view of the entire code-base (e.g. proposing the module layout) do not use groups.
      Instead, Claude receives condensed input in a single session.

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
