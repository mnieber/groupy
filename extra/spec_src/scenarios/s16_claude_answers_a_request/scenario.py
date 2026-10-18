import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s16_claude_answers_a_request")


def run_scenario():
    r.claude = c.External.Actors.Claude
    r.groupy_cli = c.Runtime.Entrypoints.Groupy
    r.rfa_policy = c.ClaudeRequests.Policies.ClaudeRfaPolicy
    r.rfr_policy = c.ClaudeRequests.Policies.ClaudeRfrPolicy
    r.run_claude_action = c.ClaudeRequests.Actions.RunClaude
    r.get_claude_model_rule = c.ClaudeRequests.Rules.GetClaudeModel
    r.get_preamble_rule = c.ClaudeRequests.Rules.GetPreamble
    r.run_requested_callback_action = c.ClaudeRequests.Actions.RunRequestedCallback
    r.run_callback_action = c.ClaudeRequests.Actions.RunCallback
    r.config = c.Sessions.Models.Config

    with goal().answer_a(r.request).using(r.claude):

        # Start Claude
        with the(r.stage_action).calls_the(r.rfa_policy).or_the(r.rfr_policy):
            it().calls(r.run_claude_action).with_the(r.request)

        with the(r.run_claude_action).starts(r.claude):
            it().writes_the(r.context).to_the(r.context_file)
            it().calls(r.get_claude_model_rule).with_the(r.config)
            it().calls(r.get_preamble_rule).to_explain_the(r.callbacks)
            it().runs_claude_in_headless_mode().with_the(r.prompt).and_the(r.preamble)
            it().restricts_the(r.tools).that(r.claude).may_use()

        # Claude runs callbacks
        with the(r.claude).runs(r.groupy_cli).with_the(r.callback_command):
            the(r.groupy_cli).calls(r.run_requested_callback_action)
            with the(r.run_requested_callback_action).calls(r.run_callback_action):
                it().prints_the(r.result).to(r.claude)

        # A failed callback may be retried once
        with the(r.callback).fails():
            the(r.run_requested_callback_action).records_the(r.failed_callback)
            the(r.groupy_cli).offers(r.claude).to_retry_the(r.callback).once()
            with the(r.retry).fails():
                the(r.run_requested_callback_action).records_the(r.error).in_the(
                    r.request_dir
                )
                the(r.groupy_cli).tells(r.claude).to_stop()
                it().refuses_the(r.later_callbacks).of_the(r.request)

        # End the request
        with the(r.run_claude_action).waits_until(r.claude).stops():
            it().keeps_the(r.session_log)
            with it().finds_the(r.error).of_a(r.failed_retry):
                it().restores_the(r.working_tree)
                it().raises_the(r.error)
            it().raises(r.claude_request_error).if_claude_fails()


markdown_node = sunya.add_markdown_node(scenario, "Claude answers a request")

markdown_node.markdown = """
The stages send their requests (RFAs and RFRs) to the policies that the config file names. The default policies,
`ClaudeRfaPolicy` and `ClaudeRfrPolicy`, let Claude Code answer each request in a session of its own, in which
Claude runs Groupy's callbacks with a command. This scenario describes how a request is answered; the scenarios of
the stages describe what Claude does in it. The tests use fake policies instead (see s02).

### Steps

#### It starts Claude

The policy calls `run_claude` with the request, which runs `claude -p` in the repo dir. Every request gets a fresh
session, so that a request only depends on its prompt and its context.</br>

- The context of the request is written to `.groupy/requests/<request-id>/context.yaml`, instead of being inlined in
  the prompt.
- The prompt is the prompt of the request, followed by a *preamble* (`get_preamble`) that explains where the target
  code and the context are, how to run a callback, how to name a node (its location), and which callbacks exist,
  with their arguments.
- The model is the `claude_model` of the config file, unless `claude_model_by_stage` gives the current stage a model
  of its own (`get_claude_model`). An empty model is the default model of Claude Code.
- In an RFA, Claude may only read files and run callbacks. In an RFR, it may also edit files directly (see s04).
- The output of the session is kept in `.groupy/logs/<request-id>.jsonl`, for debugging. Neither the request dir nor
  the logs are committed.

#### Claude runs callbacks

Claude runs each callback with `groupy callback <name> --args '<json>'`, which calls `run_requested_callback`.
That action runs the callback with `run_callback` (in RFR mode for an RFR), just as the fake policies do, so the
callbacks commit as described in s02 and s04. The command prints the result of the callback (e.g. the source of a
function for `get_source`), or `OK`. It always runs in the repo dir, also when Claude has changed its directory.
</br>

#### A failed callback may be retried once

When a callback fails, the command prints the error, and offers Claude to correct the call and retry it once. A
failed callback is recorded in the request dir (`failed-callback.yaml`), and the next callback that succeeds clears
it.</br>
When the next callback fails too, the request ends: Groupy records the error (`error.yaml`), tells Claude to stop,
and refuses every later callback of the request. Claude stops by ending its answer. If it doesn't, Groupy stops
`claude` after a few minutes.</br>

#### It ends the request

When `claude` exits, `run_claude` checks the request dir. After a failed retry, it restores the working tree (which
also undoes the files that Claude edited after the failure in an RFR) and raises the error of the retry, which
interrupts the stage (see s03). When `claude` itself fails (e.g. it cannot reach Claude), it raises
`ClaudeRequestError` with the end of the error output. On Ctrl+C, Groupy stops `claude` and restores the working
tree.</br>
Afterwards, the stage checks the result as usual, e.g. with a follow-up request (see s07).</br>

### Diagram

```mermaid
sequenceDiagram
    actor Claude
    participant Stage as Stage (action)
    participant Policy as ClaudeRfaPolicy / ClaudeRfrPolicy (policy)
    participant RunClaude as RunClaude (action)
    participant Groupy as Groupy (entrypoint)
    participant RunRequestedCallback as RunRequestedCallback (action)
    participant RunCallback as RunCallback (action)

    Note over Stage,RunClaude: Start Claude
    Stage->>Policy: run(request)
    Policy->>RunClaude: run_claude(request, model)
    RunClaude->>RunClaude: write the context file, get the model and the preamble
    RunClaude->>Claude: claude -p (prompt + preamble)

    loop for each callback
        Note over Claude,RunCallback: Claude runs callbacks
        Claude->>Groupy: groupy callback <name> --args <json>
        Groupy->>RunRequestedCallback: run_requested_callback(callback)
        RunRequestedCallback->>RunCallback: run_callback(callback)
        alt the callback succeeds
            Groupy-->>Claude: result or OK
        else it fails for the first time
            RunRequestedCallback->>RunRequestedCallback: record the failed callback
            Groupy-->>Claude: error, retry once
        else the retry fails too
            RunRequestedCallback->>RunRequestedCallback: record the error
            Groupy-->>Claude: error, stop
        end
    end

    Note over RunClaude: End the request
    Claude-->>RunClaude: exits
    RunClaude->>RunClaude: keep the session log
    alt a retry failed
        RunClaude->>RunClaude: restore the working tree
        RunClaude-->>Stage: the error of the retry
    else claude failed
        RunClaude-->>Stage: ClaudeRequestError
    end
```
"""
