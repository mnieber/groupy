# Call graph

Breaker maintains a single call graph for the entire target code. It passes a filtered view of this graph to Claude,
and offers actions that allow Claude to query the graph for more information.

## Scope

1. The call graph covers the target code only.
   1. Test code is ignored when deciding on a refactoring. If a refactoring breaks a test, we do it anyway.
      The user will fix the tests later.

## Contents

1. Each node in the call graph is a function or method, identified by its file path and qualified name
   (using the same notation as the edit locations, e.g. `reports/markdown_reports.py:get_api_usage._get_api_url`).
2. Each edge records:
   1. the caller and the callee.
   2. the location of the call (file path and line number).
   3. whether the edge is certain or uncertain.
      1. A call is uncertain when Breaker cannot determine which function is called (e.g. `obj.save()`, where the
         type of `obj` is unknown and subclasses may override `save`).
3. The call graph is stored in `.breaker/call-graph.yaml`.
   1. It is derived from the target code, so Breaker can rebuild it at any time. It is not committed.

## Keeping the call graph up-to-date

1. Actions and RFRs change the code (e.g. extract-method adds functions, move-steps-to-caller changes callers).
   Since chunks are usually not independent, each chunk must see the changes made by the previous chunks.
2. Before each chunk, Breaker updates the call graph.
   1. Every edge originates in a file, so Breaker only needs to re-analyze the files that changed since the
      last update.

## The view that is passed to Claude

1. For each function in the chunk, Breaker passes its direct callers and callees (one level deep).
   1. Each caller and callee is labelled as: same module, other module in the chunk, or outside the chunk.
   2. Uncertain edges are marked as such.
2. Functions outside the chunk are given as their qualified name and a one-line responsibility (taken from their
   node file), without their source.
3. When a function has many callers, Breaker passes a summary instead of the full list
   (e.g. "called from 37 places in 12 modules").
4. Each RFA defines which view of the call graph it uses. For example:
   1. identify-helper-functions: callers only (mainly the number of callers, and whether they are in the same module).
   2. move-steps-to-caller: the callers of F, including their source.
   3. propose-module-layout and propose-code-restructure: the dependencies between modules, aggregated from the
      function-level call graph.

## Query actions

1. Claude can use read-only actions to query the call graph beyond the view that it received:
   1. `get_callers(location)`
   2. `get_callees(location)`
   3. `get_source(location)`
2. This keeps the default context small, while still allowing Claude to follow the call graph further when its
   judgement requires it.
