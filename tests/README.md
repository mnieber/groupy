# Tests

All tests follow the workflow-test style: a workflow test per main scenario in `test_<feature>/`, and impl tests for
edge cases in `test_<feature>_impl/`. Each test package has its own `conftest.py` and Env.

## Fake policies

The tests don't call Claude or depend on rope's formatting. Instead, they use fake policies (in
`groupy_next_tests/fake_policies.py`).

1. The config file of a test refers to a function in that module that returns the fake policy (e.g.
   `get_fake_rfa_policy`), and the test scripts the fake before it runs `groupy next`.
2. Every request to Claude has a deterministic id, which the scripts use as a key (e.g.
   `identify-helper-functions/group-1/chunk-1` for an RFA, or
   `extract_method/myapp/books.py:create_book/_validate_title` for an RFR made by a callback).
3. The fakes:
   1. `FakeRfaPolicy` maps each RFA id onto a list of scripted callbacks (an action name plus its arguments). It
      runs these callbacks through the same callback dispatcher (`run_callback`) that the real policy uses.
   2. `FakeRfrPolicy` maps each RFR id onto a list of scripted steps: file writes (the new text of a module) and
      callbacks (run in RFR mode, so that they don't commit).
   3. `FakeRefactoringPolicy` subclasses `RopeRefactoringPolicy`: it refactors with rope, records the refactorings
      (`calls`) and raises `FakeRefactoringError` for the refactorings that a test lets fail
      (`failing_refactorings`, by module and name, with `@module` for `move_module`).
4. Every fake records the requests that it receives (id, prompt and context), so that tests can assert on the
   context that Groupy pre-computed (e.g. the call-graph view).
5. A request without a script raises `UnscriptedRequestError`, so that unexpected requests fail the test.
6. A fake is only added once a test needs it.

## Grouping

Tests use the `simple` grouping strategy with a large group and chunk size (set in the config file), so that the
chunk ids are predictable, except in the tests of the grouping strategies themselves.
