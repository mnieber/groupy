# Scope

Breaker is a radical refactoring tool that takes a python code-base apart and rebuilds it.
Since it is expected to break the code, the developer will need to help with
fixing the errors and testing.

# Glossary

- action: an operation - offered by Breaker - that changes nodes files and/or target code
- callback: a call from Claude to Breaker - using the Claude Agent API - requesting Breaker to run an action
- chunk: a sub-set of node files in a group that is processed together
- config file: a file with the choices that the developer makes for a session (e.g. the grouping strategy)
- group: a group of semantically related node files
- group file: a file that assigns each node file to a group
- helper candidate: a function that might just be a helper function (e.g. because it's is only called by one other function in the same module)
- node file: a yaml file that captures the structure of a Python module or package
- request for actions (RFA): a request to Claude to analyze the node files and Python code and run actions
- request for refactoring (RFR): a request to Claude to refactor the Python code directly, without calling actions
- rope: a Python library that can perform refactorings
- stage id: the id of the current stage in the refactoring. The user call `breaker next` to move to the next stage.
- sub-session: a fresh Claude session that handles (part of) a chunk
- target code: the Python code that we're refactoring

# Rationale

## Breaker and Claude collaborate on editing node files and source files

Typically the user will initiate a Breaker session and call `breaker next` to perform the next stage in the refactoring.
Breaker will make RFAs. In response, Claude will issue callbacks to run Breaker actions.
These actions may update node files, or refactor the code via rope, or trigger RFRs that cause Claude to refactor the Python code directly.
Breaker commits the updated node files and source files after each action; it groups the commits by prefixing the commit message with the stage id.

## Breaker next

A call to `breaker next` runs the stage in the `next_stage` field of the session file.

1. It refuses to run when there is no session, when there is no group file (see ./chunking.md), or when the working
   tree is not clean.
2. It runs the stage. Most stages make an RFA per chunk.
   1. The callbacks of Claude run actions, and Breaker commits after each action, with the commit message
      `<stage-id>: <callback name>`.
   2. After each chunk, Breaker records the chunk as finished in the session file (in the `finished_chunks` field,
      using the RFA id `<stage-id>/<chunk-id>`), and commits with the message `<stage-id>: finish <chunk-id>`.
   3. When a stage is interrupted (e.g. by an error), the next call to `breaker next` runs the same stage again,
      and skips the finished chunks.
   4. When an action fails, Breaker restores the working tree to the last commit (undoing the partial changes of the
      action, e.g. of rope or an RFR) and re-raises the error, which interrupts the stage. The actions that succeeded
      stay committed, so the developer can inspect and repair the state, and run `breaker next` again. Each stage
      derives its remaining work from the node files (e.g. the renamings that are left, or the candidates that are
      not `n/a`), so that a resumed stage does not repeat finished work.
3. After the stage, Breaker sets `next_stage` to the stage that follows it, clears `finished_chunks`, and commits
   with the message `<stage-id>: finish the stage`.

## Breaker group

A call to `breaker group` recreates the group file, using the grouping strategy and the sizes in the config file, and
commits it. The developer uses it after changing the config file.

## Config file

The config file (`.breaker/config.yaml`) contains the choices that the developer makes for a session.

1. `rfa_policy`, `rfr_policy`, `grouping_policy` and `refactoring_policy`: the import path (`<module>:<name>`) of a
   callable that returns the policy that Breaker uses to make RFAs, RFRs and smart groups, and to refactor the code
   (see "Refactoring policy"). This is usually the policy class itself (e.g.
   `breaker.claude_requests.policies.claude_rfa_policy:ClaudeRfaPolicy`), but tests use a function that returns a
   fake policy.
   1. Breaker creates a policy when it needs it, and does not keep it.
2. `grouping_strategy`: `simple`, `package` or `smart` (default: `package`).
3. `max_group_lines` and `max_chunk_lines`: the maximum size of a group and of a chunk (in lines of code, default:
   2000 and 500).
4. Fields that are missing in the config file get their default value.
5. The config file is part of the session, so a change of the config file must be committed before
   `breaker next` runs.

## Refactoring policy

1. Breaker refactors the code (e.g. renaming a symbol, including its call sites) through a `RefactoringPolicy`
   (`renamings/policies/refactoring_policy.py`). The default implementation, `RopeRefactoringPolicy`, uses rope.
   1. `rename_symbol(source_root, module_name, scope_location, name, new_name)` renames the symbol `name` in the
      scope (`@module` for module-level names, a class name for attributes and methods, or a function location for
      local symbols), including its imports and call sites in other modules. It raises `RenameConflictError` when
      the new name clashes with an existing name, before it changes any file.
   2. The policy is passed to the actions that refactor (e.g. `rename_helper_functions` and `apply_renamings`), so
      that the engine can be replaced (e.g. by libcst, or by an RFR when rope cannot do a refactoring).
2. Tests use `FakeRefactoringPolicy`, which subclasses `RopeRefactoringPolicy`, records the renames, and raises an
   error for the renames that the test lets fail.

## Breaker sync

A call to `breaker sync` updates the node files so that their structure reflects the structure of the source files
again (e.g. after the developer changed the code by hand). The developer then reviews the changes, and updates the
analysis (e.g. the concepts and steps) where needed, because Breaker does not re-evaluate it.

1. The structure consists of the names of the top-level functions, the classes and their methods, and the
   module-level variables.
   1. Helper function nodes count as top-level functions (also the helpers of methods), because helper functions
      are top-level functions in the Python code (see "Nested functions").
   2. Functions that are nested in the Python code have no node, so they are not compared.
   3. Breaker does not detect changes inside a function body, so the analysis of a changed function may be stale
      (MS-9 adds this).
2. Breaker updates the node files:
   1. It adds a node for every name that is in the source but not in the node file. The new node is inserted in
      source order among its siblings.
   2. It removes the node of every name that is in the node file but not in the source.
      1. The helper function nodes of a removed node take its place (in the same list), so that they keep their
         own analysis. The analysis of the removed node itself is dropped.
      2. A renamed function, class or variable is therefore a removed node and an added node: Breaker cannot tell a
         rename from a removal plus an addition. The analysis of the removed node is visible in the diff of the
         node file, so the developer can move it to the new node.
   3. It sets `line_count` of every module node file.
   4. It creates the module node file of a module that has none (and the package node file of a new package), and
      it deletes the node file of a module that no longer exists. It updates the `module_names` of the package node
      files accordingly.
   5. It updates the group file: a new module goes into the group of a module in the same dir, or else into a new
      group (with the next free group number). A deleted module is removed from its group.
3. Breaker reports each change on a line:
   1. `<module>: added <location>` and `<module>: removed <location>`, where the location is the qualified name
      (e.g. `Book.save`). For a removed node with fields that do not have their default value (other than `name`),
      the line ends with `(it had <fields>)`, e.g. `(it had responsibilities, steps)`, as a hint to move them.
   2. `<module>: created the node file` and `<module>: deleted the node file`.
   3. The lines are sorted by module and location, and followed by the line
      `Please review the changes to the node files (e.g. with git diff), and move the analysis of renamed nodes.`
      A change of `line_count` alone is not reported. Without changes, Breaker prints `The node files match the source.`
4. `breaker sync` does not commit, and does not require a clean working tree. Since `breaker next` requires a clean
   working tree, the developer reviews and commits the changes before the next stage.

## Guidelines for the Claude requests

1. Breaker pre-computes everything that can be computed deterministically and passes it to Claude as context.
   1. E.g. the call graph (who calls which function, inside and outside the module), the source of the module,
      and the project glossary (in the analyze-terminology stage: the glossary so far).
   2. Claude should spend its effort on judgement, not on facts that Breaker can compute.
2. All edits to node files are done by Breaker, not by Claude directly.
   The edit location is passed in the callback as:
   - "@module": to indicate a change in the module node
   - \_get_api_url to indicate a change in the function node for that function
   - get_api_usage.\_get_api_url to disambiguate the location using the parent function name
   - Book.save to indicate a change in the node of a method (or of a helper function of a method)

   A location that is the full qualified name of a node (e.g. `validate` for a top-level function) finds that node.
   Otherwise, the location must match the end of the qualified name of exactly one node; if it matches several
   nodes (e.g. `save` when `Book` and `Author` both have a `save` method), the location is ambiguous and the edit is
   rejected.

3. When an action or RFR changes the code of a function, then the analysis of that function (e.g. its concepts,
   responsibilities and steps) is updated in the same RFA (or RFR), so that later stages don't work with stale data.
4. An RFR edits the source directly, but it may also run callbacks to update the node files.
   1. In an RFR, only the node file edits (e.g. `add_step`, `move_function_to_parent`), the glossary edits and
      `commit_refactoring` are allowed. Callbacks that refactor the code (e.g. `extract_method`) are rejected with
      `CallbackNotAllowedError`, so that an RFR never starts another RFR.
   2. The callbacks in an RFR do not commit by themselves, because the source may be half-refactored while they
      run. Instead, `commit_refactoring(description)` checks that the changed Python files parse, and commits the
      source and the node files together with the message `<stage-id>: <description>`. If a file does not parse,
      Breaker restores the working tree to the last commit and raises `RefactoringDoesNotParseError`.
   3. An RFR that is made by a stage (rather than by a callback) must commit its work with `commit_refactoring`
      (typically once per refactoring). When there are uncommitted changes after the RFR, Breaker restores the
      working tree and raises `UncommittedRefactoringError`.
   4. An RFR that is made by a callback (e.g. `extract_method`) does not call `commit_refactoring`: the callback
      verifies the result and commits.

## Functions and methods

1. Class methods are processed in the same way as standalone functions.
   1. A method is considered to be a function that is called in a special way (with a `self` argument).
   2. This applies to all analysis stages (e.g. helper functions, terminology, renamings and extract-method).
2. In the call graph, calls to methods are marked as uncertain when Breaker cannot determine which method is called.
   1. E.g. `obj.save()` cannot be resolved without knowing the type of `obj`, and subclasses may override `save`.
   2. Claude takes this uncertainty into account when it uses the call graph (e.g. to decide whether a function
      is a helper function).
3. Some methods must stay methods, because Python or a framework calls them:
   1. dunder methods (e.g. `__str__`, `__eq__`) and properties.
   2. overrides of methods of a base class (e.g. `save` in a Django model).
   3. methods that have several implementations across subclasses.
4. In the code restructure, every other method may be turned into an action or rule that takes the instance as its
   first argument.

## Nested functions

1. A function that is nested in the Python code (e.g. a closure) is part of the body of its enclosing function.
   1. It has no node of its own: its name and local symbols are covered by the `local_terms`, `renamings` and
      `steps` of the enclosing function.
   2. It stays nested in the Python code.
2. Nesting in the node file has a different meaning: a function node in `helper_function_nodes` is a helper
   function of its parent function node.
   1. In the Python code, a helper function is a top-level function in the same module as its parent function.

## Chunking the work

See ./chunking.md.

## Call graph

Breaker maintains a single call graph for the target code (ignoring test code), and passes a filtered view of it
to Claude. See ./call-graph.md.

## Example

An example node file is given in `./module_node_example.md`.

## Node file schema

1. A `ModuleNode` has the fields:
   1. `name: str`: the path of the module, relative to the source root.
   2. `rename_to: str | None`: the proposed new path.
   3. `line_count: int`: the number of lines of code in the Python file.
   4. `concepts: Dict[str, str | None]`: concepts that apply to the entire module, mapped onto a short description.
   5. `renamings: Dict[str, str]`: renamings that apply to the entire module.
   6. `function_nodes: List[FunctionNode]`: the top-level functions in the module.
   7. `class_nodes: List[ClassNode]`: the classes in the module.
   8. `variable_nodes: List[VariableNode]`: the module-level variables and constants.
2. A `FunctionNode` has the fields:
   1. `name: str`
   2. `rename_to: str | None`
   3. `move_to_file: str | None`: the proposed new path.
   4. `code_unit_type: str | None`: one of `action`, `rule`, `util`, `entrypoint`.
   5. `is_helper_candidate: bool`,
   6. `concepts: Dict[str, str | None]`
   7. `local_terms: Dict[str, str | None]`
   8. `responsibilities: List[str]`
   9. `steps: List[str]`
   10. `steps_to_move_to_caller: List[str]`: the steps (texts from `steps`, in the order of `steps`) that are proposed to move
       to the caller(s) of the function (see MS-7).
   11. `extract_method_priority: Literal['high', 'medium', 'low', 'n/a'] | None`: `None` means that the
       priority is not set yet.
   12. `renamings: Dict[str, str]`
   13. `aliases: Dict[str, List[str]]`
   14. `abbreviations: Dict[str, str]`
   15. `helper_function_nodes: List[FunctionNode]`: the helper functions of this function. They are top-level
       functions in the Python code (see "Nested functions").
3. A `ClassNode` has the fields:
   1. `name: str`
   2. `rename_to: str | None`
   3. `move_to_file: str | None`
   4. `code_unit_type: str | None`: one of `model`, `schema`, `enum`, `exception`, `policy`, `other`.
   5. `concepts: Dict[str, str | None]`
   6. `responsibilities: List[str]`
   7. `extract_method_priority: Literal['high', 'medium', 'low', 'n/a'] | None`
   8. `renamings: Dict[str, str]`
   9. `method_nodes: List[FunctionNode]`
4. A `VariableNode` has the fields `name: str`, `rename_to: str | None`, `move_to_file: str | None` and
   `code_unit_type: str | None`: one of `constant`, `setting`.
5. A `PackageNode` has the fields:
   1. `name: str`: the path of the package, relative to the source root. The root package (the target dir) has
      the name `"."`.
   2. `module_names: List[str]`: the modules in the package (including `__init__.py`, but not the
      sub-packages).
   3. `proposed_modules: Dict[str, str]`: only used in the root package node file (the package node file of
      the target dir).
6. The `concepts` and `local_terms` fields map each concept or local term onto a short description.
   1. The description is empty if it is already given elsewhere (e.g. in `ModuleNode.concepts`).
   2. Breaker writes an empty description as `null`, but accepts both `null` and `""`.
7. All paths in node files use the same notation: a file path relative to the source root
   (e.g. `myapp/reports/rules/create_user_stats_report.py`).
8. Breaker leaves out the fields that have their default value (`null`, `{}`, `[]` or `false`) when it writes a
   node file, and it reads a missing field as its default value.
   1. Therefore, a missing field and a field with the default value mean the same thing.
   2. The fields are written in the order of the schema, so that loading and saving a node file keeps its contents.

## Glossary file

1. The project glossary (`glossary.breaker.yaml` in the root of the target dir) is a list of entries. Each entry
   describes one concept, with the fields:
   1. `name: str`: the name of the concept.
   2. `description: str`: a one-line description.
   3. `aliases: List[str]`: other names that are used in the code-base for this concept.
   4. `abbreviation: str | None`: the abbreviation of the concept, if any.
2. When a name is used for several meanings in the code-base, the glossary has an entry per meaning (with the same
   name), each with its own aliases and abbreviation.
3. As for node files, fields that have their default value are left out.
4. Breaker saves the entries sorted by name. The sort is stable, so entries with the same name keep their order.
5. Callbacks identify an entry by its name.
   1. When several entries have that name, the callback also passes `meaning_nr`: the (1-based) position of the
      entry among the entries with that name. Without it, the callback is rejected as ambiguous.
6. The glossary is a guide for choosing names. The concepts in the node files do not need to have an entry in the
   glossary, and the glossary does not record where its concepts are used.
7. Breaker offers these actions on the glossary (they are also available as callbacks):
   1. `add_glossary_entry(name, description)`: adds a new entry, also when there already is an entry with that name
      (a second meaning).
   2. `set_glossary_description(name, description)`.
   3. `add_glossary_alias(name, alias)`: an alias is listed once.
   4. `set_glossary_abbreviation(name, abbreviation)`: an abbreviation of `null` removes the abbreviation.
   5. `merge_glossary_entries(name, into_name)`: removes the entry `name`, and adds its name and aliases to the
      aliases of the entry `into_name`. The entry `into_name` keeps its description, and its abbreviation (if it has
      none, it gets the abbreviation of the entry `name`). It takes `meaning_nr` for `name` and `into_meaning_nr`
      for `into_name`.
   6. An action on a name that is not in the glossary raises an error, and leaves the glossary unchanged.
   7. When the glossary file does not exist yet, the actions treat it as an empty glossary.

```yaml
- name: report
  description: a markdown document with the statistics of a user
- name: report
  description: an error report that is sent to Sentry
  aliases: [error_doc]
- name: title
  description: the name of a book
  aliases: [name, book_title]
  abbreviation: ttl
```

# Milestones

## MS-1: A developer initiates a breaker session

1. The developer runs `breaker init --target-dir=<target-dir> --branch-name=<branch-name>`
2. Breaker will create a new branch with --branch-name
3. Breaker will create a .breaker/session.yaml file in the repository root.
   1. This session file contains a `next_stage` field that identifies the next stage of the refactoring
   2. It also contains the `target_dir` field that identifies the target code.
   3. When the repository does not contain a config file (see "Config file"), Breaker creates it with all fields set
      to their default value. Otherwise, it keeps the existing config file.
4. Breaker will create node files that form a source map
   1. Per package it will create a package node file (called `package-node.breaker.yaml`) in the package root.
      1. A package is the target dir (the root package), or a dir below it that contains Python modules, directly
         or in a sub-dir.
      2. A dir does not need an `__init__.py` to be a package (i.e. namespace packages are packages).
   2. Per python module it will create a module node file (e.g. `books.py.breaker.yaml` for `books.py`)
      1. Initially, each module node file just reflects the current contents of the module.
      2. Specifically, Breaker sets the initial contents of the `function_nodes`, `class_nodes` and
         `variable_nodes` fields.
      3. Every top-level function gets a node in `function_nodes`, and every method gets a node in the `method_nodes`
         of its class; the `helper_function_nodes` fields are still empty.
      4. Functions that are nested in the Python code get no node (see "Nested functions").
      5. An `__init__.py` is just another module, so it also gets a module node file.
5. Breaker creates the group file (see ./chunking.md), using the grouping strategy and the sizes in the config file.
   1. The developer can inspect (and edit) the group file before running the first stage.
6. Breaker creates a first commit with the session file, the config file, the group file and the new node files.
   1. It will set `next_stage` to `identify-helper-functions`.

## MS-2: Breaker identifies helper functions

1. The user calls `breaker next` to start the next stage.
2. The stage processes the chunks one by one. For each chunk, Breaker computes the call graph and marks the helper
   candidates in the node files of the chunk (setting `is_helper_candidate`), and commits with the message
   `identify-helper-functions: mark_helper_candidates`.
   1. A function or method is a helper candidate when it has exactly one caller, and this caller is a function or
      method in the same module that calls it through a certain edge.
   2. Therefore, a function is not a helper candidate when it has no callers, when it is called from module-level
      code, from another module or by several functions, or when one of its calls is uncertain.
   3. Dunder methods (e.g. `__init__`) are never helper candidates, because Python calls them.
3. Breaker will ask Claude to examine the FunctionNodes in the module node file.
   1. The RFA context contains the call graph view of the chunk (see ./call-graph.md), with the callers of each
      function.
   1. Claude decides which functions are helper functions and uses the move_function_to_parent action to nest them under their parent function.
      1. Not every helper candidate will necessarily turn out to be a helper function.
      2. A function that is called from outside the module is never a helper function.
      3. The move_function_to_parent action only changes the node file: in the Python code, the helper function
         stays a top-level function.
      4. The move_function_to_parent action is a plain edit of the node file: it does not check who calls the
         function (that is Claude's judgement). It can also move a helper function to another parent, and move a
         method (which signifies that the method is treated as a helper function of its new parent).
   1. A function that is called by several functions in the module is not nested. It stays a top-level function
      (it later will typically become a rule or util).
4. After the RFA of a chunk, Breaker renames the helper functions in the chunk so that they start with an underscore
   (in the node file and in the source, using the refactoring policy), and commits with the message
   `identify-helper-functions: rename_helper_functions`. Then it finishes the chunk.
   1. This applies to all helper function nodes, also to helpers of helpers and to helpers of methods. A helper
      whose name already starts with an underscore keeps its name.
   2. Rope also renames the call sites (and imports) in other modules.
   3. Renaming the helpers per chunk keeps the node files, the source and the call graph consistent for the next
      chunk.
   4. When the new name clashes with an existing name in the module, Breaker raises an error (before it changes any
      file), which interrupts the stage. The developer resolves the clash and runs `breaker next` again.
5. Breaker commits the results and updates `next_stage` to `analyze-terminology`.

## MS-3: Breaker analyzes the terminology

1. The developer runs `breaker next`
2. Breaker will pass each node file to Claude and ask it to update it (by running actions)
   1. Breaker makes an RFA per chunk. The RFA context contains:
      1. `module_sources`: the source of each module of the chunk (by module name).
      2. `call_graph_view`: the call graph view of the chunk, with the callers and the callees.
      3. `glossary`: the text of the glossary file so far (empty when there is no glossary file yet).
   2. Claude first updates the `ModuleNode.concepts: Dict[str, str | None]` field
      1. These are the concepts that apply to the module as a whole.
      2. Each key names a concept and the value is a short description of that concept.
      3. They are recorded once at the module level to avoid repeating them in each FunctionNode.
         Concepts in `FunctionNode.concepts` are not necessarily less important.
   3. Claude will then update each function-node in `function_nodes` (and each class-node in `class_nodes`):
      1. It updates the `FunctionNode.concepts: Dict[str, str | None]` field
         1. Each key names a concept that is used in the function, and that is not already present (with the same meaning) in `ModuleNode.concepts`.
            1. If it's present there with a different meaning (which should be rare), then it can be duplicated in the FunctionNode.
         2. The value optionally describes the concept.
            1. Claude leaves the description empty if it is already given elsewhere (e.g. in another node of the
               same module), unless the meaning in this function is specific.
            2. When the glossary has several entries (meanings) for the name, the meaning is always specific, so
               Claude gives a description.
         3. A concept is a term that helps explain the purpose and responsibilities of the function.
      2. It updates the `FunctionNode.local_terms: Dict[str, str | None]` field
         1. Each key names a local term that is used in the function
         2. The value optionally describes the local term (following the same rule as for concepts).
         3. A local term has local significance but is not significant in a wider context (and therefore is not a concept).
            1. E.g. `hash_tag` may be a local term if the function deals with hash_tags, but this term may not
               be a meaningful concept within the larger context that is the code-base.
            2. Claude will use its own judgement to distinguish between concepts and local terms.
               1. The distinction matters because concepts are only meaningful when not everything is a concept.
      3. It updates the `FunctionNode.responsibilities: List[str]` field.
         1. Each string describes a responsibility of the function
         2. The description usually refers to concepts and local terms.
         3. The responsibility to update (by the action) is identified by its list index
         4. Based on whether the function has too many responsibilities, it sets `extract_method_priority`.
            1. `'n/a'` means that the function doesn't need refactoring
      4. It updates the `FunctionNode.steps: List[str]` field
         1. Each string describes a step that the function takes to meet its responsibilities.
         2. The description usually refers to concepts and local terms.
         3. The step to update (by the action) is identified by its list index
      5. When a function uses several names for the same concept or term (aliases), Claude records each concept or
         term once (using the name that it considers canonical) and lists the aliases in the
         `FunctionNode.aliases: Dict[str, List[str]]` field.
         1. E.g. `outlier: [outlier_point]`.
         2. The list of aliases serves as an input for determining the renamings that are used to get rid of aliases.
   4. Claude updates the project glossary (see "Glossary file") with the concepts of the chunk.
      1. Each RFA receives the glossary so far, so that Claude can reuse the names and descriptions of earlier chunks.
      2. A concept that is not in the glossary yet is added with its description.
      3. When a concept has the same meaning as a glossary entry with another name, Claude adds its name as an alias
         of that entry.
      4. When a concept has the same name as a glossary entry, but a different meaning, Claude adds a new entry
         with the same name. Claude does not try to resolve this.
      5. Abbreviations may be used to keep names relatively short.
         1. Concepts that are already short usually don't need an abbreviation.
         2. Abbreviations are recorded in the glossary so that they can be applied consistently across the
            code-base.
            1. Once an abbreviation is introduced, we should always use exactly that abbreviation and no alternative
               abbreviations.
   5. After the RFA of a chunk, Breaker checks that Claude analyzed every function node (also method nodes and
      helper function nodes) and class node of the chunk, i.e. that its `extract_method_priority` is set.
      1. If some nodes are not analyzed, Breaker makes one follow-up RFA (with the id `<rfa-id>/retry-1`) whose
         context lists their locations (`unanalyzed_nodes`, sorted, e.g. `myapp/books.py:Book.__init__`).
      2. If nodes are still not analyzed after the follow-up RFA, Breaker raises an error that lists them. This
         interrupts the stage, and the chunk is not finished.
3. After the last chunk, Breaker asks Claude to consolidate the glossary (in a single session that receives the
   entire glossary).
   1. The consolidation RFA has the id `analyze-terminology/consolidate-glossary`, and its context contains the
      `glossary`. It is treated as a final chunk: Breaker records it in `finished_chunks` and commits with the message
      `analyze-terminology: finish consolidate-glossary`, so that a stage that is interrupted during the
      consolidation only reruns the consolidation.
   2. Early chunks may have added entries that turn out to have the same meaning. Claude merges them into one entry,
      and the other names become aliases.
   3. Claude makes the abbreviations consistent.
   4. Claude does not resolve names with several meanings; that is up to the developer.
4. The developer reviews the glossary and cleans it up.
   1. In particular, the developer gives entries with the same name distinct names (e.g. `report` for the user
      statistics, and `error_report`, with the alias `report`, for the error reports).
5. Breaker commits the results and updates `next_stage` to `propose-renamings`.

## MS-4: Breaker proposes renamings that unify the terminology

1. The developer runs `breaker next`.
2. Breaker asks Claude to update the `FunctionNode.renamings: Dict[str, str]` field, using the glossary.
   1. Breaker makes an RFA per chunk. The RFA context contains `module_sources` (the source of each module of the
      chunk) and `glossary` (the text of the glossary file). Claude reads the concepts and aliases from the node
      files.
   2. Renamings are used to get rid of aliases. They apply to:
      1. Symbols that are local to the function (variables and parameters).
      2. Concepts and local terms (in the node file)
   3. Claude will chose `renamings` such that all aliases are replaced by the canonical name.
      1. Ideally, the canonical name comes from the global glossary,
      2. Claude may also choose the canonical name from the module scope.
   4. The glossary is a guide. When a concept in the node file has the same meaning as a glossary entry (judged
      from its description and the source), Claude may rename the concept to the name of that entry, also when
      the glossary lists the concept as an alias.
      1. When the glossary still has several entries with the same name, Claude chooses the entry from the
         context, or leaves the name unchanged.
      2. A concept without a glossary entry keeps its name, unless one of the other rules applies.
      3. The entire symbol is stored as the key, not some part thereof (since there is no partial matching).
      4. The new name maintains the meaning (e.g. plural stays plural).
         1. E.g. if the function uses `outlier` and `outlier_point` as aliases then `new_outlier_points` will be renamed to `new_outliers` and `find_next_outlier_point` will be renamed to `find_next_outlier`.
   5. Renamings can also be used to create shorter symbol names.
   6. A renaming of the function itself is stored in `FunctionNode.rename_to`.
      Renamings of module-level symbols are stored in `ModuleNode.renamings`.
   7. The `renamings` field maps the old symbol name onto the new symbol name, using these guidelines:
      1. Map types are renamed to `foo_by_bar` where `foo` is the value and `bar` is the key.
         1. It's also possible to have `foo_by_bar_by_baz`, where `baz` is the key and `foo_by_bar` is the value.
      2. Abbreviations from the glossary may be used to keep the new name relatively short.
         1. E.g. if `sf` is the abbreviation for `suitability_fraction` in the glossary then Claude may add a renaming from `highest_suitability_fraction_by_plot_id` to `highest_sf_by_plot_id`
         2. Local terms that need an abbreviation are recorded in `FunctionNode.abbreviations: Dict[str, str]`.
      3. Only symbols that are defined in the code-base are renamed. Attributes, parameters and dict-keys of external
         libraries are not renamed.
         1. ❔how will we ensure this?
         2. Maybe scramble the third party names to protect them from being renamed, and afterwards undo the scrambling?
         3. The scrambled name should contain a special token that allows Breaker/Claude to skip that name.
3. Breaker validates the proposed renamings after the RFA of each chunk.
   1. It reports a conflict when a new name clashes with an existing name in the same scope, that is not itself
      renamed. The scopes are:
      1. A function: its local symbols (variables and parameters) and the keys of its `renamings`.
      2. A class: its attributes and methods, with the class `renamings` and the `rename_to` of its methods.
      3. A module: its top-level functions, classes and variables, with `ModuleNode.renamings` and the `rename_to`
         of its top-level nodes.
   2. It also reports a conflict when two renamings in the same scope have the same new name.
   3. A chain (e.g. `title -> text` and `text -> body`) is allowed: the new name `text` is renamed away, and
      apply-renamings orders the renames so that they work. A cycle (e.g. a swap of `title` and `text`) is a
      conflict, because there is no such order without a temporary name.
   4. Each conflict is a line `<module>:<scope location>: <description>`, where the scope location is `@module`
      for the module scope, e.g.:
      1. `myapp/reports.py:create_report: title -> text clashes with the existing name text`
      2. `myapp/reports.py:create_report: report -> person and user -> person have the same new name`
      3. `myapp/reports.py:create_report: text -> title and title -> text form a cycle`
   5. When there are conflicts, Breaker makes one follow-up RFA (with the id `<rfa-id>/retry-1`) whose context
      lists them (`renaming_conflicts`, sorted). If conflicts remain after the follow-up RFA, Breaker raises an error
      that lists them. This interrupts the stage, and the chunk is not finished.
4. Breaker commits the results and updates `next_stage` to `apply-renamings`.

## MS-5: Breaker applies the unified terminology

1. The developer reviews all node files, possibly making edits to the proposed renamings and terminology.
2. When they are done, they run `breaker next`.
   1. Breaker first checks all renamings for conflicts (see MS-4), before it changes anything. When there are
      conflicts, it raises the same error as propose-renamings, which lists them. Since a module whose renamings
      are applied has no renamings left, the check also works when the stage is resumed.
   2. Breaker will then apply the renamings (using `rename_symbol` of the refactoring policy), including in all call
      sites in the code-base.
      1. This stage makes no Claude requests. It processes the chunks with `process_chunks`, and the modules of a
         chunk in sorted order.
      2. Per module, Breaker applies all renamings of the module node file (the `renamings` of the module, its
         classes and its functions, and the `rename_to` of its functions, methods and classes), updates the node
         file, and commits with the message `apply-renamings: apply the renamings of <module>`. A module without
         renamings gets no commit.
      3. Within a scope, Breaker orders the renames so that a chain works (e.g. for `title -> text` and
         `text -> body`, it renames `text` first).
      4. A renaming whose old name is not a symbol in the source scope (e.g. a concept such as `outlier_point`)
         only renames the keys in the node file.
      5. When a rename fails, Breaker discards the uncommitted changes (it restores the working tree to the last
         commit, which also undoes the renames of the module that already succeeded), and re-raises the error. The
         module keeps its renamings, so the next `breaker next` resumes at that module.
   3. Breaker updates each node whose renamings it applied:
      1. `name` becomes `rename_to`, and `rename_to` is cleared.
      2. The keys of `concepts`, `local_terms` and `abbreviations` are renamed by the `renamings` of the node, all at
         once (so `text -> body` and `body -> content` turn the keys `text` and `body` into `body` and `content`).
         When a key that is not renamed already has the new name, it keeps its own description.
      3. `renamings` and `aliases` are cleared, because the aliases are gone.
3. Breaker commits the results and updates `next_stage` to `extract-methods`.

## MS-6: Breaker extract methods

1. The developer runs `breaker next`.
2. Breaker creates a list of functions to refactor based on the `FunctionNode.extract_method_priority` field.
   1. The candidates are the function nodes (also method nodes and helper function nodes) with the priority `high`
      or `medium`.
3. It divides this list into chunks and asks Claude to apply "extract method" to each function that requires it.
   1. Breaker makes an RFA per module chunk that has candidates. A chunk without candidates is finished without an
      RFA.
   2. The RFA context contains `extract_method_candidates` (the locations `<module>:<location>`, with the `high`
      candidates first, then in order of location) and `module_sources`.
   3. Claude calls the callback `extract_method(module_name, location, new_name, description)`.
      1. Breaker makes an RFR with the id `extract_method/<module>:<location>/<new_name>`, whose context contains
         the `module_name`, `location`, `new_name` and `description`. In the RFR, Claude adds the top-level function
         `new_name` to the module (also when it extracts from a method) and calls it from the parent.
      2. After the RFR, Breaker checks that the module has a new top-level function `new_name`, and that the parent
         still exists. If not, it restores the working tree to the last commit and raises
         `ExtractMethodFailedError`.
      3. Otherwise, the extract-method action creates a node for the extracted function in `function_nodes` (in
         source order), and Breaker commits with the message `extract-methods: extract_method`.
   4. In the same RFA, Claude fills in the analysis of the extracted function (e.g. concepts, responsibilities and
      steps) and updates the analysis of the parent function.
      1. When the extracted function is a helper function of the parent, Claude nests it with
         `move_function_to_parent`. After the RFA, Breaker renames the helper functions of the chunk so that they
         start with an underscore (as in MS-2), and commits with the message
         `extract-methods: rename_helper_functions` (only when it renamed something).
   5. Claude sets the `extract_method_priority` of a candidate to `n/a` when it is done with it (also when it
      decides not to extract anything).
      1. After the RFA of a chunk, Breaker makes one follow-up RFA (with the id `<rfa-id>/retry-1`) for the candidates
         that still have the priority `high` or `medium`, whose context lists them (`unfinished_candidates`).
      2. If candidates are still unfinished after the follow-up RFA, Breaker raises `UnfinishedCandidatesError`,
         which lists them. This interrupts the stage, and the chunk is not finished.
4. Breaker commits the results and updates `next_stage` to `propose-move-steps-to-caller`.

## MS-7: Breaker moves steps to the caller

Moving a step changes the behaviour for every caller, so the developer reviews the proposed moves before they are
applied. The stage is therefore split in two: `propose-move-steps-to-caller` and `apply-move-steps-to-caller`.

1. The developer runs `breaker next`.
2. Breaker asks Claude to identify steps in a function F that should be done by the caller of F, before it calls F.
   1. Typically, such a step has already been extracted into a separate function in the extract-methods stage,
      so that moving the step means moving a single function call.
   2. Breaker passes the callers of F (from the call graph) to Claude.
   3. A step is only moved when F has a single caller, or when all callers of F should clearly perform the step.
      Otherwise, moving the step would duplicate code.
   4. The candidates are the function nodes (also method nodes and helper function nodes) that have at least one
      caller, where all callers are functions or methods with certain edges (not module-level code).
   5. Breaker makes an RFA per chunk that has candidates. A chunk without candidates is finished without an RFA. The
      RFA context contains `move_step_candidates` (the locations `<module>:<location>`, sorted), `module_sources`,
      and `caller_sources`: the source of each caller of a candidate (also in other modules), by its location.
   6. Claude records each step that should move in `FunctionNode.steps_to_move_to_caller`, with the actions
      `add_step_to_move_to_caller(module_name, location, step)` and `remove_step_to_move(module_name, location, step)`.
      1. The step must be one of the `steps` of the function, and it is listed once.
      2. `update_step` also updates the step in `steps_to_move_to_caller`, and `remove_step` also removes it from
         `steps_to_move_to_caller`.
   7. The source does not change. There is no check that Claude considered every candidate: moving steps is
      optional.
3. Breaker commits the results and updates `next_stage` to `apply-move-steps-to-caller`.
4. The developer reviews the proposed moves (and possibly edits them), and runs `breaker next`.
5. Claude moves the steps to the caller(s) of F, and updates the analysis of F and of its callers.
   1. Since this is a refactoring of the source, the stage makes an RFR (not an RFA) per chunk that has steps to
      move, with the id `apply-move-steps-to-caller/<chunk-id>`. A chunk without steps to move is finished without
      an RFR.
   2. The RFR context contains `steps_to_move_to_caller` (lines `<module>:<location>: <step>`, sorted by location and in the
      order of the steps), `module_sources`, and `caller_sources` (the source of each caller of a function with
      steps to move).
   3. Claude edits the source, updates the steps of F and of its callers with the node file edits, and calls
      `commit_refactoring` after each move (see "Guidelines for the Claude requests"). Removing the step from F
      (with `remove_step`) also removes it from `steps_to_move_to_caller`. When Claude decides that a step cannot be moved,
      it withdraws the proposal with `remove_step_to_move`.
   4. After the RFR of a chunk, Breaker makes one follow-up RFR (with the id `<rfr-id>/retry-1`) for the steps that
      are still in `steps_to_move_to_caller`, whose context lists them. If steps are still not moved after the follow-up RFR,
      Breaker raises `UnappliedStepMovesError`, which lists them. This interrupts the stage, and the chunk is not
      finished.
6. Breaker commits the results and updates `next_stage` to `propose-module-layout`.

## MS-8: Breaker proposes to restructure the code

1. The developer runs `breaker next`.
2. Breaker asks Claude to propose the module layout of the application package.
   1. Claude receives the glossary and, for each module node file, the module concepts and the names and
      responsibilities of the top-level functions and classes.
   2. Claude runs an action to record the list of proposed modules in the root package node file (in the
      `PackageNode.proposed_modules: Dict[str, str]` field), mapping each module name onto a one-line description.
   3. The developer reviews (and possibly edits) the proposed module layout.
3. Breaker commits the results and updates `next_stage` to `propose-code-restructure`.
4. The developer runs `breaker next`.
5. Breaker asks Claude to propose a structuring for each module node file, using the proposed module layout.
   1. For every top-level function, class and module-level variable, Claude sets the `code_unit_type` field
      and the `move_to_file` field.
      1. Claude leaves `move_to_file` empty when the target is the current file. Since an empty field is left
         out of the node file, Breaker uses `code_unit_type` to check that every node was considered.
   2. Claude sets `ModuleNode.rename_to` when the module will continue to exist (typically it is renamed after
      the main function in that file), or to null when no rename is needed.
6. The target code structure follows the following guidelines:
   1. Application package
      1. The application consists of a single application package (e.g. `myapp/`).
      2. The application package is divided into feature packages, e.g. `myapp/books/`, `myapp/chapters/`.
         1. Each feature package covers one cohesive area of the domain and is named after its main concept,
            using the canonical name from the glossary).
            1. When in doubt, plural form is preferred, e.g. `books` or `chapters`.
         2. Code that is used by several modules but belongs to none of them goes into a shared module
            (e.g. `myapp/utils/` for generic utils).
   2. Code units
      1. A function that changes the application state (e.g. it writes to a database, a file or a network
         service, or it mutates its arguments) is an action.
         1. It goes to `<module>/actions/<action_name>.py`.
      2. A function that retrieves or computes information subject to business logic, without changing the
         application state, is a rule.
         1. It goes to `<module>/rules/<rule_name>.py`.
      3. A function that is free from business logic (a generic helper) is a util.
         1. It goes to `<module>/utils/<util_name>.py`.
         2. A group of many small, closely related utils (e.g. small math helpers) may share a single group file.
      4. A dataclass that represents a domain entity is a model.
         1. It goes to `<module>/models/<model_name>.py`.
         2. It uses the `dataclass` decorator from the `dataclassy` package.
      5. Pydantic classes that describe the structure of a JSON blob are schemas.
         1. They go into a schema file that is located close to the code that uses it.
      6. Enums go to `<module>/enums.py`. All enums of a module live in this single file.
      7. A module-level variable whose value configures the application (e.g. a timeout, a URL, a limit or a
         value that is read from an environment variable) is a setting.
         1. Settings (including all reads of environment variables) go to the single file
            `<app_package>/settings.py`.
      8. Any other module-level variable is a constant.
         1. It goes to the target file of the code unit that uses it.
         2. When several code units in different target files use it, it goes to the target file of one of them,
            and the other files import it from there.
            1. Preferably, this is the file of the lowest code unit in the dependency direction (see
               "Dependencies"), so that the imports follow that direction.
            2. If this creates a circular import, then the developer fixes it later (Breaker does not try to
               prevent it).
      9. Application entrypoints go to `<app_package>/runtime/entrypoints/<name>.py`.
         1. Entrypoints are usually registered in the `[project.scripts]` section of `pyproject.toml`, but this is outside of scope for Breaker.
      10. An exception class is defined in the action file that raises it.
          1. Only very generic exceptions that are shared by many actions go to `<module>/utils/exceptions.py`.
      11. A class that defines the interface to an external service (e.g. Claude, Jira or a payment provider) is a
          policy.
          1. The abstract policy goes to `<module>/policies/<policy_name>.py` (e.g. `rfa_policy.py`), and each
             implementation goes to its own file in the same directory (e.g. `claude_rfa_policy.py`).
          2. Fake implementations for tests live with the tests (e.g. in `fake_policies.py`).
   3. Files
      1. Each action, rule, util and model gets its own file (except for util group files).
      2. The file is named after the code unit it contains, in snake_case
         (e.g. `CreateChapterForm` and `create_chapter` live in `chapters/actions/create_chapter.py`).
      3. Helper functions stay in the file of their parent function and start with an underscore.
         1. A helper that is used by several public functions is promoted to a rule or util.
   4. Dependencies
      1. Dependencies point in one direction: entrypoints → actions → rules → utils.
         1. A rule never calls an action, and a util never calls a rule or an action.
         2. Models, schemas and enums may be used by all code units.
         3. A policy is passed as an argument to the action that uses it, so that a test can pass a fake policy.
            1. A policy does not import actions or rules. When it needs to call back (e.g. to run a callback of
               Claude), it receives the function as an argument.
      2. Imports between modules must not create circular imports at runtime.
         1. Type references to models in other modules use a `typing.TYPE_CHECKING` guard.
7. Breaker validates the proposal.
   1. It checks that every top-level node has a `code_unit_type`.
   2. It checks that each `move_to_file` path matches the location rule of its `code_unit_type`.
   3. It checks that no target file receives more than one public code unit (except for util group files,
      enums, schemas, settings, constants and the exception/form classes that go with an action). Each policy
      implementation is a code unit of its own.
   4. It uses the call graph to report dependencies that violate the dependency direction.
8. Breaker commits the results and updates `next_stage` to `apply-code-restructure`.

## MS-9: Breaker sync detects changed and renamed functions

1. Every `FunctionNode` gets a `body_hash: str | None` field: the first 12 hex characters of the md5 hash of the
   `ast.dump()` of the function's decorators, arguments and body (but not its name).
   1. Since the hash is computed from the AST, formatting and comments don't change it (docstrings do).
   2. Breaker sets the hash when it creates a node (e.g. in `breaker init` and `breaker sync`).
2. Whenever Breaker commits, it first refreshes the `body_hash` of the functions in the modules that changed, so
   that its own changes of the code (e.g. by rope or by an RFR) are not reported by `breaker sync`.
   1. Alternatively, we require the user to run `breaker hash` before they edit the source code manually.
3. `breaker sync` uses the hash:
   1. It reports a function whose hash differs from the source as `<module>: changed <location>`, and updates the
      hash. It does not change the analysis: the developer reviews whether it is still correct.
   2. When a removed node and an added node in the same module (with the same parent) have the same hash, Breaker
      treats them as a rename: it renames the node, so that it keeps its analysis, and reports
      `<module>: renamed <old location> to <new location>`.
   3. A rename combined with a change of the body is still reported as a removed and an added node.
