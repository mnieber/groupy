# Scope

Breaker is a radical refactoring tool that takes a python code-base apart and rebuilds it.
Since it is expected to break the code, the developer will need to help with
fixing the errors and testing.

# Glossary

- action: an operation - offered by Breaker - that changes nodes files and/or target code
- helper candidate: a function that might just be a helper function (e.g. because it's is only called by one other function in the same module)
- node file: a yaml file that captures the structure of a Python module or package
- request for actions (RFA): a request to Claude to analyze the node files and Python code and run actions
- request for refactoring (RFR): a request to Claude to refactor the Python code directly, without calling actions
- rope: a Python library that can perform refactorings
- stage id: the id of the current stage in the refactoring. The user call `breaker next` to move to the next stage.
- target code: the Python code that we're refactoring

# Rationale

## Breaker and Claude collaborate on editing node files and source files

Typically the user will initiate a Breaker session and call `breaker next` to perform the next stage in the refactoring.
Breaker will make RFAs that will cause Claude to run actions. These actions may update node files, or refactor the code
via rope, or trigger RFRs that cause Claude to refactor the Python code directly. Breaker commits the updated node files
and source files after each action; it groups the commits by prefixing the commit message with the stage id.

## Breaker sync

A call to `breaker sync` checks that the structure of each node file (it it exists) still reflects the structure of its related source file.
If there are differences then it reports them and asks the user to make edits to resolve the differences.

## Guidelines for the Claude requests

1. Breaker pre-computes everything that can be computed deterministically and passes it to Claude as context.
   1. E.g. the call graph (who calls which function, inside and outside the module), the source of the module,
      and the project glossary.
   2. Claude should spend its effort on judgement, not on facts that Breaker can compute.
2. All edits to node files are done by Breaker, not by Claude directly.
   The edit location is given as:
   - "@module": to indicate a change in the module node
   - \_get_api_url to indicate a change in the function node for that function
   - get_api_usage.\_get_api_url to disambiguate the location using the parent function name

## Example

An example node file is given in `./module_node_example.md`.

## Node file schema

1. A `ModuleNode` has the fields:
   1. `name: str`: the path of the module, relative to the source root.
   2. `rename_to: str | None`: the proposed new path.
   3. `concepts: List[str]`: concepts that apply to the entire module.
   4. `renamings: Dict[str, str]`: renamings that apply to the entire module.
   5. `function_nodes: List[FunctionNode]`: the top-level functions in the module.
   6. `class_nodes: List[ClassNode]`: the classes in the module.
   7. `variable_nodes: List[VariableNode]`: the module-level variables and constants.
2. A `FunctionNode` has the fields:
   1. `name: str`
   2. `rename_to: str | None`
   3. `move_to_file: str | None`: the proposed new path.
   4. `code_unit_type: str | None`: one of `action`, `rule`, `util`, `entrypoint`.
   5. `is_helper_candidate: bool`,
   6. `concepts: List[str]`
   7. `local_terms: List[str]`
   8. `responsibilities: List[str]`
   9. `steps: List[str]`
   10. `renamings: Dict[str, str]`
   11. `aliases: Dict[str, List[str]]`
   12. `abbreviations: Dict[str, str]`
   13. `helper_function_nodes: List[FunctionNode]`
3. A `ClassNode` has the fields:
   1. `name: str`
   2. `rename_to: str | None`
   3. `move_to_file: str | None`
   4. `code_unit_type: str | None`: one of `model`, `schema`, `enum`, `exception`, `other`.
   5. `concepts: List[str]`
   6. `responsibilities: List[str]`
   7. `renamings: Dict[str, str]`
   8. `method_nodes: List[FunctionNode]`
4. A `VariableNode` has the fields `name: str`, `rename_to: str | None` and `move_to_file: str | None`.
5. A `PackageNode` has the fields:
   1. `name: str`: the path of the package, relative to the source root.
   2. `module_names: List[str]`: the modules in the package.
   3. `proposed_modules: Dict[str, str]`: only used in the root package node file.
6. All paths in node files use the same notation: a file path relative to the source root
   (e.g. `myapp/reports/rules/create_user_stats_report.py`).

# Milestones

## MS-1: A developer initiates a breaker session

1. The developer runs `breaker init --branch-name=<branch-name>`
   1. Breaker will check that the working tree is clean.
   2. Breaker will check that there is no existing breaker-session.yaml file.
2. Breaker will create a new branch with --branch-name
   1. The branch-name defaults to "breaker"
3. Breaker will create a breaker-session.yaml file in the repository root.
   1. This session file contains a `next_stage` field that identifies the next stage of the refactoring
   2. It also contains the `target_dir` field (defaults to `src`) that identifies the target code.
4. Breaker will create node files that form a source map
   1. Per package it will create a package node file (called `package-node.breaker.yaml`) in the package root.
   2. Per python module it will create a module node file (with extension `.breaker.yaml`)
      1. Initially, each module node file just reflects the current contents of the module.
      2. Specifically, Breaker sets the initial contents of the `function_nodes`, `class_nodes` and
         `variable_nodes` fields.
5. Breaker creates a first commit with the session file and the new node files.
   1. It will set `next_stage` to `identify-helper-functions`.

## MS-2: Breaker identifies helper functions

1. The user calls `breaker next` to start the next stage.
2. Breaker computes the call graph and marks helper candidates.
3. Breaker will ask Claude to examine the FunctionNodes in the module node file.
   1. Claude decides which functions are helper functions and uses the move_function_to_parent action to nest them under their parent function.
      1. Not every helper candidate will necessarily turn out to be a helper function.
      2. A function that is called from outside the module is never a helper function.
   2. A function that is called by several functions in the module is not nested. It stays a top-level function
      (it later will typically become a rule or util).
4. Breaker renames the helper functions so that they start with an underscore (in the node file and in the source).
5. Breaker commits the results and updates `next_stage` to `analyze-terminology`.

## MS-3: Breaker analyzes the terminology

1. The developer runs `breaker next`
2. Breaker will pass each node file to Claude and ask it to update it (by running actions)
   1. Claude first updates the `ModuleNode.concepts: List[str]` field
      1. These are the concepts that apply to the module as a whole.
      2. They are recorded once at the module level to avoid repeating them in each FunctionNode.
         Concepts in `FunctionNode.concepts` are not necessarily less important.
   2. Claude will then update each function-node in `function_nodes` (and each class-node in `class_nodes`):
      1. It updates the `FunctionNode.concepts: List[str]` field
         1. Each string names a concept that is used in the function, and that is not already in `ModuleNode.concepts`.
         2. A concept is a term that helps explain the purpose and responsibilities of the function.
      2. It updates the `FunctionNode.local_terms: List[str]` field
         1. Each string names a local term that is used in the function
         2. A local term has local significance but is not significant in a wider context (and therefore is not a concept).
            1. E.g. `hash_tag` may be a local term if the function deals with hash_tags, but this term may not
               be a meaningful concept within the larger context that is the code-base.
            2. Claude will use its own judgement to distinguish between concepts and local terms.
               1. The distinction matters because concepts are only meaningful when not everything is a concept.
      3. It updates the `FunctionNode.responsibilities: List[str]` field.
         1. Each string describes a responsibility of the function
         2. The description usually refers to concepts and local terms.
         3. The responsibility to update (by the action) is identified by its list index
      4. It updates the `FunctionNode.steps: List[str]` field
         1. Each string describes a step that the function takes to meet its responsibilities.
         2. The description usually refers to concepts and local terms.
         3. The step to update (by the action) is identified by its list index
      5. When a function uses several names for the same concept or term (aliases), Claude records each concept or
         term once (using the name that it considers canonical) and lists the aliases in the
         `FunctionNode.aliases: Dict[str, List[str]]` field.
         1. E.g. `outlier: [outlier_point]`.
3. Breaker commits the results and updates `next_stage` to `create-glossary`.

## MS-4: Breaker creates a project glossary

1. The developer runs `breaker next`.
2. Breaker collects all concepts, aliases and local terms from all node files.
3. Breaker asks Claude to create a project glossary in `glossary.breaker.yaml`.
   1. The glossary contains, for each concept:
      1. the canonical name.
      2. the aliases that are used in the code-base for this concept.
      3. optionally, an abbreviation.
      4. a one-line description.
   2. When two concepts in different modules have the same meaning, Claude merges them into one glossary entry.
      1. One of the two concepts will become an alias.
   3. When the same name is used for different meanings in different modules, Claude records this as a conflict
      in the glossary, so that the developer can resolve it.
   4. Abbreviations may be used to keep names relatively short.
      1. Concepts that are already short usually don't need an abbreviation.
      2. Abbreviations are recorded in the glossary so that they can be applied consistently across the code-base.
         1. Once an abbreviation is introduced, we should always use exactly that abbreviation and no alternative abbreviations.
4. The developer reviews the glossary and may edit it.
5. Breaker commits the results and updates `next_stage` to `propose-renamings`.

## MS-5: Breaker proposes renamings that unify the terminology

1. The developer runs `breaker next`.
2. Breaker asks Claude to update the `FunctionNode.renamings: Dict[str, str]` field, using the glossary.
   1. Renamings are used to get rid of aliases.
   2. They can also be used to create shorter symbol names.
   3. The `renamings` field maps the old symbol name onto the new symbol name, using these guidelines:
      1. The entire symbol is stored as the key, not some part thereof (since there is no partial matching).
      2. The renamings in `FunctionNode.renamings` apply to symbols that are local to the function (variables and
         parameters). A renaming of the function itself is stored in `FunctionNode.rename_to`.
         Renamings of module-level symbols are stored in `ModuleNode.renamings`.
      3. When the function uses multiple names for the same thing, then these aliases are replaced by the canonical name.
         1. The canonical name comes from the glossary for concepts. Local terms should also be renamed if they are aliases.
         2. The new name maintains the meaning (e.g. plural stays plural).
            1. E.g. if the function uses `outlier` and `outlier_point` as aliases then `new_outlier_points` will be renamed to `new_outliers` and `find_next_outlier_point` will be renamed to `find_next_outlier`.
      4. Map types are renamed to `foo_by_bar` where `foo` is the value and `bar` is the key.
         1. It's also possible to have `foo_by_bar_by_baz`, where `baz` is the key and `foo_by_bar` is the value.
      5. Abbreviations from the glossary may be used to keep the new name relatively short.
         1. E.g. if `sf` is the abbreviation for `suitability_fraction` in the glossary then Claude may add a renaming from `highest_suitability_fraction_by_plot_id` to `highest_sf_by_plot_id`
         2. Local terms that need an abbreviation are recorded in `FunctionNode.abbreviations: Dict[str, str]`.
      6. Only symbols that are defined in the code-base are renamed. Attributes, parameters and dict-keys of external
         libraries are not renamed.
3. Breaker validates the proposed renamings.
   1. It reports a conflict when a new name clashes with an existing name in the same scope.
4. Breaker commits the results and updates `next_stage` to `apply-renamings`.

## MS-6: Breaker applies the unified terminology

1. The developer reviews all node files, possibly making edits to the proposed renamings and terminology.
2. When they are done, they run `breaker next`.
   1. Breaker will then apply the renamings (using the `rename_symbol` action), including in all call sites in the
      code-base.
3. Breaker commits the results and updates `next_stage` to `propose-module-layout`.

## MS-7: Breaker proposes to restructure the code

1. The developer runs `breaker next`.
2. Breaker asks Claude to propose the module layout of the application package.
   1. Claude receives the glossary and, for each module node file, the module concepts and the names and
      responsibilities of the top-level functions and classes.
   2. Claude runs an actio to record the list of proposed modules in the root package node file (in the
      `PackageNode.proposed_modules: Dict[str, str]` field), mapping each module name onto a one-line description.
   3. The developer reviews (and possibly edits) the proposed module layout.
3. Breaker commits the results and updates `next_stage` to `propose-code-restructure`.
4. The developer runs `breaker next`.
5. Breaker asks Claude to propose a structuring for each module node file, using the proposed module layout.
   1. For every top-level function, class and module-level variable, Claude sets the `code_unit_type` field
      and the `move_to_file` field.
      1. Claude sets `move_to_file` to null when the target is the current file, so that Breaker can check that
         every node was considered.
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
      7. Settings (including all reads of environment variables) go to the single file `<app_package>/settings.py`.
      8. Application entrypoints go to `<app_package>/runtime/entrypoints/<name>.py`.
         1. Entrypoints are usually registered in the `[project.scripts]` section of `pyproject.toml`, but this is outside of scope for Breaker.
      9. An exception class is defined in the action file that raises it.
         1. Only very generic exceptions that are shared by many actions go to `<module>/utils/exceptions.py`.
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
      2. Imports between modules must not create circular imports at runtime.
         1. Type references to models in other modules use a `typing.TYPE_CHECKING` guard.
7. Breaker validates the proposal.
   1. It checks that every top-level node has a `code_unit_type` and a `move_to_file`.
   2. It checks that each `move_to_file` path matches the location rule of its `code_unit_type`.
   3. It checks that no target file receives more than one public code unit (except for util group files,
      enums, schemas and the exception/form classes that go with an action).
   4. It uses the call graph to report dependencies that violate the dependency direction.
8. Breaker commits the results and updates `next_stage` to `apply-code-restructure`.
