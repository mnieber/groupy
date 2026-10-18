## E2E tests with real Claude

The tests in `tests/` replace Claude with fake policies. The e2e tests in `e2e_tests/` run the stages with the real
Claude policies (see `add-claude-policies.md`), to check that the prompts, the context and the callbacks work
together. They are written before the policies exist, and pass once the policies are implemented.

### Principles

1. One workflow test per stage that calls Claude, and no test of a full session. Each test prepares the session at
   its stage (with `set_next_stage` and pre-filled node files, as the tests in `tests/` do), and runs a single
   `groupy next`.
2. The tests are cheap: the target code is a single small module (10 to 30 lines) in a single chunk, so that each
   test makes one Claude request (plus a possible follow-up request).
3. The tests are opt-in. `e2e_tests/conftest.py` skips them unless the env var `GROUPY_E2E=1` is set and `claude`
   is on the `PATH`, so that `pytest` (also `pytest e2e_tests`) never calls Claude by accident. They run with
   `GROUPY_E2E=1 pytest e2e_tests`.
4. The config of a test uses the real RFA and RFR policies (the defaults), the `simple` grouping strategy with
   large groups and chunks, and `claude_model: haiku`. A test that turns out to need a stronger model sets
   `claude_model` itself, and the plan records why.
5. Claude's answers are not deterministic, so the tests only assert what any reasonable answer has in common:
   1. the stage finished (`next_stage` moved on), and the working tree is clean;
   2. the node files load;
   3. the snippet has an obvious answer (e.g. a helper function with a single caller), and the test checks that
      answer, but not the wording (e.g. that a responsibility exists, not what it says);
   4. after a refactoring by Claude, the code parses, and a small behaviour check (calling the refactored function
      in a subprocess) gives the same result as before.
6. The e2e tests don't repeat what the normal tests already cover (e.g. the commits of a stage, the renaming of
   helper functions, or the context of a request), unless repeating it is useful. They focus on Claude's judgement,
   and on whether the real flow works end to end.
7. When a test fails, its message points to the session logs (`.groupy/logs/<request-id>.jsonl`), and pytest keeps
   the repo dir (`tmp_path`), so that the developer can see what Claude did.
8. The e2e Env reuses the Envs of `tests/` where it can (e.g. `sessions_tests.groupy_test_env.TestEnv`), so that
   `e2e_tests/conftest.py` adds `tests/` to `sys.path`.

### Batches

1. Infrastructure, and identify-helper-functions (RFA).
   1. Snippet: `create_book` calls `_normalize_title` (its only caller) and `make_slug`, which is also called by
      `create_chapter`.
   2. Asserts: the stage finished with a clean working tree; `_normalize_title` is nested under `create_book`;
      `make_slug` is not nested. Claude doesn't change the source in this stage, so there is no behaviour check.
   3. Exercises: `e2e_tests/conftest.py` (opt-in, `sys.path`, the context fixture, pointing to the logs),
      `e2e_tests/stage_tests/e2e_test_env.py` (a session with only the modules of the test, and a config with the
      real policies and `claude_model`).
2. analyze-terminology (RFA, with the glossary) and propose-renamings (RFA).
   1. analyze-terminology snippet: functions that use the abbreviation `qty` and the aliases `book` and
      `volume` for the same concept. Asserts: the stage finished (so every node has an `extract_method_priority`),
      the module has concepts, every function has responsibilities and steps, `volume` is recorded as an alias and
      `qty` as an abbreviation, and the glossary has an entry for the concept.
   2. propose-renamings snippet: `stats.py` uses `outlier_point` as an alias of `outlier`, which the glossary and
      the node files record. Asserts: `is_outlier_point` gets a `rename_to`, and `new_outlier_points` a renaming,
      both without `outlier_point`; the source is unchanged.
   3. Exercises: the glossary and the loaded nodes in the e2e Env.
3. extract-methods (RFA, and an RFR per `extract_method` callback).
   1. Snippet: a function with two clearly separate parts (e.g. it validates the input, and then formats a report),
      pre-filled with `extract_method_priority: high`.
   2. Asserts: the module has a new function that the original function calls, the candidate has priority `n/a`,
      and the behaviour check passes.
   3. Exercises: the behaviour check in the e2e Env (first needed here).
4. propose-move-steps-to-caller (RFA) and apply-move-steps-to-caller (RFR).
   1. propose snippet: `format_invoice`, whose only caller is `print_invoice`, marks the invoice as printed, which
      clearly belongs to the caller. The steps of both functions are pre-filled. Asserts: exactly that step is
      recorded as a step to move, and the source is unchanged.
   2. apply snippet: the same code, with the step to move pre-filled. Asserts: the marking is gone from
      `format_invoice` and present in `print_invoice` (in the source and in the steps), the stage finished with a
      clean working tree (so the work was committed with `commit_refactoring`), and the behaviour check passes.
5. propose-module-layout (RFA) and propose-code-restructure (RFA).
   1. propose-module-layout snippet: two modules about books and authors, with pre-filled module concepts,
      responsibilities and glossary. Asserts: there are proposed modules, each is a package under `myapp`, and there
      is a package for books and one for authors.
   2. propose-code-restructure snippet: `books.py` with a model (`Book`), a rule (`is_valid_isbn`) and an action
      (`create_book`), and the proposed module `myapp/books`. Asserts: the proposal has no problems (the stage
      finished), the three code unit types are recognized, and each moves to a file in `myapp/books/`.

apply-renamings and apply-code-restructure don't call Claude (they refactor with rope), so they have no e2e test.

### Models

All tests pass with the real policies (`GROUPY_E2E=1 pytest e2e_tests`, about 3 minutes). Haiku is good enough for
identify-helper-functions, extract-methods, the move-steps stages and propose-module-layout. Three tests use Sonnet:

1. analyze-terminology: Haiku uses activities as concepts (e.g. `customer_lookup`) and misuses the glossary
   callbacks.
2. propose-renamings: Haiku confuses `set_renaming` and `set_rename_to`.
3. propose-code-restructure: Haiku ignores the proposed modules (e.g. it proposes `myapp/models/book.py`).

Changes to the snippets after the first runs: analyze-terminology uses `client` as an alias of `customer` (Claude
rightly read `volume` as a copy of a book), and doesn't check abbreviations (they are introduced for long terms,
not found in the code); propose-code-restructure uses a rule with clear business logic (`can_borrow_book`), in a
module (`library.py`) that doesn't clash with the proposed package `myapp/books`.

### Open points

1. A test may be flaky when Claude sometimes makes another reasonable choice. Then we relax the assert (or make
   the snippet more obvious), rather than retry the test.
