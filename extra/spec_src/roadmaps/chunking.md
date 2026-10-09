# Chunking the work

To keep the workload per Claude request reasonable, Breaker groups the node files into groups, it splits each
group into chunks and processes these chunks in series. There are three grouping strategies:

1. simple: We sort the node files by path and divide into groups of equal size (measured by lines of code).
2. package: A group contains all files (i.e. the entire file-tree) within a sub-package within the target root dir.
3. smart: We use Claude Haiku to create the groups.

## Smart grouping

1. Breaker creates an index file (`.breaker/index.yaml`) from the node files.
   1. Per node file, it contains the line count, the package, the module name, the modules that it imports
      (within the target code) and the list of function-names for that module.
   2. The index file does not involve Claude, so Breaker can rebuild it cheaply at any time.
2. Breaker asks Claude Haiku to assign each node file to a group.
   1. The node files within a group are semantically related (e.g. they cover the same feature area).
   2. The assignment is done incrementally, in batches of K node files (with K fixed).
      1. Breaker sorts the node files by path, so that related files tend to end up in the same batch.
      2. For each batch, Haiku receives the group description file (`.breaker/group-descriptions.md`) and an index
         file that only contains the K node files of the batch.
      3. Haiku returns the group numbers for these K node files and the updated group description file.
   3. The group description file contains one line per group, with the group number and a one-line description.
      1. Haiku may add new groups or refine the description of an existing group (when the new files clearly
         widen the topic of the group).
      2. Haiku may not renumber, merge or delete groups. Breaker checks this after each batch.
   4. The group numbers are stored in the group file (`.breaker/groups.txt`), where every line contains a node file
      path and a group number.
      1. Breaker discards malformed lines, and lines that assign a node file to more than one group.
      2. Node files that did not get a group number are added to the next batch.
      3. If node files are still unassigned after the last batch, Breaker asks the user to assign them.
3. Groups may grow arbitrarily large.
   1. A group is a semantic unit. A chunk is a unit of work.
   2. Breaker splits a large group into several chunks (e.g. by subpackage, then by sorted path).
   3. If a group turns out to be a catch-all (e.g. "misc utilities") then we may later decide to re-run the
      incremental assignment for the files of that group.
4. Breaker keeps the group file up-to-date.
   1. When an action renames a file, it also renames it in the group file.
   2. When an action splits off code into a new file, the new file goes into the same group as the original file.
   3. For stages where we know that the structure may have changed a lot (e.g. after the code restructure),
      `breaker next` first recreates the group file.
5. An RFA refers to the group file.
   1. Each chunk is a fresh Claude session that receives the group description and the pre-computed context.
   2. Chunks are usually not independent. How work is handed over from one chunk to the next (e.g. via a
      summary that is passed to the next chunk) is defined per RFA.
   3. Breaker records each finished chunk in the session file, so that an interrupted stage can be resumed.
   4. Stages that need a view of the entire code-base (e.g. proposing the module layout) do not use groups.
      Instead, Claude receives condensed input in a single session.
