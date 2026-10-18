import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s04_claude_refactors_code_in_an_rfr")


def run_scenario():
    r.claude = c.External.Actors.Claude
    r.rfr_policy = c.ClaudeRequests.Policies.RfrPolicy
    r.rfr = c.ClaudeRequests.Models.Rfr
    r.run_callback_action = c.ClaudeRequests.Actions.RunCallback
    r.commit_refactoring_action = c.Functions.Actions.CommitRefactoring

    with goal().refactor(r.target_code).with_an(r.rfr):

        # Request the refactoring
        with the(r.stage_action).calls(r.rfr_policy).with_an(r.rfr):
            it().sends(r.rfr).with_the(r.precomputed_context).to(r.claude)

        # Claude refactors the code
        with the(r.claude).refactors(r.target_code).for_each(r.refactoring):
            it().edits_the(r.source_files).directly()

            with the(r.claude).sends(r.callbacks).to(r.run_callback_action):
                it().raises(r.callback_not_allowed_error).if_the(
                    r.callback
                ).refactors_the_code()
                it().runs_the(r.node_file_edits).without_committing()

            with the(r.claude).calls(r.commit_refactoring_action).with_a(r.description):
                with it().checks_that_the(r.changed_modules).parse():
                    it().restores_the(r.working_tree).to_the(r.last_commit)
                    it().raises(r.refactoring_does_not_parse_error)
                it().commits_the(r.source_files).and_the(r.node_files).together()

        # Check that the work is committed
        with the(r.stage_action).checks_that_the(r.working_tree).is_clean():
            it().restores_the(r.working_tree).to_the(r.last_commit)
            it().raises(r.uncommitted_refactoring_error)


markdown_node = sunya.add_markdown_node(scenario, "Claude refactors code in an RFR")

markdown_node.markdown = """
Some refactorings cannot be done with a refactoring library (e.g. moving a step from a function to its callers).
For these, Groupy sends Claude a *request for refactoring* (RFR), in which Claude edits the source files directly.
While Claude refactors, the code may be temporarily broken, so an RFR follows other rules than an RFA: callbacks
don't commit, and Claude decides when a refactoring is complete by calling `commit_refactoring`.

An RFR is made by a stage (e.g. apply-move-steps-to-caller, with the id `<stage-id>/<chunk-id>`), or by a callback
that needs a refactoring (e.g. `extract_method`, with the id `<action>/<location>/<name>`). This scenario follows
an RFR made by a stage. An RFR made by a callback works the same, except that Claude does not call
`commit_refactoring`: the callback verifies the result itself (e.g. that the extracted function exists) and commits.

### Steps

#### It requests the refactoring

The stage calls the RFR policy (named in the config file) with an RFR, whose context contains the pre-computed
information that Claude needs (e.g. the sources of the modules and of the callers).</br>

#### Claude refactors the code

Claude edits the source files directly. It also updates the node files of the code that it changed (e.g. the steps
of the functions), using callbacks.</br>

- In an RFR, only the node file edits, the glossary edits and `commit_refactoring` are allowed. A callback that
  refactors the code (e.g. `extract_method`) is rejected with `CallbackNotAllowedError`, so that an RFR never
  starts another RFR. With the Claude policies, Claude can then continue without it.
- The callbacks don't commit, because the source may be half-refactored while they run.

When a refactoring is complete, Claude calls `commit_refactoring(description)`, typically once per refactoring.
It checks that the changed Python files parse, and commits the source files and the node files together with the
message `<stage-id>: <description>`. If a file does not parse, Groupy restores the working tree to the last commit
and raises `RefactoringDoesNotParseError`.</br>

#### It checks that the work is committed

After the RFR, the stage checks that the working tree is clean. Uncommitted changes mean that Claude did not
finish a refactoring, so Groupy restores the working tree to the last commit and raises
`UncommittedRefactoringError`.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Claude
    participant Stage as Stage (action)
    participant RfrPolicy as RfrPolicy (policy)
    participant RunCallback as RunCallback (action)
    participant CommitRefactoring as CommitRefactoring (action)

    Note over Stage,RfrPolicy: Request the refactoring
    Stage->>RfrPolicy: run(rfr with pre-computed context)
    RfrPolicy->>Claude: RFR

    loop for each refactoring
        Note over Claude,CommitRefactoring: Claude refactors the code
        Claude->>Claude: edit the source files
        Claude->>RunCallback: node file edits (no commit)
        RunCallback->>RunCallback: reject callbacks that refactor the code
        Claude->>CommitRefactoring: commit_refactoring(description)
        CommitRefactoring->>CommitRefactoring: check that the changed modules parse
        CommitRefactoring->>CommitRefactoring: commit source and node files
    end

    Note over Stage: Check that the work is committed
    Stage->>Stage: check: clean working tree
```
"""
