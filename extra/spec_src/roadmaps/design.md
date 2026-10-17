# Rationale

## Groupy group

A call to `groupy group` recreates the group file, using the grouping strategy and the sizes in the config file, and
commits it. The developer uses it after changing the config file.

## Chunking the work

See ./chunking.md.

## Open points

1. Renamings: only symbols that are defined in the target code may be renamed, not the attributes, parameters and
   dict keys of external libraries. How do we ensure this?
   1. Maybe scramble the third party names to protect them from being renamed, and afterwards undo the scrambling.
   2. The scrambled name should contain a special token that allows Groupy/Claude to skip that name.
2. Should `done` be followed by a new round (e.g. `groupy group` and `analyze-terminology` on the restructured
   code)?

# Milestones

## MS-10: Groupy sync detects changed and renamed functions

1. Every `FunctionNode` gets a `body_hash: str | None` field: the first 12 hex characters of the md5 hash of the
   `ast.dump()` of the function's decorators, arguments and body (but not its name).
   1. Since the hash is computed from the AST, formatting and comments don't change it (docstrings do).
   2. Groupy sets the hash when it creates a node (e.g. in `groupy init` and `groupy sync`).
2. Whenever Groupy commits, it first refreshes the `body_hash` of the functions in the modules that changed, so
   that its own changes of the code (e.g. by rope or by an RFR) are not reported by `groupy sync`.
   1. Alternatively, we require the user to run `groupy hash` before they edit the source code manually.
3. `groupy sync` uses the hash:
   1. It reports a function whose hash differs from the source as `<module>: changed <location>`, and updates the
      hash. It does not change the analysis: the developer reviews whether it is still correct.
   2. When a removed node and an added node in the same module (with the same parent) have the same hash, Groupy
      treats them as a rename: it renames the node, so that it keeps its analysis, and reports
      `<module>: renamed <old location> to <new location>`.
   3. A rename combined with a change of the body is still reported as a removed and an added node.

## MS-11: The developer restricts the refactoring to a part of the target code

The developer may want to refactor only a part of the code-base (e.g. one feature area), while the analysis still
benefits from seeing the entire code-base (e.g. so that the glossary and the module layout fit all the code).

1. The config file gets a `refactoring_filter: List[str]` field (default: `[]`).
   1. Each entry is a glob pattern, relative to the target dir (e.g. `myapp/reports/**`).
   2. A module matches the filter when its path matches one of the patterns. When the filter is empty, every module
      matches.
   3. `groupy init` takes an optional `--refactoring-filter` (that can be repeated), whose patterns it writes to the
      config file that it creates. When the config file already exists, Groupy refuses this option, so that the
      config file stays the only source of the filter.
2. The analysis operates on the entire target dir.
   1. `groupy init`, `groupy sync` and `groupy group` keep a node file for every module, and the group file lists
      every module. The filter does not change the groups or the chunks, so that chunk ids do not depend on the
      filter.
   2. The analysis stages ignore the filter: the nesting of helper functions (identify-helper-functions), analyze-terminology
      and propose-module-layout (which receives the summaries of all modules).
   3. The call graph and the context of the Claude requests (e.g. `caller_sources`) cover the entire target dir.
3. The proposals and refactorings only start from the nodes in modules that match the filter.
   1. identify-helper-functions only renames the helper functions in matching modules.
   2. propose-renamings only makes an RFA for chunks with matching modules, and only for those modules. Groupy
      rejects (as a conflict) a renaming that is proposed for a node in a module that does not match.
   3. extract-methods, propose-move-steps-to-caller and propose-code-restructure only take candidates from matching
      modules. As before, a chunk without candidates is finished without an RFA.
   4. The validation of the code restructure (in propose-code-restructure and apply-code-restructure) only checks the nodes in matching modules, so that a
      module that does not match does not need a `code_unit_type`.
   5. The apply stages apply the proposals that exist. Since proposals only exist for matching modules, they need
      no extra check, but Groupy reports a proposal in a module that does not match (e.g. one that the developer
      added during the review) as a problem.
4. The ripple effects of a refactoring are applied everywhere in the target dir.
   1. The refactoring policy updates the call sites and the imports in all modules (e.g. when a function in a
      matching module is renamed or moved).
   2. In apply-move-steps-to-caller, a step of a function in a matching module may move to a caller in a module that
      does not match. Claude edits that caller, and updates its node file.
5. Since the analysis still covers the entire target dir, the filter does not reduce the cost of the Claude requests
   of the analysis stages. It limits what changes in the code.
6. The modules that do not match keep their own terminology: their aliases are not renamed and their helper
   functions are not renamed to start with an underscore.
