## Guide the developer through the session

Today, `groupy next` prints nothing when a stage finishes (only `The refactoring is done.` when `next_stage` is
`done`), and an interrupted stage ends with a Python traceback. The scenarios say that the developer reviews the
result of each stage, and repairs the state after an interruption, but Groupy doesn't tell them what to review or
how to repair. This plan adds that guidance, a `groupy status` command and a `groupy reset` command.

A stage is *interrupted* when it stops on an error that Groupy caught (a failed action or refactoring, a failed
Claude request, or a check that Claude could not satisfy). Then the working tree is clean, and the developer can
repair and resume. A Ctrl+C that Groupy catches also interrupts the stage (see 4). A stage is *aborted* when the
process crashes or is killed. Then the working tree may be dirty, and the developer may prefer to redo the stage.

The tests check the printed reports by key fragments (e.g. the stage id, the request id, the error class and
message, and the phrases `finished`, `interrupted`, `aborted`, `will start`, `will resume`, `nothing to reset`),
not by exact lines, so that the wording can evolve.

1. When a stage finishes, `groupy next` prints a short report.
   1. The stage that finished, and the number of commits it made (e.g. `identify-helper-functions finished
      (14 commits)`).
   2. What to review, per stage (see 3), with the hint that the developer may edit and commit the node files before
      continuing.
   3. What the next `groupy next` will do: the name and a one-line description of the next stage, or that the
      refactoring is done.
   4. Messages that a stage already prints (e.g. the dependency violations of propose-code-restructure) come before
      the report.
2. When a stage is interrupted, `groupy next` prints the error instead of a traceback, and exits with code 1.
   `main()` still raises the error (so that tests can check its type); a wrapper `run()`, which is the console
   script in `pyproject.toml`, prints the error and returns the exit code.
   1. The stage, the request id of the chunk that was running (e.g. `extract-methods/group-2/chunk-1`), and the
      error class and message.
   2. That the working tree was restored to the last commit, so the changes that are committed (see `git log`) are
      kept, and the chunks in `finished_chunks` will be skipped.
   3. What to do: repair the cause (e.g. edit the code or a node file), commit the repair, and run `groupy next` to
      resume the stage.
   4. With `-v`, Groupy also prints the traceback.
   5. The precondition errors (`NoSessionError`, `NoGroupFileError`, `DirtyWorkingTreeError`) are printed the same
      way, with their own hint (e.g. "commit or stash your changes").
3. A stage guide (`sessions/rules/get_stage_guide.py`) returns, per stage, its description and what to review:
   1. identify-helper-functions: the nesting of helper functions (`helper_function_nodes`) and their new names.
   2. analyze-terminology: the glossary (give entries with the same name distinct names), and the concepts, local
      terms and abbreviations in the node files.
   3. propose-renamings: the proposed renamings in the node files.
   4. apply-renamings: the renamed code (`git log -p`).
   5. extract-methods: the extracted helper functions.
   6. propose-move-steps-to-caller: the proposed moves in the node files.
   7. apply-move-steps-to-caller: the moved steps in the code.
   8. propose-module-layout: the proposed modules in the package node files.
   9. propose-code-restructure: the proposal (`code_unit_type`, `move_to_file`, `rename_to`) and the printed
      dependency violations.
   10. apply-code-restructure: the restructured code.
4. On Ctrl+C, Groupy cleans up and reports the stage as interrupted.
   1. `run_callback` and the other places that restore the working tree on a failed action also do so on a
      `KeyboardInterrupt` (they catch `BaseException` instead of `Exception`), so that a half-done action doesn't
      leave a dirty working tree.
   2. The Claude policies terminate the `claude` process on Ctrl+C, and the request is treated as failed.
   3. `last-run.yaml` records the stage as interrupted, with `KeyboardInterrupt` as the error, and `run()` exits with
      code 130.
   4. After a crash or kill, the working tree may still be dirty. `groupy next` then refuses with
      `DirtyWorkingTreeError`, whose hint mentions `groupy reset`.
5. Groupy marks the start of each stage with a git tag, so that it can reset to it.
   1. `groupy init` tags its commit as `groupy/init`.
   2. `groupy next` tags `HEAD` as `groupy/<stage-id>/start` when it starts a stage (not when it resumes one, i.e.
      when the tag exists). The tag comes after the review edits that the developer committed after the previous
      stage, so that a reset keeps them.
6. `groupy reset` resets the session to the start of the current stage (the stage in `next_stage`).
   1. It lists what will be lost: uncommitted changes, and the commits since the tag that Groupy didn't make (e.g.
      repairs of the developer). It asks for confirmation (`--yes` skips it).
   2. It runs `git reset --hard` to the tag, and prints the previous `HEAD`, so that the reset can be undone (e.g.
      `git reset --hard <sha>`).
   3. When the current stage has not started (there is no tag), there is nothing to reset, and Groupy says so.
   4. `groupy reset --init` resets to `groupy/init` instead, which also resets `next_stage` to the first stage.
   5. A reset deletes the tags of the stages that it undoes, so that the next `groupy next` starts the stage anew.
7. `groupy status` prints the state of the session, without changing anything.
   1. The target dir and the stage that `groupy next` will run, and whether it will start or resume that stage
      (from the stage's start tag).
   2. The result of the last `groupy next`: finished, interrupted (with the request id and the error), aborted, or
      none yet.
   3. For a stage that will resume: the finished chunks and the chunks that remain.
   4. Whether the working tree is clean (`groupy next` refuses to run otherwise), and if not, a hint to commit,
      stash, or `groupy reset`.
   5. What to review for the last finished stage (the stage guide), so that the developer can see it again later.
8. To know the result of the last run, Groupy writes `.groupy/last-run.yaml`, with the fields `stage`, `result`
   (`running`, `finished` or `interrupted`), `request_id` and `error` (the error class and message).
   1. The file is excluded from git (like `call-graph.yaml`), so that writing it doesn't dirty the working tree
      after an interruption.
   2. `groupy next` writes the result `running` when it starts, and replaces it when it finishes or is interrupted.
      A `running` result that is left behind (and no `groupy next` runs) means that the stage was aborted.
   3. To know the request id of the running chunk, `run_unfinished_step` attaches it to the error (e.g. as a note
      on the exception) before re-raising.
9. Tests:
   1. `groupy_next_tests`: the report of an interrupted and of a finished stage (workflow test), the traceback with
      `-v`, the hint for a dirty working tree, the start tags, the clean working tree after a Ctrl+C in a callback,
      and a stage guide for every stage;
   2. `groupy_status_tests`: the progress of a session from start to a finished stage (workflow test), an aborted
      stage, `done`, and a repo without a session;
   3. `groupy_reset_tests`: a reset of a started stage that keeps the review edits before it (workflow test), a
      reset with `--init`, a stage that has not started, and the confirmation that lists what will be lost.
