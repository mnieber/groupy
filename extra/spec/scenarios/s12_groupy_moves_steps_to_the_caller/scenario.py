import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s12_groupy_moves_steps_to_the_caller")


def run_scenario():
    r.claude = c.External.Actors.Claude
    r.developer = c.External.Actors.Developer
    r.groupy_cli = c.Runtime.Entrypoints.Groupy
    r.stage_action = c.Functions.Actions.ApplyMoveStepsToCaller
    r.rfr_policy = c.ClaudeRequests.Policies.RfrPolicy
    r.add_step_action = c.Functions.Actions.AddStep
    r.remove_step_action = c.Functions.Actions.RemoveStep
    r.remove_step_to_move_to_caller_action = (
        c.Functions.Actions.RemoveStepToMoveToCaller
    )
    r.commit_refactoring_action = c.Functions.Actions.CommitRefactoring

    with goal().move_the(r.proposed_steps).to_the(r.callers):
        the(r.developer).reviews_the(r.proposed_moves)
        the(r.developer).runs(r.groupy_cli).with_the(r.next_command)

        with the(r.stage_action).processes_each(r.chunk).with_(r.steps_to_move):

            # Claude moves the steps
            with the(r.stage_action).calls(r.rfr_policy).with_an(r.rfr).with_the(
                r.steps_to_move
            ).and_the(r.module_sources).and_the(r.caller_sources):
                with the(r.claude).moves_each(r.step).to_the(r.callers):
                    it().edits_the(r.function).and_its(r.callers)
                    it().calls(r.remove_step_action).for_the(r.function)
                    it().calls(r.add_step_action).for_each(r.caller)
                    it().calls(r.commit_refactoring_action)
                the(r.claude).calls(r.remove_step_to_move_to_caller_action).for_each(
                    r.step
                ).that_cannot_be_moved()

            # Check that every step is moved
            the(r.stage_action).calls(r.rfr_policy).with_a(r.follow_up_rfr).for_the(
                r.unapplied_moves
            )
            it().raises(r.unapplied_step_moves_error).if_moves_remain()


markdown_node = sunya.add_markdown_node(scenario, "Groupy moves steps to the caller")

markdown_node.markdown = """
In this stage, Claude applies the moves that the developer has reviewed: it moves each proposed step of a function
F to the callers of F, and updates the analysis of F and of its callers. Since this changes the source, the stage
makes an RFR rather than an RFA.

### Steps

#### Claude moves the steps

Groupy makes an RFR per chunk that has steps to move (with the id `apply-move-steps-to-caller/<chunk-id>`); a chunk
without steps to move is finished without an RFR. The context contains the steps to move (as lines
`<module>:<location>: <step>`), the sources of the modules of the chunk, and the source of each caller of a function
whose steps move (also in other modules).</br>
For each move, Claude edits F and its callers, removes the step from the steps of F (which also removes it from
`steps_to_move_to_caller`), adds it to the steps of the callers, and calls `commit_refactoring`. As in any RFR, the
callbacks don't commit by themselves, and work that is not committed is rejected.</br>
When Claude finds that a step cannot be moved after all, it withdraws the proposal with
`remove_step_to_move_to_caller`.</br>

#### It checks that every step is moved

After the RFR, Groupy makes one follow-up RFR for the steps that are still in `steps_to_move_to_caller`. Steps that
remain raise `UnappliedStepMovesError`, which interrupts the stage. The moves that were committed stay
committed.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Claude
    actor Developer
    participant Stage as ApplyMoveStepsToCaller (action)
    participant RfrPolicy as RfrPolicy (policy)
    participant NodeEdits as remove_step, add_step (actions)
    participant CommitRefactoring as CommitRefactoring (action)

    Developer->>Developer: review the proposed moves
    Developer->>Stage: groupy next

    loop for each chunk with steps to move
        Note over Claude,CommitRefactoring: Claude moves the steps
        Stage->>RfrPolicy: RFR(steps_to_move_to_caller, module_sources, caller_sources)
        RfrPolicy->>Claude: RFR
        loop for each step
            Claude->>Claude: edit F and its callers
            Claude->>NodeEdits: remove_step(F), add_step(caller)
            Claude->>CommitRefactoring: commit_refactoring(description)
        end

        Note over Stage,RfrPolicy: Check that every step is moved
        opt steps are not moved
            Stage->>RfrPolicy: follow-up RFR(unapplied moves)
        end
    end
```
"""
