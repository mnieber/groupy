import sunya
from sunya import M as m
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s02_a_developer_runs_the_next_stage")


def run_scenario():
    r.developer = m.External.Actors.Developer
    r.claude = m.External.Actors.Claude
    r.groupy_cli = m.Runtime.Entrypoints.Groupy
    r.run_next_stage_action = m.Runtime.Actions.RunNextStage
    r.session = m.Sessions.Models.Session
    r.config = m.Sessions.Models.Config
    r.get_chunks_rule = m.Groups.Rules.GetChunks
    r.process_chunks_action = m.Sessions.Actions.ProcessChunks
    r.create_rfa_policy_rule = m.ClaudeRequests.Rules.CreateRfaPolicy
    r.rfa_policy = m.ClaudeRequests.Policies.RfaPolicy
    r.rfa = m.ClaudeRequests.Models.Rfa
    r.run_callback_action = m.ClaudeRequests.Actions.RunCallback
    r.find_node_rule = m.Nodes.Rules.FindNode

    with goal().run_the(r.next_stage).of_the(r.session):

        # Start the stage
        with the(r.developer).runs(r.groupy_cli).with_the(r.next_command):
            it().calls(r.run_next_stage_action)

        with the(r.run_next_stage_action).checks_the(r.preconditions):
            it().raises(r.no_session_error).if_there_is_no(r.session)
            it().raises(r.no_group_file_error).if_there_is_no(r.group_file)
            it().raises(r.dirty_working_tree_error).if_the(r.working_tree).is_not_clean()

        the(r.run_next_stage_action).calls_the(r.stage_action).for_the(r.next_stage).of_the(r.session)

        # Divide the work into chunks
        with the(r.stage_action).calls(r.get_chunks_rule).with_the(r.group_file).and_the(r.config):
            it().splits_each(r.group).into(r.chunks)
            it().returns(r.chunks)

        # Process each chunk
        with the(r.stage_action).calls(r.process_chunks_action).with_the(r.chunks):
            with it().calls_the(r.stage_action).for_each(r.chunk).that_is_not_finished():
                the(r.stage_action).calls(r.create_rfa_policy_rule).with_the(r.config)
                with the(r.stage_action).calls(r.rfa_policy).with_an(r.rfa):
                    it().sends(r.rfa).with_the(r.precomputed_context).to(r.claude)
                    with the(r.claude).sends(r.callbacks).to(r.run_callback_action):
                        with the(r.run_callback_action).runs_the(r.action).for_each(r.callback):
                            the(r.action).calls(r.find_node_rule).with_the(r.edit_location)
                            the(r.action).edits(r.node_files).or_the(r.target_code)
                        it().commits(r.changes).with_the(r.stage_id).and_the(r.callback_name)
            it().records(r.chunk).in_the(r.finished_chunks).of_the(r.session)
            it().commits(r.session_file)

        # Finish the stage
        with the(r.run_next_stage_action).finishes_the(r.stage):
            it().sets_the(r.next_stage).of_the(r.session).to_the(r.following_stage)
            it().clears_the(r.finished_chunks)
            it().commits(r.session_file)

        the(r.developer).reviews_the(r.commits).of_the(r.stage)


markdown_node = sunya.add_markdown_node(scenario, "A developer runs the next stage")

markdown_node.markdown = """
A session progresses through a fixed sequence of stages. Each `groupy next` runs one stage: the one in the
`next_stage` field of the session file. Groupy and Claude collaborate in a stage. Groupy divides the work into
chunks and sends a *request for actions* (RFA) per chunk to Claude. Claude answers with *callbacks*: requests to
Groupy to run one of its *actions*, which change the node files and/or the target code. Every change is
committed, so the developer can follow (and undo) what happened in the git history.

The stages are, in order: `identify-helper-functions`, `analyze-terminology`, `propose-renamings`,
`apply-renamings`, `extract-methods`, `propose-move-steps-to-caller`, `apply-move-steps-to-caller`,
`propose-module-layout`, `propose-code-restructure` and `apply-code-restructure`. Then `next_stage` is `done`, and
`groupy next` prints `The refactoring is done.` Most stages make an RFA per chunk; some make no Claude requests at
all, and some make a single request for the whole code-base.

### Steps

#### It checks the preconditions

`run_next_stage` refuses to run when there is no session (`NoSessionError`), when there is no group file
(`NoGroupFileError`), or when the working tree is not clean (`DirtyWorkingTreeError`). A clean working tree ensures
that every change in the stage ends up in a commit of the stage, and that Groupy can undo a failed action by
restoring the last commit.</br>
The config file is part of the session: a change to it must be committed before `groupy next` runs.</br>

#### It divides the work into chunks

`run_next_stage` calls the action of the stage. The stage loads the group file and splits each group into chunks
with `get_chunks`.</br>

- A *group* is a set of modules that belong together. The group file (`.groupy/groups.txt`) assigns each module (by
  its path, e.g. `myapp/books.py`) to a group. The grouping strategy in the config file decides how `groupy init`
  forms the groups:
  - `simple`: the modules, sorted by path, are divided into groups of at most `max_group_lines` lines.
  - `package` (the default): a group contains the entire file-tree of a sub-package of a top-level package (e.g.
    `myapp/books`); the modules directly in a top-level package form a group of their own.
- A *chunk* is the part of a group that is processed in one Claude request, with at most `max_chunk_lines` lines.
  Groupy keeps the modules of a package together in a chunk where possible. A chunk has a deterministic id, such
  as `group-2/chunk-1`: the same group file always gives the same chunks.
- The developer may edit the group file (e.g. to move a module to another group) before running a stage.

#### It processes each chunk

`process_chunks` calls the stage for each chunk that is not finished yet. Most stages make an RFA for the chunk,
with the id `<stage-id>/<chunk-id>` (e.g. `identify-helper-functions/group-1/chunk-1`), through the RFA policy that
the config file names.</br>

- The config file names each policy (the RFA, RFR, grouping and refactoring policy) by the import path of a
  callable that returns it, e.g. `groupy.claude_requests.policies.claude_rfa_policy:ClaudeRfaPolicy`. This lets the
  tests use fake policies that replay scripted callbacks.
- Groupy pre-computes everything that can be computed deterministically (e.g. the sources of the modules, the
  call graph and the glossary) and passes it in the context of the RFA. Claude spends its effort on judgement,
  not on facts that Groupy can compute.

Claude answers with callbacks, which `run_callback` dispatches to Groupy's actions.</br>

- All edits of node files are done by Groupy's actions, not by Claude directly. A callback identifies the node to
  edit by the module and an *edit location*: `@module` for the module node, `create_book` for a function,
  `Book.save` for a method, or `create_report._format_lines` for a helper function of a function. A location that
  is not a full qualified name must match the end of the qualified name of exactly one node (e.g. `save` is
  ambiguous when both `Book` and `Author` have a `save` method). `find_node` rejects unknown and ambiguous
  locations.
- After each action, Groupy commits with the message `<stage-id>: <callback name>`.
- When an action changes the code of a function, Claude updates the analysis of that function (e.g. its
  responsibilities and steps) in the same request, so that later stages don't work with stale data.

After the chunk, `process_chunks` records its RFA id in the `finished_chunks` field of the session file, and
commits with the message `<stage-id>: finish <chunk-id>`.</br>

#### It finishes the stage

Groupy sets `next_stage` to the stage that follows, clears `finished_chunks`, and commits with the message
`<stage-id>: finish the stage`. The developer reviews the result (e.g. the node files) before running the next
stage, and may edit it.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    actor Claude
    participant Groupy as Groupy (entrypoint)
    participant RunNextStage as RunNextStage (action)
    participant Stage as Stage (action)
    participant ProcessChunks as ProcessChunks (action)
    participant RfaPolicy as RfaPolicy (policy)
    participant RunCallback as RunCallback (action)

    Note over Developer,RunNextStage: Start the stage
    Developer->>Groupy: groupy next
    Groupy->>RunNextStage: run_next_stage()
    RunNextStage->>RunNextStage: check: session, group file, clean working tree
    RunNextStage->>Stage: run the stage in next_stage

    Note over Stage,ProcessChunks: Divide the work into chunks
    Stage->>Stage: get_chunks(group file, config)

    Stage->>ProcessChunks: process_chunks(chunks)
    loop for each chunk that is not finished
        ProcessChunks->>Stage: run chunk
        Stage->>RfaPolicy: run(rfa with pre-computed context)
        RfaPolicy->>Claude: RFA
        loop for each callback
            Claude->>RunCallback: callback(action, args)
            RunCallback->>RunCallback: run action (edit node files and/or code)
            RunCallback->>RunCallback: commit "<stage-id>: <callback name>"
        end
        ProcessChunks->>ProcessChunks: record chunk in finished_chunks
        ProcessChunks->>ProcessChunks: commit "<stage-id>: finish <chunk-id>"
    end

    Note over RunNextStage: Finish the stage
    RunNextStage->>RunNextStage: set next_stage, clear finished_chunks
    RunNextStage->>RunNextStage: commit "<stage-id>: finish the stage"
    Developer->>Developer: review the commits of the stage
```
"""
