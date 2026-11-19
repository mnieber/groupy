import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s03_a_developer_resumes_an_interrupted_stage")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.groupy_cli = c.Runtime.Entrypoints.Groupy
    r.run_next_stage_action = c.Runtime.Actions.RunNextStage
    r.process_chunks_action = c.Sessions.Actions.ProcessChunks
    r.session = c.Sessions.Models.Session
    r.last_run = c.Sessions.Models.LastRun
    r.get_remaining_request_ids_rule = c.Sessions.Rules.GetRemainingRequestIds
    r.get_started_stage_tag_rule = c.Sessions.Rules.GetStartedStageTag
    r.get_stage_commit_count_rule = c.Sessions.Rules.GetStageCommitCount
    r.get_uncommitted_changes_rule = c.Sessions.Rules.GetUncommittedChanges
    r.reset_to_tag_action = c.Sessions.Actions.ResetToTag

    with goal().finish_a(r.stage).that_was_interrupted_by_an(r.error):

        # The stage is interrupted
        with the(r.developer).runs(r.groupy_cli).with_the(r.next_command):
            the(r.run_next_stage_action).tags_the(r.start).of_the(
                r.stage
            ).unless_it_resumes_the(r.stage)
            the(r.run_next_stage_action).records_a(r.last_run).that_is_running()
            with the(r.stage_action).processes_the(r.chunks):
                it().commits_each(r.action).that_succeeds()
                the(r.process_chunks_action).records_each(r.finished_chunk).in_the(
                    r.session
                )
                with the(r.action).fails().or_the(r.developer).presses_ctrl_c():
                    the(r.stage_action).restores_the(r.working_tree).to_the(
                        r.last_commit
                    )
                    the(r.process_chunks_action).attaches_the(r.request_id).to_the(
                        r.error
                    )
                    it().reraises_the(r.error)
            the(r.run_next_stage_action).records_the(r.last_run).as_interrupted()
            the(r.groupy_cli).prints_the(r.error).and_how_to_resume_the(r.stage)

        # The developer inspects the state
        with the(r.developer).runs(r.groupy_cli).with_the(r.status_command):
            it().prints_the(r.current_branch)
            it().prints_the(r.last_run)
            it().prints_whether_the_next_command_starts_or_resumes_the(r.stage)
            it().calls(r.get_remaining_request_ids_rule).to_print_the(
                r.remaining_chunks
            )
            it().prints_whether_the(r.working_tree).is_clean()

        # The developer repairs the state
        with the(r.developer).inspects_the(r.commits).and_the(r.node_files):
            it().repairs_the(r.cause).of_the(r.error)
            it().commits_the(r.repair)

        # Or the developer resets the stage
        with the(r.developer).runs(r.groupy_cli).with_the(r.reset_command).for_a(
            r.stage
        ):
            with it().calls(r.get_started_stage_tag_rule).for_the(r.stage):
                it().raises(r.stage_not_started_error).if_the(r.stage).has_no(
                    r.start_tag
                )
            with the(r.groupy_cli).says_what_will_be_lost():
                it().calls(r.get_stage_commit_count_rule).since_the(r.start_tag)
                it().calls(r.get_uncommitted_changes_rule)
            it().asks_for(r.confirmation).unless_the(r.force_option).is_given()
            with the(r.groupy_cli).calls(r.reset_to_tag_action).with_the(r.start_tag):
                it().resets_the(r.repo).to_the(r.start_tag)
                it().deletes_the(r.start_tags).of_the(r.stages).that_it_undoes()
                it().returns_the(r.previous_head)

        # The stage resumes
        with the(r.developer).runs(r.groupy_cli).with_the(r.next_command):
            the(r.run_next_stage_action).runs_the_same(r.stage).because_the(
                r.next_stage
            ).is_unchanged()
            with the(r.process_chunks_action).skips_the(r.finished_chunks):
                the(r.stage_action).derives_the(r.remaining_work).from_the(r.node_files)
                it().processes_the(r.remaining_work)
            the(r.run_next_stage_action).finishes_the(r.stage)


markdown_node = sunya.add_markdown_node(
    scenario, "A developer resumes an interrupted stage"
)

markdown_node.markdown = """
Since Groupy changes the code radically, a stage may stop halfway: a refactoring fails, a Claude
request fails, or Groupy detects a problem that Claude could not fix. Groupy is designed so that an interrupted
stage leaves a consistent state that the developer can inspect and repair, and so that running `groupy next`
again continues where the stage stopped, without repeating finished work. When the developer prefers to redo the
stage, `groupy reset` takes the session back to the start of the stage.

### Steps

#### The stage is interrupted

When `groupy next` starts a stage, it tags the commit at the start of the stage as
`groupy/<branch-name>/<stage-id>/start` (`groupy init` tags its commit as `groupy/<branch-name>/init`). When it resumes a stage, the tag already exists, and stays where
it is. The tag comes after the review edits that the developer committed after the previous stage.</br>
While a stage processes its chunks, each action that succeeds is committed, and each finished chunk is recorded in
the `finished_chunks` of the session file.</br>
When an action fails, Groupy restores the working tree to the last commit, which undoes the partial changes of
the action (e.g. a refactoring that changed some files but not all). Then it re-raises the error, which interrupts
the stage. The `next_stage` field of the session is unchanged. The same happens when the developer presses Ctrl+C.
With the Claude policies, Claude may first retry a failed callback once, and the stage is only interrupted when
the retry fails too.</br>

Groupy records the result of each `groupy next` in `.groupy/<branch-name>/last-run.yaml` (which is not committed): `running`
while the stage runs, then `finished` or `interrupted`, with the request id of the chunk that was running and the
error. A `running` result that is left behind means that the process crashed or was killed (the stage was
*aborted*). Then the working tree may not be clean.</br>

Instead of a traceback, `groupy next` prints the stage, the request id of the chunk (e.g.
`extract-methods/group-2/chunk-1`) and the error, and explains that the committed work is kept and how to resume.
With `-v`, it also prints the traceback. The errors that stop `groupy next` before the stage starts (e.g.
`DirtyWorkingTreeError`) come with a hint of their own.</br>

#### The developer inspects the state

`groupy status` prints the state of the session of the current branch, without changing anything:</br>

- the current branch;
- the result of the last `groupy next` (finished, interrupted or aborted), with the request id and the error;
- whether `groupy next` will start or resume the next stage (it resumes when the stage has a start tag), and for a
  stage that resumes, the finished chunks and the chunks that remain;
- whether the working tree is clean, and if not, a hint to commit, stash, or reset;
- the costs of Claude so far on the current branch, in USD, summed over the session logs. When the cost of a session is unknown
  (it was aborted, so its log has no result), the total is a lower bound (e.g. `at least 0.25 USD`).

#### The developer repairs the state

The working tree is clean, and the git history shows which actions succeeded. The developer finds the cause of the
error (e.g. a name clash, or a proposal that cannot be applied), repairs it (e.g. by editing the code or a node
file), and commits the repair.</br>

#### Or the developer resets the stage

Instead of repairing, the developer may run `groupy reset`, which resets the current branch to the start tag of the
current stage, so that the next `groupy next` runs the stage anew. This is also the way out after an aborted stage.
`groupy reset <stage-id>` resets to the start of an earlier stage, and `groupy reset init` to the start of the
session.</br>

- When the stage has not started (`get_started_stage_tag` raises a `StageNotStartedError`), there is nothing to
  reset.
- Otherwise, Groupy says what will be lost: the number of commits since the start tag (also the commits of Groupy,
  which cost Claude requests to redo), and the uncommitted changes, e.g. `all 3 commits since the start of
  identify-helper-functions as well as these uncommitted changes: ...`. Then it asks for confirmation (`--force`
  skips it). When nothing will be lost, it just says that the repo is already at the start of the stage.
- It deletes the start tags of the stages that it undoes, and prints the previous head, so that the developer can
  undo the reset with `git reset --hard <sha>`.

#### The stage resumes

The developer runs `groupy next`, which runs the same stage again.</br>

- `process_chunks` skips the chunks that are recorded in `finished_chunks`.
- Within the interrupted chunk, the stage derives its remaining work from the node files, which reflect the work
  that was already committed. For example, applying a renaming clears it from the node file, so the resumed
  apply-renamings stage only applies the renamings that are left. Likewise, a stage that works on candidates only
  takes the candidates that are not done yet.

When the stage is finished, Groupy moves on to the next stage, as usual.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Groupy as Groupy (entrypoint)
    participant RunNextStage as RunNextStage (action)
    participant Stage as Stage (action)
    participant ProcessChunks as ProcessChunks (action)
    participant ResetToTag as ResetToTag (action)

    Note over Developer,ProcessChunks: The stage is interrupted
    Developer->>Groupy: groupy next
    Groupy->>RunNextStage: run_next_stage()
    RunNextStage->>RunNextStage: tag the start of the stage, record the last run (running)
    RunNextStage->>Stage: run the stage
    Stage->>ProcessChunks: process_chunks(chunks)
    ProcessChunks->>ProcessChunks: commit actions, record finished chunks
    ProcessChunks->>Stage: run chunk
    Stage->>Stage: action fails (or Ctrl+C)
    Stage->>Stage: restore working tree to last commit
    Stage-->>RunNextStage: error (with the request id)
    RunNextStage->>RunNextStage: record the last run (interrupted)
    RunNextStage-->>Groupy: error
    Groupy-->>Developer: error, and how to resume

    Note over Developer,Groupy: The developer inspects the state
    Developer->>Groupy: groupy status
    Groupy-->>Developer: last run, next stage (start or resume), chunks, working tree

    alt The developer repairs the state
        Developer->>Developer: inspect commits and node files, repair, commit
    else The developer resets the stage
        Developer->>Groupy: groupy reset [stage-id | init]
        Groupy-->>Developer: the number of commits and the changes that will be lost
        Developer->>Groupy: confirm (or --force)
        Groupy->>ResetToTag: reset_to_tag(start tag)
        ResetToTag->>ResetToTag: git reset --hard, delete the tags of undone stages
        ResetToTag-->>Groupy: previous head
        Groupy-->>Developer: how to undo the reset
    end

    Note over Developer,ProcessChunks: The stage resumes
    Developer->>Groupy: groupy next
    Groupy->>RunNextStage: run_next_stage()
    RunNextStage->>Stage: run the same stage
    Stage->>ProcessChunks: process_chunks(chunks)
    loop for each chunk that is not finished
        ProcessChunks->>Stage: run chunk
        Stage->>Stage: derive remaining work from node files
    end
    RunNextStage->>RunNextStage: finish the stage
```
"""
