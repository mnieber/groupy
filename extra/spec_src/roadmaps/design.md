# Rationale

## Groupy group

A call to `groupy group` recreates the group file, using the grouping strategy and the sizes in the config file, and
commits it. The developer uses it after changing the config file.

## Chunking the work

See ./chunking.md.

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
       to the caller(s) of the function.
   11. `extract_method_priority: Literal['high', 'medium', 'low', 'n/a'] | None`: `None` means that the
       priority is not set yet.
   12. `renamings: Dict[str, str]`
   13. `aliases: Dict[str, List[str]]`
   14. `abbreviations: Dict[str, str]`: abbreviations of local terms and of concepts without a glossary entry
   15. `helper_function_nodes: List[FunctionNode]`: the helper functions of this function. They are top-level
       functions in the Python code.
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

## Open points

1. Renamings: only symbols that are defined in the target code may be renamed, not the attributes, parameters and
   dict keys of external libraries. How do we ensure this?
   1. Maybe scramble the third party names to protect them from being renamed, and afterwards undo the scrambling.
   2. The scrambled name should contain a special token that allows Groupy/Claude to skip that name.

# Milestones

## MS-9: Groupy restructures the code

1. The developer reviews the proposed code restructure (the `code_unit_type`, `move_to_file` and
   `ModuleNode.rename_to` fields), possibly editing it, and runs `groupy next`.
2. Groupy first validates the proposal again (as in propose-code-restructure), because the developer may have edited it. It does this
   before it changes anything, and also when the stage is resumed (the restructured modules have no proposal left,
   so they pass).
   1. The problems of propose-code-restructure (a missing `code_unit_type`, a `move_to_file` that does not match the location rule of
      its `code_unit_type`, a target file that receives more than one public code unit, a method that cannot
      delegate, and a target package with the name of an existing module) raise `CodeRestructureHasProblemsError`,
      which lists them.
   2. Dependencies that violate the dependency direction are only reported (printed, as in propose-code-restructure), because the
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
   4. ❔ A target package with the same name as an existing module that stays is rejected by the validation (as in
      propose-code-restructure), and the developer resolves it by choosing another name. A later version may resolve such clashes
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
      package (as `groupy sync` does).
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
