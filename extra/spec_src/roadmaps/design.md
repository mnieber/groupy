# Scope

Breaker is a radical refactoring tool that takes a python code-base apart and rebuilds it.
Since it'sis expected to break the code,and the developer will need to help with
fixing the errors and testing.

## Breaker and Claude collaborate on editing node files and source files

Breaker will capture the structure of the Python files in so-called node (yaml) files.
It will:

- apply so-called `actions` to reorganize each module node file.
- make requests to Claude to either edit the node file directly or indirectly by executing an action.
  After updating a node file, Claude will also update the related Python module.
- commit the updated node files and source files after each round of updates.

## Example

An example node file is given in `./module_node_example.md`.

# Milestones

## MS-1: A developer initiates a breaker session

1. The developer runs `breaker --init --branch-name=<branch-name>`
   1. Breaker will check that we are on a clean branch.
2. Breaker will create a new branch with --branch-name
   1. The branch-name defaults to "breaker"
3. Breaker will create a breaker-session.yaml file in the current directory.
   1. This session file contains a `next_step` field that identifies the current step of the refactoring
   2. Initially, the `next_step` field is `create-node-files`.
4. Breaker will create node files that form a source map
   1. Per package it will create a package node file (called `package-node.breaker.yaml`) in the package root.
   2. Per python module it will create a module node file (with extension `.breaker.yaml`)
      1. Initially, each module node file just reflects the current contents of the module.
      2. Specifically, Breaker sets the initial contents of the `module_node.function_nodes` field.
   3. Breaker creates a first commit with the new node files.
      1. It will update `next_step` to `identify-helper-functions`.

## MS-2: Breaker identifies helper functions

1. The user calls `breaker next` to start the next step.
2. Breaker will ask Claude to examine the FunctionNodes in the module node file.
   1. Claude decides which functions are helper functions and uses the move_function_to_parent action to nest them under their parent function.
3. Breaker commits the results and updates `next_step` to `analyze-terminology`.

## MS-3: Breaker analyzes the terminology

1. The developer runs `breaker next`
2. Breaker will pass each node file to Claude and ask it to update it.
   1. Claude will update each function-node in `function_nodes`:
      1. It updates the `FunctionNode.concepts: List[str]` field
         1. Each string names a concept that is used in the function
         2. A concept is a term that helps explain the purpose and responsibilities of the function.
      2. It updates the `FunctionNode.local_terms: Dict[str]` field
         1. Each string names a local term that is used in the function
         2. A local term has local significance but is not significant in a wider context (and therefore is not a concept).
            1. E.g. `hash_tag` may be a local term if the function deals with hash_tags, but this term may not
               be a meaningful concept within the larger context that is the code-base.
            2. Claude will use its own judgement to distinguish between concepts and local terms.
               1. The distinction matters because concepts are only meaningful when not everything is a concept.
         3. It updates the `FunctionNode.responsibilities: List[str]` field.
            1. Each string describes a responsibility of the function
            2. The description usually refers to concepts and local terms.
         4. It updates the `FunctionNode.steps: List[str]` field
            1. Each string describes a step that the function takes to meet its responsibilities.
            2. The description usually refers to concepts and local terms.
3. Breaker commits the results and updates `next_step` to `propose-unified-terminology`.

## MS-4: Breaker proposes renamings that unify the terminology

1. The developer runs `breaker next`.
2. Breaker asks Claude to update the `FunctionNode.renamings: Dict[str, str]` field.
   1. Renamings are used to get rid of aliases.
   2. They can also be used to create shorter symbol names.
   3. The `renamings` field maps the old symbol name onto the new symbol name, using these guidelines:
      1. The entire symbol is stored as the key, not some part thereof (since there is no partial matching).
      2. When the function uses multiple names for the same thing, then these aliases are replaced by the canonical name.
         1. Typically, the canonical name will come from `FunctionNode.concepts`. However, also local terms should be renamed if they are aliases.
         2. The new name maintains the meaning (e.g. plural stays plural).
            1. E.g. if the function uses `outlier` and `outlier_point` as aliases then `new_outlier_points` will be renamed to `new_outliers` and `find_next_outlier_point` will be renamed to `find_next_outlier`.
      3. Map types are renamed to `foo_by_bar` where `foo` is the value and `bar` is the key.
         1. It's also possible to have `foo_by_bar_by_baz`, where `baz` is the key and `foo_by_bar` is the value.
      4. Abbrevations may be used to keep the new name relatively short.
         1. Claude will record abbreviations in the `FunctionNode.abbrevations: Dict[str]` field
         2. Concepts and terms that are already short usually don't need an abbrevation.
         3. Each key contains either a concept or local term, and the value contains its abbrevation.
         4. Abbreviations are recorded so that they can be applied consistently.
            1. Once an abbreviation is introduced, we should always use exactly that abbrevation and no alternative abbrevations.
            2. E.g. if `sf` is an abbrevation for `suitability_fraction` in the `abbrevations` field then Claude may add a renaming from `highest_suitability_fraction_by_plot_id` to `highest_sf_by_plot_id`
      5. Helper functions are renamed so that they start with an underscore.
3. Claude will move concepts that apply at the module-level from the FunctionNodes to `ModuleNode.concepts`.
   1. The related renamings are moved to `ModuleNode.renamings`.
   2. Moving concepts to `ModuleNode.concepts` is done to avoid repeating them in each FunctionNode. Concepts in `FunctionNode.concepts` are not necessarily less important.
4. The ModuleNode has a rename_to field that Claude can use to propose a new filename
   1. Typically, Claude will propose to rename the file after the main function in that file.
      1. If there are multiple candidate main function, then Claude picks the most suitable one.
         1. The other candidates will be moved out of the node file (and related Python file) later.
5. Breaker commits the results and updates `next_step` to `apply-unified-terminology`.

## MS-5: Breaker applies the unified terminology

1. The developer reviews all node files, possibly making edits to the proposed renamings and terminology.
2. When they are done, they run `breaker next`.
   1. Breaker will then apply the renaming.
3. Breaker commits the results and updates `next_step` to `propose-code-restructure`.

## MS-6: Breaker proposes to restructure the code

1. The developer runs `breaker next`.
2. Breaker asks Claude to propose a structuring by setting the `FunctionNode.move_to_file` field where applicable.
