## Open points

1. Renamings: only symbols that are defined in the target code may be renamed, not the attributes, parameters and
   dict keys of external libraries. How do we ensure this?
   1. Maybe scramble the third party names to protect them from being renamed, and afterwards undo the scrambling.
   2. The scrambled name should contain a special token that allows Groupy/Claude to skip that name.
2. Should `done` be followed by a new round (e.g. `groupy group` and `analyze-terminology` on the restructured
   code)?
