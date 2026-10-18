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
