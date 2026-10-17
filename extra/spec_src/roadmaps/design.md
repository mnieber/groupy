# Glossary

- helper candidate: a function that might just be a helper function (e.g. because it's is only called by one other function in the same module)
- rope: a Python library that can perform refactorings
- sub-session: a fresh Claude session that handles (part of) a chunk

# Rationale

## Groupy group

A call to `groupy group` recreates the group file, using the grouping strategy and the sizes in the config file, and
commits it. The developer uses it after changing the config file.

## Refactoring policy

1. Groupy refactors the code (e.g. renaming a symbol, including its call sites) through a `RefactoringPolicy`
   (`renamings/policies/refactoring_policy.py`). The default implementation, `RopeRefactoringPolicy`, uses rope.
   1. `rename_symbol(source_root, module_name, scope_location, name, new_name)` renames the symbol `name` in the
      scope (`@module` for module-level names, a class name for attributes and methods, or a function location for
      local symbols), including its imports and call sites in other modules. It raises `RenameConflictError` when
      the new name clashes with an existing name, before it changes any file.
   2. The policy is passed to the actions that refactor (e.g. `rename_helper_functions` and `apply_renamings`), so
      that the engine can be replaced (e.g. by libcst, or by an RFR when rope cannot do a refactoring).
2. Tests use `FakeRefactoringPolicy`, which subclasses `RopeRefactoringPolicy`, records the refactorings (the
   method, the module and the name), and raises an error for the refactorings that the test lets fail.

## Groupy sync

A call to `groupy sync` updates the node files so that their structure reflects the structure of the source files
again (e.g. after the developer changed the code by hand). The developer then reviews the changes, and updates the
analysis (e.g. the concepts and steps) where needed, because Groupy does not re-evaluate it.

1. The structure consists of the names of the top-level functions, the classes and their methods, and the
   module-level variables.
   1. Helper function nodes count as top-level functions (also the helpers of methods), because helper functions
      are top-level functions in the Python code (see "Nested functions").
   2. Functions that are nested in the Python code have no node, so they are not compared.
   3. Groupy does not detect changes inside a function body, so the analysis of a changed function may be stale
      (MS-10 adds this).
2. Groupy updates the node files:
   1. It adds a node for every name that is in the source but not in the node file. The new node is inserted in
      source order among its siblings.
   2. It removes the node of every name that is in the node file but not in the source.
      1. The helper function nodes of a removed node take its place (in the same list), so that they keep their
         own analysis. The analysis of the removed node itself is dropped.
      2. A renamed function, class or variable is therefore a removed node and an added node: Groupy cannot tell a
         rename from a removal plus an addition. The analysis of the removed node is visible in the diff of the
         node file, so the developer can move it to the new node.
   3. It sets `line_count` of every module node file.
   4. It creates the module node file of a module that has none (and the package node file of a new package), and
      it deletes the node file of a module that no longer exists. It updates the `module_names` of the package node
      files accordingly.
   5. It updates the group file: a new module goes into the group of a module in the same dir, or else into a new
      group (with the next free group number). A deleted module is removed from its group.
3. Groupy reports each change on a line:
   1. `<module>: added <location>` and `<module>: removed <location>`, where the location is the qualified name
      (e.g. `Book.save`). For a removed node with fields that do not have their default value (other than `name`),
      the line ends with `(it had <fields>)`, e.g. `(it had responsibilities, steps)`, as a hint to move them.
   2. `<module>: created the node file` and `<module>: deleted the node file`.
   3. The lines are sorted by module and location, and followed by the line
      `Please review the changes to the node files (e.g. with git diff), and move the analysis of renamed nodes.`
      A change of `line_count` alone is not reported. Without changes, Groupy prints `The node files match the source.`
4. `groupy sync` does not commit, and does not require a clean working tree. Since `groupy next` requires a clean
   working tree, the developer reviews and commits the changes before the next stage.

## Functions and methods

1. Class methods are processed in the same way as standalone functions.
   1. A method is considered to be a function that is called in a special way (with a `self` argument).
   2. This applies to all analysis stages (e.g. helper functions, terminology, renamings and extract-method).
2. In the call graph, calls to methods are marked as uncertain when Groupy cannot determine which method is called.
   1. E.g. `obj.save()` cannot be resolved without knowing the type of `obj`, and subclasses may override `save`.
   2. Claude takes this uncertainty into account when it uses the call graph (e.g. to decide whether a function
      is a helper function).
3. Some methods must stay methods, because Python or a framework calls them:
   1. dunder methods (e.g. `__str__`, `__eq__`) and properties.
   2. overrides of methods of a base class (e.g. `save` in a Django model).
   3. methods that have several implementations across subclasses.
4. In the code restructure, every other method may delegate to an action, rule or util that takes the instance as
   its first argument (see MS-8 and MS-9).
   1. The method continues to exist, and its body becomes a call of the new function. Therefore, the call sites of
      the method (which may be uncertain in the call graph) don't change.
   2. The developer can later drop the method by inlining it, if they wish.

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

Groupy maintains a single call graph for the target code (ignoring test code), and passes a filtered view of it
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
   2. Groupy writes an empty description as `null`, but accepts both `null` and `""`.
## Glossary file

1. The project glossary (`glossary.groupy.yaml` in the root of the target dir) is a list of entries. Each entry
   describes one concept, with the fields:
   1. `name: str`: the name of the concept.
   2. `description: str`: a one-line description.
   3. `aliases: List[str]`: other names that are used in the code-base for this concept.
   4. `abbreviation: str | None`: the abbreviation of the concept, if any.
2. When a name is used for several meanings in the code-base, the glossary has an entry per meaning (with the same
   name), each with its own aliases and abbreviation.
3. As for node files, fields that have their default value are left out.
4. Groupy saves the entries sorted by name. The sort is stable, so entries with the same name keep their order.
5. Callbacks identify an entry by its name.
   1. When several entries have that name, the callback also passes `meaning_nr`: the (1-based) position of the
      entry among the entries with that name. Without it, the callback is rejected as ambiguous.
6. The glossary is a guide for choosing names. The concepts in the node files do not need to have an entry in the
   glossary, and the glossary does not record where its concepts are used.
7. Groupy offers these actions on the glossary (they are also available as callbacks):
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

## MS-2: Groupy identifies helper functions

1. The user calls `groupy next` to start the next stage.
2. The stage processes the chunks one by one. For each chunk, Groupy computes the call graph and marks the helper
   candidates in the node files of the chunk (setting `is_helper_candidate`), and commits with the message
   `identify-helper-functions: mark_helper_candidates`.
   1. A function or method is a helper candidate when it has exactly one caller, and this caller is a function or
      method in the same module that calls it through a certain edge.
   2. Therefore, a function is not a helper candidate when it has no callers, when it is called from module-level
      code, from another module or by several functions, or when one of its calls is uncertain.
   3. Dunder methods (e.g. `__init__`) are never helper candidates, because Python calls them.
3. Groupy will ask Claude to examine the FunctionNodes in the module node file.
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
4. After the RFA of a chunk, Groupy renames the helper functions in the chunk so that they start with an underscore
   (in the node file and in the source, using the refactoring policy), and commits with the message
   `identify-helper-functions: rename_helper_functions`. Then it finishes the chunk.
   1. This applies to all helper function nodes, also to helpers of helpers and to helpers of methods. A helper
      whose name already starts with an underscore keeps its name.
   2. Rope also renames the call sites (and imports) in other modules.
   3. Renaming the helpers per chunk keeps the node files, the source and the call graph consistent for the next
      chunk.
   4. When the new name clashes with an existing name in the module, Groupy raises an error (before it changes any
      file), which interrupts the stage. The developer resolves the clash and runs `groupy next` again.
5. Groupy commits the results and updates `next_stage` to `analyze-terminology`.

## MS-3: Groupy analyzes the terminology

1. The developer runs `groupy next`
2. Groupy will pass each node file to Claude and ask it to update it (by running actions)
   1. Groupy makes an RFA per chunk. The RFA context contains:
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
   5. After the RFA of a chunk, Groupy checks that Claude analyzed every function node (also method nodes and
      helper function nodes) and class node of the chunk, i.e. that its `extract_method_priority` is set.
      1. If some nodes are not analyzed, Groupy makes one follow-up RFA (with the id `<rfa-id>/retry-1`) whose
         context lists their locations (`unanalyzed_nodes`, sorted, e.g. `myapp/books.py:Book.__init__`).
      2. If nodes are still not analyzed after the follow-up RFA, Groupy raises an error that lists them. This
         interrupts the stage, and the chunk is not finished.
3. After the last chunk, Groupy asks Claude to consolidate the glossary (in a single session that receives the
   entire glossary).
   1. The consolidation RFA has the id `analyze-terminology/consolidate-glossary`, and its context contains the
      `glossary`. It is treated as a final chunk: Groupy records it in `finished_chunks` and commits with the message
      `analyze-terminology: finish consolidate-glossary`, so that a stage that is interrupted during the
      consolidation only reruns the consolidation.
   2. Early chunks may have added entries that turn out to have the same meaning. Claude merges them into one entry,
      and the other names become aliases.
   3. Claude makes the abbreviations consistent.
   4. Claude does not resolve names with several meanings; that is up to the developer.
4. The developer reviews the glossary and cleans it up.
   1. In particular, the developer gives entries with the same name distinct names (e.g. `report` for the user
      statistics, and `error_report`, with the alias `report`, for the error reports).
5. Groupy commits the results and updates `next_stage` to `propose-renamings`.

## MS-4: Groupy proposes renamings that unify the terminology

1. The developer runs `groupy next`.
2. Groupy asks Claude to update the `FunctionNode.renamings: Dict[str, str]` field, using the glossary.
   1. Groupy makes an RFA per chunk. The RFA context contains `module_sources` (the source of each module of the
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
         3. The scrambled name should contain a special token that allows Groupy/Claude to skip that name.
3. Groupy validates the proposed renamings after the RFA of each chunk.
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
   5. When there are conflicts, Groupy makes one follow-up RFA (with the id `<rfa-id>/retry-1`) whose context
      lists them (`renaming_conflicts`, sorted). If conflicts remain after the follow-up RFA, Groupy raises an error
      that lists them. This interrupts the stage, and the chunk is not finished.
4. Groupy commits the results and updates `next_stage` to `apply-renamings`.

## MS-5: Groupy applies the unified terminology

1. The developer reviews all node files, possibly making edits to the proposed renamings and terminology.
2. When they are done, they run `groupy next`.
   1. Groupy first checks all renamings for conflicts (see MS-4), before it changes anything. When there are
      conflicts, it raises the same error as propose-renamings, which lists them. Since a module whose renamings
      are applied has no renamings left, the check also works when the stage is resumed.
   2. Groupy will then apply the renamings (using `rename_symbol` of the refactoring policy), including in all call
      sites in the code-base.
      1. This stage makes no Claude requests. It processes the chunks with `process_chunks`, and the modules of a
         chunk in sorted order.
      2. Per module, Groupy applies all renamings of the module node file (the `renamings` of the module, its
         classes and its functions, and the `rename_to` of its functions, methods and classes), updates the node
         file, and commits with the message `apply-renamings: apply the renamings of <module>`. A module without
         renamings gets no commit.
      3. Within a scope, Groupy orders the renames so that a chain works (e.g. for `title -> text` and
         `text -> body`, it renames `text` first).
      4. A renaming whose old name is not a symbol in the source scope (e.g. a concept such as `outlier_point`)
         only renames the keys in the node file.
      5. When a rename fails, Groupy discards the uncommitted changes (it restores the working tree to the last
         commit, which also undoes the renames of the module that already succeeded), and re-raises the error. The
         module keeps its renamings, so the next `groupy next` resumes at that module.
   3. Groupy updates each node whose renamings it applied:
      1. `name` becomes `rename_to`, and `rename_to` is cleared.
      2. The keys of `concepts`, `local_terms` and `abbreviations` are renamed by the `renamings` of the node, all at
         once (so `text -> body` and `body -> content` turn the keys `text` and `body` into `body` and `content`).
         When a key that is not renamed already has the new name, it keeps its own description.
      3. `renamings` and `aliases` are cleared, because the aliases are gone.
3. Groupy commits the results and updates `next_stage` to `extract-methods`.

## MS-6: Groupy extract methods

1. The developer runs `groupy next`.
2. Groupy creates a list of functions to refactor based on the `FunctionNode.extract_method_priority` field.
   1. The candidates are the function nodes (also method nodes and helper function nodes) with the priority `high`
      or `medium`.
3. It divides this list into chunks and asks Claude to apply "extract method" to each function that requires it.
   1. Groupy makes an RFA per module chunk that has candidates. A chunk without candidates is finished without an
      RFA.
   2. The RFA context contains `extract_method_candidates` (the locations `<module>:<location>`, with the `high`
      candidates first, then in order of location) and `module_sources`.
   3. Claude calls the callback `extract_method(module_name, location, new_name, description)`.
      1. Groupy makes an RFR with the id `extract_method/<module>:<location>/<new_name>`, whose context contains
         the `module_name`, `location`, `new_name` and `description`. In the RFR, Claude adds the top-level function
         `new_name` to the module (also when it extracts from a method) and calls it from the parent.
      2. After the RFR, Groupy checks that the module has a new top-level function `new_name`, and that the parent
         still exists. If not, it restores the working tree to the last commit and raises
         `ExtractMethodFailedError`.
      3. Otherwise, the extract-method action creates a node for the extracted function in `function_nodes` (in
         source order), and Groupy commits with the message `extract-methods: extract_method`.
   4. In the same RFA, Claude fills in the analysis of the extracted function (e.g. concepts, responsibilities and
      steps) and updates the analysis of the parent function.
      1. When the extracted function is a helper function of the parent, Claude nests it with
         `move_function_to_parent`. After the RFA, Groupy renames the helper functions of the chunk so that they
         start with an underscore (as in MS-2), and commits with the message
         `extract-methods: rename_helper_functions` (only when it renamed something).
   5. Claude sets the `extract_method_priority` of a candidate to `n/a` when it is done with it (also when it
      decides not to extract anything).
      1. After the RFA of a chunk, Groupy makes one follow-up RFA (with the id `<rfa-id>/retry-1`) for the candidates
         that still have the priority `high` or `medium`, whose context lists them (`unfinished_candidates`).
      2. If candidates are still unfinished after the follow-up RFA, Groupy raises `UnfinishedCandidatesError`,
         which lists them. This interrupts the stage, and the chunk is not finished.
4. Groupy commits the results and updates `next_stage` to `propose-move-steps-to-caller`.

## MS-7: Groupy moves steps to the caller

Moving a step changes the behaviour for every caller, so the developer reviews the proposed moves before they are
applied. The stage is therefore split in two: `propose-move-steps-to-caller` and `apply-move-steps-to-caller`.

1. The developer runs `groupy next`.
2. Groupy asks Claude to identify steps in a function F that should be done by the caller of F, before it calls F.
   1. Typically, such a step has already been extracted into a separate function in the extract-methods stage,
      so that moving the step means moving a single function call.
   2. Groupy passes the callers of F (from the call graph) to Claude.
   3. A step is only moved when F has a single caller, or when all callers of F should clearly perform the step.
      Otherwise, moving the step would duplicate code.
   4. The candidates are the function nodes (also method nodes and helper function nodes) that have at least one
      caller, where all callers are functions or methods with certain edges (not module-level code).
   5. Groupy makes an RFA per chunk that has candidates. A chunk without candidates is finished without an RFA. The
      RFA context contains `move_step_candidates` (the locations `<module>:<location>`, sorted), `module_sources`,
      and `caller_sources`: the source of each caller of a candidate (also in other modules), by its location.
      1. The source of a caller that is a method is dedented, and its location is its qualified name (e.g.
         `myapp/stats.py:Sample.summarize`).
   6. Claude records each step that should move in `FunctionNode.steps_to_move_to_caller`, with the actions
      `add_step_to_move_to_caller(module_name, location, step)` and
      `remove_step_to_move_to_caller(module_name, location, step)`.
      1. The step must be one of the `steps` of the function, and it is listed once.
      2. The action does not check that the function is a candidate: the candidates guide Claude, the developer
         reviews the proposals, and the apply stage can withdraw a proposal that it cannot do.
      3. `update_step` also updates the step in `steps_to_move_to_caller`, and `remove_step` also removes it from
         `steps_to_move_to_caller`.
   7. The source does not change. There is no check that Claude considered every candidate: moving steps is
      optional.
3. Groupy commits the results and updates `next_stage` to `apply-move-steps-to-caller`.
4. The developer reviews the proposed moves (and possibly edits them), and runs `groupy next`.
5. Claude moves the steps to the caller(s) of F, and updates the analysis of F and of its callers.
   1. Since this is a refactoring of the source, the stage makes an RFR (not an RFA) per chunk that has steps to
      move, with the id `apply-move-steps-to-caller/<chunk-id>`. A chunk without steps to move is finished without
      an RFR.
   2. The RFR context contains `steps_to_move_to_caller` (lines `<module>:<location>: <step>`, sorted by location and in the
      order of the steps), `module_sources`, and `caller_sources` (the source of each caller of a function with
      steps to move).
   3. Claude edits the source, updates the steps of F and of its callers with the node file edits, and calls
      `commit_refactoring` after each move. Removing the step from F
      (with `remove_step`) also removes it from `steps_to_move_to_caller`. When Claude decides that a step cannot be moved,
      it withdraws the proposal with `remove_step_to_move_to_caller`.
   4. After the RFR of a chunk, Groupy makes one follow-up RFR (with the id `<rfr-id>/retry-1`) for the steps that
      are still in `steps_to_move_to_caller`, whose context lists them. If steps are still not moved after the follow-up RFR,
      Groupy raises `UnappliedStepMovesError`, which lists them. This interrupts the stage, and the chunk is not
      finished.
6. Groupy commits the results and updates `next_stage` to `propose-module-layout`.

## MS-8: Groupy proposes to restructure the code

1. The developer runs `groupy next`.
2. Groupy asks Claude to propose the module layout of the application package.
   1. Claude receives the glossary and, for each module node file, the module concepts and the names and
      responsibilities of the top-level functions and classes.
      1. Groupy makes a single RFA for the whole code-base, with the id `propose-module-layout/all`. It is recorded
         as a finished chunk (`finish all`), so that a resumed stage does not repeat it.
      2. The RFA context contains `glossary` (the text of the glossary file) and `module_summaries`: per module
         node file, its `concepts` and its `code_units`, which map the name of each top-level function and class
         onto its first responsibility (or `None`). Module-level variables and helper function nodes are left out.
   2. Claude runs an action to record the list of proposed modules in the root package node file (in the
      `PackageNode.proposed_modules: Dict[str, str]` field), mapping each module name onto a one-line description.
      1. A module name is the path of a (feature) package, e.g. `myapp/books` or `myapp/utils`.
      2. The actions are `set_proposed_module(name, description)` and `remove_proposed_module(name)`.
   3. The developer reviews (and possibly edits) the proposed module layout.
3. Groupy commits the results and updates `next_stage` to `propose-code-restructure`.
4. The developer runs `groupy next`.
5. Groupy asks Claude to propose a structuring for each module node file, using the proposed module layout.
   1. Groupy makes an RFA per chunk, whose context contains `module_sources`, `proposed_modules`,
      `call_graph_view` (with the callers and callees, so that Claude can follow the dependency direction) and
      `glossary`. Claude uses the callbacks `set_code_unit_type`, `set_move_to_file` and `set_rename_to`.
   2. For every top-level function, class and module-level variable, Claude sets the `code_unit_type` field
      and the `move_to_file` field.
      1. Claude leaves `move_to_file` empty when the target is the current file. Since an empty field is left
         out of the node file, Groupy uses `code_unit_type` to check that every node was considered.
      2. Helper function nodes need no `code_unit_type`, because they move with their parent.
      3. The target file of a node is its `move_to_file`, or else its module (with the module's `rename_to`, if
         any).
   3. Claude sets `ModuleNode.rename_to` when the module will continue to exist (typically it is renamed after
      the main function in that file), or to null when no rename is needed.
   4. Claude may also set the `code_unit_type` (`action`, `rule` or `util`) and the `move_to_file` of a method node,
      to propose that the method delegates to a new function in that file (see "Functions and methods").
      1. The new function is named after the target file (e.g. `save_book` for
         `myapp/books/actions/save_book.py`), or after the `rename_to` of the method node when the target is a util
         group file.
      2. A method without these fields stays as it is. Claude does not set them for the methods that must stay
         methods (see "Functions and methods").
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
            2. If this creates a circular import, then the developer fixes it later (Groupy does not try to
               prevent it).
      9. Application entrypoints go to `<app_package>/runtime/entrypoints/<name>.py`.
         1. Entrypoints are usually registered in the `[project.scripts]` section of `pyproject.toml`, but this is outside of scope for Groupy.
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
7. Groupy validates the proposal after the RFA of each chunk.
   1. It validates all node files, and keeps the problems of the nodes of the chunk (so that a clash with a node of
      an earlier chunk is reported for the node of this chunk). Each problem is a line
      `<module>:<location>: <description>`, e.g.: 1. `myapp/reports/report.py:count_reports: has no code_unit_type` 2. `myapp/reports/report.py:Report: a model goes to <package>/models/report.py, not
myapp/reports/rules/report.py` 3. `myapp/reports/report.py:create_book: myapp/books/actions/create_book.py already receives
myapp/books.py:create_book` 4. `myapp/reports/report.py:Report.__str__: a dunder method cannot delegate` (and likewise `a property`,
      `an override of Base.describe` and `a method that uses super()`) 5. `myapp/reports/report.py:list_kinds: the target package myapp/reports/enums clashes with the module
myapp/reports/enums.py`
   2. It checks that every top-level node has a `code_unit_type`.
   3. It checks that each `move_to_file` path matches the location rule of its `code_unit_type`.
   4. It checks that no target file receives more than one public code unit (except for util group files,
      enums, schemas, settings, constants and the exception/form classes that go with an action). Each policy
      implementation is a code unit of its own.
   5. It checks that a method with a `move_to_file` can delegate: its `code_unit_type` is `action`, `rule` or
      `util`, and it is not a dunder method, a property, a `classmethod` or `staticmethod`, an override of a method
      of a base class in the target code, or a method that uses `super()` or name-mangled attributes
      (`__name`). Overrides of methods of external base classes (e.g. `save` in a Django model) cannot be detected,
      so they are Claude's (and the developer's) judgement.
   6. It checks that no target package has the same name as an existing module that stays (e.g.
      `myapp/books/actions/create_book.py` while `myapp/books.py` is not renamed), because Python cannot import
      both.
   7. When there are problems, Groupy makes one follow-up RFA (with the id `<rfa-id>/retry-1`) whose context lists
      them (`restructure_problems`, sorted). If problems remain after the follow-up RFA, Groupy raises
      `CodeRestructureHasProblemsError`, which lists them. This interrupts the stage, and the chunk is not finished.
   8. After the last chunk, it uses the call graph to report dependencies that violate the dependency direction.
      They do not block the stage, because the developer may accept them during the review. 1. The code unit type of a node is its `code_unit_type`. A helper function has the type of its parent, and a
      method has the type of its class, unless the method delegates (then it has its own `code_unit_type`, so
      that its calls are judged as calls of the new function). 2. Groupy prints `The proposed code structure has dependency violations:`, followed by a line per
      violation, sorted, e.g. `myapp/reports/report.py:get_overdue_reports (rule) calls
myapp/reports/report.py:send_reminder (action)`. Without violations, it prints
      `The proposed code structure follows the dependency direction.`
8. Groupy commits the results and updates `next_stage` to `apply-code-restructure`.

## MS-9: Groupy restructures the code

1. The developer reviews the proposed code restructure (the `code_unit_type`, `move_to_file` and
   `ModuleNode.rename_to` fields), possibly editing it, and runs `groupy next`.
2. Groupy first validates the proposal again (as in MS-8), because the developer may have edited it. It does this
   before it changes anything, and also when the stage is resumed (the restructured modules have no proposal left,
   so they pass).
   1. The problems of MS-8 (a missing `code_unit_type`, a `move_to_file` that does not match the location rule of
      its `code_unit_type`, a target file that receives more than one public code unit, a method that cannot
      delegate, and a target package with the name of an existing module) raise `CodeRestructureHasProblemsError`,
      which lists them.
   2. Dependencies that violate the dependency direction are only reported (printed, as in MS-8), because the
      developer may have accepted them during the review.
3. Groupy applies the restructure with the refactoring policy, so that the imports and call sites in the
   code-base are updated (rope's "move module" and "move global" refactorings). This stage makes no Claude requests.
   1. The refactoring policy gets three more methods:
      1. `move_module(source_root, module_name, new_module_name)`: moves (renames) a module.
      2. `move_symbol(source_root, module_name, name, target_module_name)`: moves a top-level function, class or
         module-level variable to another module (creating the target module when it does not exist yet).
      3. `delegate_method(source_root, module_name, class_name, method_name, function_name)`: adds a top-level
         function `function_name` to the module, with the body of the method, where `self` is replaced by a
         parameter named after the class in snake_case (e.g. `book`). The body of the method becomes
         `return <function_name>(self, <arguments>)`.
   2. Groupy processes the chunks with `process_chunks`, and the modules of a chunk in sorted order. Per module:
      1. It first renames the module to its `rename_to` (with `move_module`), so that the code units that stay in
         the module end up in their final file.
      2. Then it lets each method with a `move_to_file` delegate to a new function (with `delegate_method`), and
         moves that function to the `move_to_file` (with `move_symbol`), together with the helper functions of the
         method.
         1. Rope adds a module-level import of the new function to the module of the class. Since the new function
            typically imports the class (e.g. a model), Groupy replaces this import by a local import inside the
            delegating method, to avoid a circular import. The delegating method then reads, e.g.:

            ```python
            def render(self):
                from myapp.reports.rules.render_report import render_report
                return render_report(self)
            ```

      3. Then it moves each top-level node with a `move_to_file` to that file (with `move_symbol`), in source order.
         1. The helper functions of a function move together with it, because they stay in the file of their
            parent function. A helper function node is moved after its parent, in the order of the node file.
         2. A class moves with its methods (including the delegating methods).
      4. It deletes a module that no longer contains any code (except an `__init__.py`), together with its node
         file.

   3. A target package that does not exist yet is created with an empty `__init__.py` (❔ or as a namespace
      package, without `__init__.py`, if rope supports that). The new `__init__.py` is a module like any other: it
      gets a module node file, it is listed in the `module_names` of its package node file, and it goes into the
      group of the module whose code unit caused the new package.
   4. ❔ A target package with the same name as an existing module that stays is rejected by the validation (see
      MS-8), and the developer resolves it by choosing another name. A later version may resolve such clashes
      itself.

4. Groupy updates the node files along with the source.
   1. A renamed module keeps its node file, which is renamed with it. Its `name` becomes the new path, and
      `rename_to` is cleared.
   2. A moved node (with its helper function nodes or method nodes) is removed from the node file of the source
      module and added to the node file of the target module (which Groupy creates when it does not exist), in
      source order. It keeps its analysis, and its `move_to_file` is cleared. Its `code_unit_type` is kept.
   3. For a delegating method, Groupy adds a function node for the new function to the node file of the target
      module, with the analysis of the method node (e.g. its concepts, responsibilities, steps and helper function
      nodes) and its `code_unit_type`. The method node stays in its class, with `Delegates to <function_name>` as its
      only responsibility, and without the other analysis, `code_unit_type` and `move_to_file`.
   4. Groupy updates the `module_names` of the package node files and creates the package node file of a new
      package (as in "Groupy sync").
   5. Groupy updates the group file: a module that is renamed keeps its group, and a new target module goes into
      the group of the module that its first code unit came from (see ./chunking.md, "Smart grouping", 4.1 and 4.2).
5. Groupy commits per module, with the message `apply-code-restructure: restructure <module>`, where `<module>` is
   the path of the module before the restructure. A module without `rename_to`, without delegating methods and
   without nodes to move gets no commit.
   1. A failed refactoring interrupts the stage and restores the working tree (as for any failed action). Since the
      `rename_to` and `move_to_file` fields of the committed modules are cleared, a resumed stage continues with the
      remaining modules.
6. Groupy does not try to fix circular imports or failing tests that the restructure causes. After the stage, the
   developer runs the tests and fixes the remaining problems (e.g. by moving a constant, or by adding a
   `typing.TYPE_CHECKING` guard).
7. Groupy commits the results and updates `next_stage` to `done`.
   1. `groupy next` with `next_stage` set to `done` prints `The refactoring is done.` and does nothing.
   2. ❔ A later version may start a new round (e.g. by running `groupy group` and `analyze-terminology` again on
      the restructured code).

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
   2. The analysis stages ignore the filter: the nesting of helper functions (MS-2), analyze-terminology (MS-3)
      and propose-module-layout (MS-8, which receives the summaries of all modules).
   3. The call graph and the context of the Claude requests (e.g. `caller_sources`) cover the entire target dir.
3. The proposals and refactorings only start from the nodes in modules that match the filter.
   1. identify-helper-functions only renames the helper functions in matching modules.
   2. propose-renamings only makes an RFA for chunks with matching modules, and only for those modules. Groupy
      rejects (as a conflict) a renaming that is proposed for a node in a module that does not match.
   3. extract-methods, propose-move-steps-to-caller and propose-code-restructure only take candidates from matching
      modules. As before, a chunk without candidates is finished without an RFA.
   4. The validation of the code restructure (MS-8 and MS-9) only checks the nodes in matching modules, so that a
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
