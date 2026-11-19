## Open points

1. Renamings: only symbols that are defined in the target code may be renamed, not the attributes, parameters and
   dict keys of external libraries. How do we ensure this?
   1. Maybe scramble the third party names to protect them from being renamed, and afterwards undo the scrambling.
   2. The scrambled name should contain a special token that allows Groupy/Claude to skip that name.
2. Should `done` be followed by a new round (e.g. `groupy group` and `analyze-terminology` on the restructured
   code)?
3. Should Claude run the callbacks through an MCP server (`groupy mcp`, passed with `--mcp-config`) instead of the
   `groupy callback` command (see s16)? MCP gives Claude typed tool schemas for the callbacks, but the command is
   simpler and easier to test.
