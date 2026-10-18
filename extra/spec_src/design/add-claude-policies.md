## Add the Claude policies

The tests run Groupy with `FakeRfaPolicy` and `FakeRfrPolicy` (`tests/groupy_next_tests/fake_policies.py`), but the
default config refers to `claude_requests.policies.claude_rfa_policy:ClaudeRfaPolicy` and
`claude_requests.policies.claude_rfr_policy:ClaudeRfrPolicy`, which don't exist yet. This plan adds them, so that
`groupy next` can be used on a real code-base.

1. The policies run Claude Code in headless mode (`claude -p`) as a subprocess, in the repo dir.
   1. One subprocess per request, so that every RFA and RFR is a fresh Claude session (as the scenarios assume).
   2. The prompt that Groupy sends is the `prompt` of the request, followed by a fixed preamble that explains how to
      read the context and how to run callbacks (see 2 and 3).
   3. A non-zero exit code of `claude` raises `ClaudeRequestError` (with the request id and the tail of stderr). The
      stage then fails like it does for any other error, so that `groupy next` can resume it.
   4. The output of the session (`--output-format stream-json`) is written to `.groupy/logs/<request-id>.jsonl`, for
      debugging. `groupy init` excludes `.groupy/logs/` from git, like `call-graph.yaml`.
   5. Support for an MCP server might be done in the future (not now).
2. The context of a request is written to a file instead of being inlined in the prompt.
   1. Groupy writes `request.context` as yaml to `.groupy/requests/<request-id>/context.yaml` (also excluded from
      git), and the preamble tells Claude to read it.
   2. Values in the context that are models (e.g. the `CallGraphView` of identify-helper-functions) are converted to
      plain dicts with a shared util (`claude_requests/utils/to_plain_data.py`).
3. Claude runs callbacks with a new CLI command: `groupy callback <name> --args '<json>'`.
   1. It calls `run_callback(Callback(name, args), in_rfr=...)` and prints the result as yaml (for the queries
      `get_callers`, `get_callees` and `get_source`), or `OK`.
   2. On an error, it prints the error class and message and exits with code 1. See 4 for what happens next.
   3. The RFR policy sets the env var `GROUPY_IN_RFR=1` for the subprocess, and the command passes
      `in_rfr=True` when it is set. This keeps `CallbackNotAllowedError` working without trusting Claude to pass a
      flag.
4. Claude may retry a failed callback once. When the retry fails too (two callbacks fail in a row), the request
   ends, and the stage is interrupted, as the specs require (s03, and e.g.
   `test_apply_move_steps_to_caller_rejects_a_refactoring_callback`, which expects `CallbackNotAllowedError` from
   `groupy next` with the fake policies). Groupy doesn't kill `claude`, but asks Claude to stop, so that the session
   ends normally and its log is complete.
   1. A failed callback writes `.groupy/requests/<request-id>/failed-callback.yaml` (the callback and the error),
      and prints the error with the offer to retry once. The next callback that succeeds removes the file.
   2. When a callback fails while that file exists, it writes the error to `error.yaml` (the import path of the
      exception class and the message), and prints a fixed instruction, e.g. "Stop processing this request now:
      don't run more callbacks or edit files, and end your answer." `run_callback` has already restored the
      working tree (in an RFA).
   3. When the error file exists, every later callback of the request runs nothing, and prints the same
      instruction.
   4. In headless mode, the `claude` process exits when Claude ends its answer. Then the policy restores the working
      tree (which discards the files that Claude edited directly after the failure, in an RFR), recreates the
      exception from the error file, and raises it.
   5. As a safety net, the policy terminates `claude` when it is still running some time (e.g. 5 minutes) after the
      error file was written. If Claude turns out to ignore the instruction, a Claude Code hook (passed with
      `--settings`) can block every tool call once the error file exists.
   6. On Ctrl+C, the policy terminates `claude` and re-raises the `KeyboardInterrupt`, so that the stage is
      interrupted like on a failed callback (see s03).
5. The policies restrict the tools that Claude may use (`--allowedTools`).
   1. `ClaudeRfaPolicy`: `Read`, `Glob`, `Grep` and `Bash(groupy callback:*)`. Claude does not edit files in an RFA;
      all changes go through callbacks.
   2. `ClaudeRfrPolicy`: the same, plus `Edit` and `Write`, since Claude edits the source files in an RFR.
6. The config gets a `claude_model: str` field (default: empty, which means the default model of Claude Code), that
   the policies pass with `--model`. The field `claude_model_by_stage` (a map from stage id to model, default empty)
   gives a stage its own model, e.g. Sonnet for the stages that need more judgement (analyze-terminology,
   propose-renamings and propose-code-restructure, see `e2e-test-plan.md`). The policies look up the stage in the
   session, so that an RFR made by a callback (e.g. `extract_method`) uses the model of its stage. Both policies share the code that builds and runs the command
   (`claude_requests/utils/run_claude.py`).
7. Tests (in a new `claude_policies_tests` package) don't call the real Claude. They put a fake `claude` executable
   on the `PATH` that records its arguments and runs a scripted list of `groupy callback` commands, and check that:
   1. the context file, the preamble, the allowed tools and the model are passed;
   2. callbacks in an RFR run without committing, and a refactoring callback is rejected;
   3. a failed callback may be retried once; after a failed retry, later callbacks are refused with the stop
      instruction, the working tree is restored, and the policy raises the error of the retry;
   4. a failing `claude` raises `ClaudeRequestError`.
8. Out of scope: `ClaudeGroupingPolicy` (the default `grouping_policy`) belongs to smart grouping
   (`add-a-smart-grouping-policy.md`). Until then, the default `grouping_strategy: package` does not use it.

### Implementation notes

The policies are implemented, and the e2e tests pass (see `e2e-test-plan.md`). Differences with the plan above:

1. The shared code is the action `claude_requests/actions/run_claude.py` (not a util), since it restores the
   working tree and raises the error of a failed callback.
2. Besides `--allowedTools`, the command passes `--tools` (the available tools), `--permission-mode dontAsk` (deny
   without asking), `--strict-mcp-config` (no MCP servers) and `--no-session-persistence`. Claude Code still lets
   read-only shell commands (e.g. `cd`, `find`, `cat`) through.
3. Claude may `cd` in its shell, so the policy passes the repo dir in `GROUPY_REPO_DIR`, and `groupy callback`
   runs there. The env vars are read in `groupy/settings.py`.
4. The preamble names the target dir, explains the locations (also of classes and variables), and says that
   every argument without a default is required (null for an empty value).
5. The e2e tests showed gaps in some stages, which are fixed: propose-move-steps-to-caller passes the steps of the
   candidates (`candidate_steps`), the apply-move-steps-to-caller prompt says that `remove_step` also removes the
   step to move, and the extract-methods prompt says that a nested helper function keeps its name until Groupy
   renames it.
6. The `claude_policies_tests` (item 7) use a fake `claude` executable (`fake_claude.py`) that runs scripted
   steps: `groupy callback` commands and file writes.

### Open questions
