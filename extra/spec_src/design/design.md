## MS-11: The developer restricts the refactoring to a part of the target code

The developer may want to refactor only a part of the code-base (e.g. one feature area), and leave the rest of the
code as it is.

1. The session file gets an `exclude: List[str]` field (default: `[]`).
   1. Each entry is a glob pattern, relative to the target dir (e.g. `myapp/reports/**`). A `*` does not match a
      `/`, and a `**` matches any number of directories. A pattern is matched against the paths of the files, so
      `myapp/reports` does not exclude `myapp/reports/summary.py`.
   2. `groupy init` takes an optional `--exclude` (that can be repeated), whose patterns it writes to the
      session file that it creates. A pattern that matches no file is accepted (it excludes nothing).
      `--exclude` is not allowed with `--from-stage` (the new branch keeps the `exclude` of the session that it
      starts from).
   3. The config file (`.groupy/config.yaml`) may also contain an `exclude` field. The patterns that Groupy uses are
      the union of the patterns in the config file and the session file.
   4. The files that match one of the patterns are called "passive". The other files are called "active". When there
      are no patterns, every file is active. A node is active when the file of its module is active.
   5. Groupy reads the patterns at the start of every stage, so that a change to `exclude` takes effect at the next
      stage.
2. The analysis operates on the active files.
   1. `groupy init`, `groupy sync` and the group-modules stage operate on all files (active and passive) so that the groups
      and the chunk ids do not depend on `exclude`.
   2. The analysis stages ignore the passive files: identify-helper-functions does not nest the helper functions in
      passive files, analyze-terminology only covers the active files (so that the glossary only describes the active
      files), and propose-module-layout only receives the summaries of the active modules (so that the passive modules
      keep their location).
   3. The call graph and the context of the Claude requests (e.g. `caller_sources`) cover all files.
   4. The stages that work on chunks (and `groupy status`, which lists the remaining chunks) use a rule that filters
      the chunks: it drops the chunks whose files are all passive, and removes the passive files from the other
      chunks. The chunk ids stay the same. Since the RFA of a chunk is made from the files of the chunk, a chunk
      whose files are all passive gets no RFA, and the RFA of a chunk with active and passive files only lists the
      active files.
3. The proposals and refactorings only start from the active files.
   1. identify-helper-functions only renames the helper functions in active files.
   2. propose-renamings only proposes renamings for the active files of the (filtered) chunk.
   3. extract-methods, propose-move-steps-to-caller and propose-code-restructure only take candidates from active
      files. As before, a chunk without candidates is finished without an RFA.
   4. The validation of the code restructure (in propose-code-restructure and apply-code-restructure) only checks the
      active nodes, so that a passive module does not need a `code_unit_type`.
   5. Groupy rejects a proposal for a passive file (e.g. one that Claude made by mistake, or that the developer
      added during the review) with the existing validators, before anything changes. Since the (filtered) chunk only
      has active files, the propose stages also check the passive files. The proposal is reported as
      `<module>:<location>: is in a passive file`.
      1. validate-renamings reports it as a conflict (which propose-renamings retries, and apply-renamings raises).
      2. validate-code-restructure reports it as a problem (in propose-code-restructure and
         apply-code-restructure).
      3. apply-move-steps-to-caller raises a `PassiveStepMovesError` that lists the steps to move in passive files.
4. The ripple effects of a refactoring are applied everywhere in the target dir.
   1. The refactoring policy updates the call sites and the imports in all files (e.g. when a function in an active
      file is renamed or moved).
   2. In apply-move-steps-to-caller, a step of a function in an active file may move to a caller in a passive file.
      Claude edits that caller, and updates its node file. This is the only case in which Claude edits the code of a
      passive file directly.
