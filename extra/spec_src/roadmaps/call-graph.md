# Call graph

Breaker maintains a single call graph for the entire target code. It passes a filtered view of this graph to Claude,
and offers actions that allow Claude to query the graph for more information.

## Scope

1. The call graph covers the target code only.
   1. Test code is ignored when deciding on a refactoring. If a refactoring breaks a test, we do it anyway.
      The user will fix the tests later.
   2. Test code is: a module in a `tests` dir, a `test_*.py` or `*_test.py` module, and `conftest.py`.
   3. Calls of functions outside the target code (e.g. of the standard library) are not recorded.

## Contents

1. Each node in the call graph is a function or method, identified by its file path and its qualified name in the
   source (e.g. `reports/markdown_reports.py:get_api_usage` or `reports/markdown_reports.py:Report.save`).
   1. A function that is nested in the source is part of its enclosing function: its calls are calls of the
      enclosing function, and calls of the nested function are not recorded.
   2. Calls in module-level code are calls of `<file>:@module`.
   3. The call graph lists all functions and methods, also those without edges, so that a query can tell an unknown
      function from a function that is not called.
2. Each edge records:
   1. the caller and the callee.
   2. the location of the call (file path and line number).
   3. whether the edge is certain or uncertain.
      1. A call is uncertain when Breaker cannot determine which function is called (e.g. `obj.save()`, where the
         type of `obj` is unknown and subclasses may override `save`).
      2. For an uncertain call, there is an uncertain edge to every method with that name in the target code.
4. Breaker resolves calls as follows:
   1. A call of a function that is defined or imported in the module (also via its module, e.g.
      `titles.capitalize()`, and also when the other module imports it in turn) is a certain edge to that function.
   2. A call of a class is a certain edge to its `__init__` method.
   3. A call of a method of `self` is a certain edge to the method of the class. If a subclass in the target code
      overrides the method, then the edges to the method and to its overrides are uncertain.
3. The call graph is stored in `.breaker/call-graph.yaml`.
   1. It is derived from the target code, so Breaker can rebuild it at any time. It is not committed.

## Keeping the call graph up-to-date

1. Actions and RFRs change the code (e.g. extract-method adds functions, apply-move-steps-to-caller changes callers).
   Since chunks are usually not independent, each chunk must see the changes made by the previous chunks.
2. Before each chunk, Breaker rebuilds the call graph from scratch.
   1. Parsing the target code takes seconds, which is small compared to the time of a Claude request.
   2. If parsing turns out to be too slow, then Breaker can cache the parse result of each module (keyed on a
      hash of its contents) inside the build. This does not change how the call graph is used.

## The view that is passed to Claude

1. For each function in the chunk, Breaker passes its direct callers and callees (one level deep).
   1. Each caller and callee is labelled as: same module, other module in the chunk, or outside the chunk.
   2. Uncertain edges are marked as such.
   3. Each caller and callee is listed once, also when it is called several times.
2. Functions outside the chunk are given as their qualified name and a one-line responsibility (the first
   responsibility in their node file), without their source.
3. When a function has more callers than a maximum, Breaker passes a summary instead of the list of callers
   (e.g. "called from 37 places in 12 modules", where a place is a call).
4. Each RFA defines which view of the call graph it uses. For example:
   1. identify-helper-functions: callers only (mainly the number of callers, and whether they are in the same module).
   2. analyze-terminology: the callers and the callees.
   3. propose-move-steps-to-caller and apply-move-steps-to-caller: the callers of F, including their source (as
      `caller_sources`).
   4. propose-module-layout and propose-code-restructure: the dependencies between modules, aggregated from the
      function-level call graph.

## Query actions

1. Claude can use read-only actions to query the call graph beyond the view that it received:
   1. `get_callers(location)`
   2. `get_callees(location)`
   3. `get_source(location)`
2. This keeps the default context small, while still allowing Claude to follow the call graph further when its
   judgement requires it.
