# Scope

Breaker is a radical refactoring tool that takes a python code-base apart and rebuilds it.
Since it'sis expected to break the code,and the developer will need to help with
fixing the errors and testing.

# Milestones

## MS-1: A developer cleans up the terminology

1. The developer runs `breaker --init --branch-name=<branch-name>`
   1. Breaker will check that we are on a clean branch.
2. Breaker will create a new branch with --branch-name (which defaults to "breaker")
3. Breaker will create a source-map
   - Per python module it will create a ModuleNode that is added to a PackageNode.
   - Each ModuleNode contains a list of FunctionNodes.
4. Breaker will call Claude and ask it to annotate each python module.
   1. It will export each ModuleNode to a node file that is saved next to the original module filename.
      1. The node file is a yaml file with extension `.breaker.yaml` (that replaces the `.py` extension of the original filename)
      2. The node file contains:
         1. a `module_filename` field that points to the original filename.
         2. a `function_nodes` field
   2. It will commit these node files to the breaker branch
   3. For each node file, it will pass the node file to Claude and ask it to update it.
      1. Claude will update each function-node in `function_nodes`:
         1. It updates the `FunctionNode.concepts: Dict[str]` field
            1. Each string names a concept that is used in the function
            2. A concept is a term that helps explain the purpose and responsibilities of the function.
         2. It updates the `FunctionNode.local_terms: Dict[str]` field
            1. Each string names a local term that is used in the function
            2. A local term is a term that has local significance but is not significant in a wider context.
               1. E.g. `hash_tag` may be a local term if the function deals with hash_tags, but this term may not
                  be a meaningful concept within the larger context that is the code-base.
               2. Claude will use its own judgement to distinguish between concepts and local terms.
                  1. The distinction is important, because concepts are meaningfull when not everything is a concept.
         3. It updates the `FunctionNode.abbrevations: Dict[str]` field
            1. Each key contains either a concept or local term, and the value contains the abbrevation for that concept or term.
            2. Concepts and terms that are already short usually don't need an abbrevation.
         4. It updates the `FunctionNode.steps: List[str]` field
            1. Each string describes a step that the function takes to reach its goals.
            2. The description usually refers to concepts and local terms.
         5. It updates the `FunctionNode.responsibilities: List[str]` field.
            1. Each string describes a responsibility of the function
            2. The description usually refers to concepts and local terms.
         6. It updates the `FunctionNode.renamings: Dict[str, str]` field.
            1. Renamings are used to get rid of aliases.
            2. They can also be used to create shorter symbol names.
            3. The `renamings` field maps the old symbol name onto the new symbol name, using these guidelines:
               1. The new name maintains the meaning (e.g. plural stays plural).
                  1. E.g. if the function uses `outlier` and `outlier_point` as aliases then `new_outlier_points` will be renamed to `new_outliers` and `find_next_outlier_point` will be renamed to `find_next_outlier`.
               2. When the function uses multiple names for the same thing, then these aliases are replaced by the canonical name.
                  1. Typically, the canonical name will come from `FunctionNode.concepts`. However, also local terms should be renamed if they are aliases.
               3. Abbrevations may be used to keep the new name relatively short.
                  1. E.g. if `sf` is an abbrevation for `suitability_fraction` in the `abbrevations` field then Claude may add a renaming from `highest_suitability_fraction_by_plot_id` to `highest_sf_by_plot_id`
               4. Map types are renamed to `foo_by_bar` where `foo` is the value and `bar` is the key.
                  1. It's also possible to have `foo_by_bar_by_baz`, where `baz` is the key and `foo_by_bar` is the value.
