# Chunking the work

To keep the workload per Claude request reasonable, Breaker groups the node files into groups, it splits each
group into chunks and processes these chunks in series.

1. Groups and chunks contain module node files only. They refer to a module node file by the path of its module,
   relative to the target dir (e.g. `myapp/books.py`). Package node files are not grouped.
2. The size of a module is the number of lines in its source file.
3. Groups are numbered from 1, in the order of their first module path.
4. There are three grouping strategies:
   1. simple: We sort the modules by path and divide them into groups of roughly equal size. Breaker adds modules
      to a group until the next module would make it larger than the maximum group size; then it starts a new group.
      A module that is larger than the maximum group size gets a group of its own.
   2. package: A group contains all modules (i.e. the entire file-tree) within a sub-package of a top-level package
      in the target dir (e.g. `myapp/books`). The modules that are directly in a top-level package (e.g.
      `myapp/__init__.py`) form a group of their own.
   3. smart: We use Claude Haiku to create the groups.
5. Breaker splits a group into chunks of at most the maximum chunk size.
   1. It sorts the modules by path, and tries to keep the modules of a package (i.e. the modules that are directly
      in the same dir) in the same chunk: when a package doesn't fit in the current chunk, it starts a new chunk.
   2. A package that is larger than the maximum chunk size is split by sorted path.
   3. A module that is larger than the maximum chunk size gets a chunk of its own.
   4. Chunks are numbered per group, and the chunk id contains both numbers (e.g. `group-2/chunk-1`). The same
      group gives the same chunks, with the same ids.
6. `breaker init` creates the group file, using the grouping strategy and the sizes in the config file.
   1. `breaker group` recreates the group file (e.g. after the developer changed the config file).
   2. `breaker next` refuses to run when there is no group file.
   1. A stage gets its chunks by loading the group file and splitting each group into chunks.

## Incremental accumulation

Some tasks need to consider all node files, but the input is too large for a single Claude request.
Such tasks use incremental accumulation:

1. Breaker divides the input into batches of K items (with K fixed).
2. For each batch, Claude receives the batch and a state file, and returns the updated state file.
   1. The state file accumulates the result of the batches that were processed so far.
3. Breaker validates the state file after each batch.
   1. The task defines which changes to the state file are allowed (e.g. only adding entries).
4. Items that were not processed in a batch are added to the next batch.

## Smart grouping

1. Breaker creates an index file (`.breaker/index.yaml`) from the node files.
   1. Per node file, it contains the line count, the package, the module name, the modules that it imports
      (within the target code) and the list of function-names for that module.
   2. The index file does not involve Claude, so Breaker can rebuild it cheaply at any time.
2. Breaker asks Claude Haiku to assign each node file to a group.
   1. The node files within a group are semantically related (e.g. they cover the same feature area).
   2. The assignment uses incremental accumulation (see above), in batches of K node files,
      with the group description file as the state file.
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
      `breaker next` first recreates the group file. It only does this at the start of a stage, and not when it
      resumes an interrupted stage, so that the finished chunks in the session file stay valid.
5. An RFA refers to the group file.
   1. Each chunk is a fresh Claude session that receives the group description and the pre-computed context.
   2. Chunks are usually not independent. How work is handed over from one chunk to the next (e.g. via a
      summary that is passed to the next chunk) is defined per RFA.
   3. Breaker records each finished chunk in the session file, so that an interrupted stage can be resumed.
   4. Stages that need a view of the entire code-base (e.g. proposing the module layout) do not use groups.
      Instead, Claude receives condensed input in a single session.
