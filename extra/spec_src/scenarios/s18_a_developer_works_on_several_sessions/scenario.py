import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s18_a_developer_works_on_several_sessions")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.groupy_cli = c.Runtime.Entrypoints.Groupy
    r.init_session_action = c.Sessions.Actions.InitSession
    r.discard_and_checkout_action = c.Sessions.Actions.DiscardAndCheckout
    r.abort_branch_action = c.Sessions.Actions.AbortBranch
    r.session = c.Sessions.Models.Session
    r.get_groupy_branch_session_rule = c.Sessions.Rules.GetGroupyBranchSession
    r.get_started_stage_tag_rule = c.Sessions.Rules.GetStartedStageTag
    r.get_branch_tags_rule = c.Sessions.Rules.GetBranchTags
    r.get_uncommitted_changes_rule = c.Sessions.Rules.GetUncommittedChanges
    r.get_lost_commit_count_rule = c.Sessions.Rules.GetLostCommitCount
    r.get_groupy_branches_rule = c.Sessions.Rules.GetGroupyBranches
    r.get_aborted_branches_rule = c.Sessions.Rules.GetAbortedBranches
    r.load_last_run_rule = c.Sessions.Rules.LoadLastRun
    r.get_claude_costs_rule = c.ClaudeRequests.Rules.GetClaudeCosts

    with goal().work_on_several(r.sessions).in_the(r.repo):

        # Start a session from a stage
        with the(r.developer).runs(r.groupy_cli).with_the(r.init_command).and_the(
            r.from_stage_option
        ):
            it().explains_the(r.risks).and_asks(r.developer).to_accept_them()
            with it().calls(r.init_session_action).with_the(r.stage).and_the(
                r.groupy_branch
            ):
                it().calls(r.get_groupy_branch_session_rule).for_the(r.groupy_branch)
                it().calls(r.get_started_stage_tag_rule).for_the(r.stage)
                it().creates_the(r.new_branch).at_the(r.start_tag)
                it().creates_the(r.per_branch_dir).of_the(r.new_branch)
                with it().copies_the(r.tags).of_the(r.groupy_branch):
                    it().calls(r.get_branch_tags_rule)
                    it().copies_the(r.init_tag).and_the(r.start_tags).up_to_the(r.stage)

        # Switch to another session
        with the(r.developer).runs(r.groupy_cli).with_the(r.switch_command):
            it().calls(r.get_groupy_branch_session_rule).for_the(r.groupy_branch)
            with it().says_what_will_be_lost():
                it().calls(r.get_uncommitted_changes_rule)
            it().asks_for(r.confirmation).unless_the(r.force_option).is_given()
            it().calls(r.discard_and_checkout_action).with_the(r.groupy_branch)
            it().prints_the(r.next_stage).of_the(r.session)

        # Leave the session
        with the(r.developer).runs(r.groupy_cli).with_the(r.leave_command):
            with it().says_what_will_be_lost():
                it().calls(r.get_uncommitted_changes_rule)
            it().asks_for(r.confirmation).unless_the(r.force_option).is_given()
            it().calls(r.discard_and_checkout_action).with_the(r.base_branch).of_the(
                r.session
            )

        # Abort a session
        with the(r.developer).runs(r.groupy_cli).with_the(r.abort_command):
            with it().says_what_will_be_lost():
                it().calls(r.get_lost_commit_count_rule).for_the(r.groupy_branch)
                it().calls(r.get_uncommitted_changes_rule).if_the(
                    r.groupy_branch
                ).is_the(r.current_branch)
            it().asks_for(r.confirmation).unless_the(r.force_option).is_given()
            with it().calls(r.abort_branch_action).with_the(r.groupy_branch):
                it().writes_the(r.undo_script).to_the(r.per_branch_dir)
                it().calls(r.discard_and_checkout_action).with_the(
                    r.base_branch
                ).if_the(r.groupy_branch).is_the(r.current_branch)
                it().deletes_the(r.groupy_branch).and_its(r.tags)
            it().prints_how_to_run_the(r.undo_script)

        # Report every session
        with the(r.developer).runs(r.groupy_cli).with_the(r.status_all_command):
            it().calls(r.get_groupy_branches_rule).and_the(r.get_aborted_branches_rule)
            with it().prints_a(r.line).for_each(r.groupy_branch):
                it().calls(r.get_groupy_branch_session_rule).to_print_the(r.next_stage)
                it().calls(r.load_last_run_rule).to_print_the(r.last_run)
                it().calls(r.get_claude_costs_rule).to_print_the(r.costs)
            it().prints_the(r.total_costs)


markdown_node = sunya.add_markdown_node(
    scenario, "A developer works on several sessions"
)

markdown_node.markdown = """
A repository can have several sessions, each on a branch of its own. A *groupy branch* is a local branch that has a
session file. Groupy works on the session of the current branch, so the developer may try another approach on a
new branch (e.g. another grouping strategy, or a stage that is redone), and keep the branches side by side.

### Steps

#### It starts a session from a stage

`groupy init --from-stage=<stage-id>` creates a new branch at the start tag of a stage of the current branch, so that
the developer can redo the stage on a new branch. `--from-stage=<branch-name>/<stage-id>` takes the stage of another
groupy branch, and `init` instead of a stage id takes the start of the session.</br>

- `init_session` raises a `NoGroupyBranchError` when the branch is not a groupy branch, and a
  `StageNotStartedError` when the stage has not started.
- The new branch starts at the tagged commit, without a commit of its own, so its session file and config file are
  those of the stage, with the same target dir and base branch. The new branch is named like any new branch, and
  gets a per-branch dir.
- Groupy copies the init tag and the start tags of the stages up to and including the stage to the new branch,
  so that `groupy next` resumes the stage there, and `groupy reset` works as usual.

#### It switches to another session

`groupy switch <branch-name>` checks out another groupy branch (`get_groupy_branch_session` raises a
`NoGroupyBranchError` for a branch without a session), and prints its next stage. Since `groupy switch` loses the
uncommitted changes, it first says what will be lost and asks for confirmation, like `groupy reset` (`--force` skips
it). The per-branch dirs are excluded from git, so they are kept.</br>

#### It leaves the session

`groupy leave` checks out the base branch of the session, and keeps the groupy branch, so that the developer can
come back to it with `groupy switch`. Like `groupy switch`, it asks before it discards uncommitted changes.</br>

#### It aborts a session

`groupy abort` deletes the current groupy branch and its tags, and goes back to the base branch.
`groupy abort <branch-name>` deletes another groupy branch, and stays on the current branch.</br>

- Groupy says what will be lost and asks for confirmation. The commits that are lost are those that are on no
  other branch (`get_lost_commit_count`): a branch that started from a stage shares its first commits with the
  branch that it started from. The uncommitted changes are only lost when the aborted branch is the current branch.
- `abort_branch` writes an undo script (`.groupy/<branch-name>/undo-abort.sh`) that recreates the branch and its
  tags at the commits where they were. It cannot restore the uncommitted changes.
- The per-branch dir is kept, so that the logs (and the costs) of the session stay available, and the branch name
  is not reused.

#### It reports every session

`groupy status --all` prints a line per groupy branch, also when the current branch has no session (e.g. the base
branch). The line gives the next stage (read from the session file of the branch, without a checkout), the result
of the last run, and the costs of Claude. The current branch is marked with `*`. An aborted branch has a per-branch
dir but no branch anymore: it is listed with its costs. The total of the costs comes last, e.g.

```
* groupy-1: next stage analyze-terminology, last run finished, costs 0.25 USD
  groupy-2: next stage group-modules, no run yet, costs at least 0.05 USD
  groupy-3 (aborted): costs 0.20 USD
Total costs: at least 0.50 USD
```

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Groupy as Groupy (entrypoint)
    participant InitSession as InitSession (action)
    participant DiscardAndCheckout as DiscardAndCheckout (action)
    participant AbortBranch as AbortBranch (action)

    Note over Developer,InitSession: Start a session from a stage
    Developer->>Groupy: groupy init --from-stage=[branch-name/]stage-id
    Groupy->>InitSession: init_session(form)
    InitSession->>InitSession: check: groupy branch, started stage
    InitSession->>InitSession: create branch at the start tag, and its per-branch dir
    InitSession->>InitSession: copy the tags up to the stage

    Note over Developer,DiscardAndCheckout: Switch to another session, or leave it
    Developer->>Groupy: groupy switch branch-name (or groupy leave)
    Groupy-->>Developer: the uncommitted changes that will be lost
    Developer->>Groupy: confirm (or --force)
    Groupy->>DiscardAndCheckout: discard_and_checkout(groupy branch, or base branch)

    Note over Developer,AbortBranch: Abort a session
    Developer->>Groupy: groupy abort [branch-name]
    Groupy-->>Developer: the commits and changes that will be lost
    Developer->>Groupy: confirm (or --force)
    Groupy->>AbortBranch: abort_branch(branch-name)
    AbortBranch->>AbortBranch: write the undo script
    AbortBranch->>DiscardAndCheckout: discard_and_checkout(base branch), if current
    AbortBranch->>AbortBranch: delete the branch and its tags
    Groupy-->>Developer: how to undo the abort

    Note over Developer,Groupy: Report every session
    Developer->>Groupy: groupy status --all
    Groupy-->>Developer: a line per groupy branch, and the total costs
```
"""
