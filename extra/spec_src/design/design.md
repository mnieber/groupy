## MS-11: The developer restricts the refactoring to a part of the target code

The developer may want to refactor only a part of the code-base (e.g. one feature area), and leave the rest of the
code as it is.

1. The session file gets an `exclude: List[str]` field (default: `[]`).
   1. Each entry is a glob pattern, relative to the target dir (e.g. `myapp/reports/**`). A `*` does not match a
      `/`, and a `**` matches any number of directories.
   2. `groupy init` takes an optional `--exclude` (that can be repeated), whose patterns it writes to the
      session file that it creates.
   3. The config file (`.groupy/config.yaml`) may also contain an `exclude` field. The patterns that Groupy uses are
      the union of the patterns in the config file and the session file.
   4. The files that match one of the patterns are called "passive". The other files are called "active". When there
      are no patterns, every file is active. A node is active when the file of its module is active.
   5. Groupy reads the patterns at the start of every stage, so that a change to `exclude` takes effect at the next
      stage.
2. The analysis operates on the active files.
   1. `groupy init`, `groupy sync` and `groupy group` operate on all files (active and passive) so that the groups
      and the chunk ids do not depend on `exclude`.
   2. The analysis stages ignore the passive files: identify-helper-functions does not nest the helper functions in
      passive files, analyze-terminology only covers the active files (so that the glossary only describes the active
      files), and propose-module-layout only receives the summaries of the active modules (so that the passive modules
      keep their location).
   3. The call graph and the context of the Claude requests (e.g. `caller_sources`) cover all files.
3. The proposals and refactorings only start from the active files.
   1. identify-helper-functions only renames the helper functions in active files.
   2. propose-renamings only makes an RFA for chunks with active files, and only for those active files.
   3. extract-methods, propose-move-steps-to-caller and propose-code-restructure only take candidates from active
      files. As before, a chunk without candidates is finished without an RFA.
   4. The validation of the code restructure (in propose-code-restructure and apply-code-restructure) only checks the
      active nodes, so that a passive module does not need a `code_unit_type`.
   5. Since proposals are only made for active files, the apply stages apply the proposals that exist. Groupy rejects
      (as a conflict) a proposal for a passive file (e.g. one that Claude made by mistake, or that the developer added
      during the review).
4. The ripple effects of a refactoring are applied everywhere in the target dir.
   1. The refactoring policy updates the call sites and the imports in all files (e.g. when a function in an active
      file is renamed or moved).
   2. In apply-move-steps-to-caller, a step of a function in an active file may move to a caller in a passive file.
      Claude edits that caller, and updates its node file. This is the only case in which Claude edits the code of a
      passive file directly.
