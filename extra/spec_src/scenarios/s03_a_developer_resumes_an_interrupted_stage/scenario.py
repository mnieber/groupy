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

    with goal().finish_a(r.stage).that_was_interrupted_by_an(r.error):

        # The stage is interrupted
        with the(r.developer).runs(r.groupy_cli).with_the(r.next_command):
            with the(r.stage_action).processes_the(r.chunks):
                it().commits_each(r.action).that_succeeds()
                the(r.process_chunks_action).records_each(r.finished_chunk).in_the(
                    r.session
                )
                with the(r.action).fails():
                    the(r.stage_action).restores_the(r.working_tree).to_the(
                        r.last_commit
                    )
                    it().reraises_the(r.error)
            the(r.groupy_cli).reports_the(r.error).to_the(r.developer)

        # The developer repairs the state
        with the(r.developer).inspects_the(r.commits).and_the(r.node_files):
            it().repairs_the(r.cause).of_the(r.error)
            it().commits_the(r.repair)

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
again continues where the stage stopped, without repeating finished work.

### Steps

#### The stage is interrupted

While a stage processes its chunks, each action that succeeds is committed, and each finished chunk is recorded in
the `finished_chunks` of the session file.</br>
When an action fails, Groupy restores the working tree to the last commit, which undoes the partial changes of
the action (e.g. a refactoring that changed some files but not all). Then it re-raises the error, which interrupts
the stage. The `next_stage` field of the session is unchanged.</br>

#### The developer repairs the state

The working tree is clean, and the git history shows which actions succeeded. The developer finds the cause of the
error (e.g. a name clash, or a proposal that cannot be applied), repairs it (e.g. by editing the code or a node
file), and commits the repair.</br>

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

    Note over Developer,ProcessChunks: The stage is interrupted
    Developer->>Groupy: groupy next
    Groupy->>RunNextStage: run_next_stage()
    RunNextStage->>Stage: run the stage
    Stage->>ProcessChunks: process_chunks(chunks)
    ProcessChunks->>ProcessChunks: commit actions, record finished chunks
    ProcessChunks->>Stage: run chunk
    Stage->>Stage: action fails
    Stage->>Stage: restore working tree to last commit
    Stage-->>Groupy: error
    Groupy-->>Developer: error

    Note over Developer: The developer repairs the state
    Developer->>Developer: inspect commits and node files, repair, commit

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
