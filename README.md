# groupy

**Take a Python code-base apart, and put it back together the way you would have written it.**

Groupy is a refactoring tool for Python code-bases that have grown without a plan. It works with Claude to
analyze every function and class, unify the terminology, split functions that do too much, and restructure the
code into feature packages of actions, rules, utils and models. Groupy and Claude do the heavy lifting, and you
review every step.

```
$ groupy init --target-dir=myapp
$ groupy next        # group-modules
$ groupy next        # identify-helper-functions
$ groupy next        # analyze-terminology
...
$ groupy next        # apply-code-restructure
The refactoring is done.
```

> **Groupy is experimental.** It changes code radically, it will break things, and its stages are still being
> tuned. I'm using it to refactor existing code-bases, and I expect to improve it as I learn from that work. Use
> it on a branch you are prepared to throw away, and expect its behaviour (and the format of its files) to change
> between versions.

---

## Why groupy

### It refactors the whole code-base, not one function at a time

IDE refactorings and code assistants work on what you point them at. Groupy works on the entire target code, in a
fixed sequence of *stages*, where each stage builds on the previous one:

| Stage | What happens |
|---|---|
| `group-modules` | divide the modules into groups that are processed together |
| `identify-helper-functions` | find the functions that only exist to serve one parent, and nest them under it |
| `analyze-terminology` | record the concepts, responsibilities and steps of every function, and build a glossary |
| `propose-renamings` / `apply-renamings` | replace aliases of the same concept by one canonical name |
| `extract-methods` | split functions that have too many responsibilities |
| `propose-move-steps-to-caller` / `apply-move-steps-to-caller` | move steps that belong to the caller |
| `propose-module-layout` | propose the feature packages of the application |
| `propose-code-restructure` / `apply-code-restructure` | classify every code unit, and move it to its own file |

At the end, a function such as `create_chapter` lives in `myapp/chapters/actions/create_chapter.py`, a dataclass
in `myapp/chapters/models/`, and dependencies point in one direction: entrypoints → actions → rules → utils.

### Claude judges, Groupy computes

Groupy pre-computes everything that can be computed deterministically: the call graph, the sources of the
modules and their callers, the glossary so far. Claude spends its effort on judgement: is this function really
a helper? Are `outlier` and `outlier_point` the same concept? Is this a rule or an action?

Claude never edits Groupy's files directly. It answers with *callbacks* (`groupy callback set_concept ...`) that
Groupy validates and commits. Mechanical refactorings, such as renames and moves, are done with
[rope](https://github.com/python-rope/rope), so that imports and call sites in the rest of the code-base follow.
Claude only edits source files itself where no refactoring library can help (e.g. extracting a method, or moving
a step to the callers), and then Groupy checks that the result parses before it commits.

### You review, and stay in control

Every stage that changes the design comes in two halves: a *propose* stage that records the plan in yaml *node
files* next to your modules, and an *apply* stage that carries it out. Between them, you review the proposal and
edit it where you disagree:

```yaml
# myapp/books.py.groupy.yaml, after propose-renamings
module_node:
  name: myapp/books.py
  function_nodes:
    - name: create_book
      concepts:
        title: the name of a book
      aliases:
        title: [book_title]
      responsibilities:
        - create a book with a normalized title
      renamings:
        book_title: title
      helper_function_nodes:
        - name: _normalize_title
```

The node files are the record of what was analyzed, proposed and done. They live in the repo, so you can read
them, diff them and change them like any other file.

### Every change is a commit

Groupy works on a branch of its own, and commits after every action, with messages such as
`apply-renamings: apply the renamings of myapp/books.py`. You can follow what happened in `git log`, and undo any
of it.

When a stage fails halfway (a rename clashes, or Claude cannot finish a request), Groupy restores the last commit
and stops. `groupy status` tells you where you are, and after you repair the problem, `groupy next` continues
where it stopped, without repeating finished work. If you'd rather redo the stage, `groupy reset` takes you back
to its start.

### Refactor part of the code-base

`--exclude=myapp/reports/**` marks files as *passive*: the stages don't analyze or refactor them, but they stay in
the call graph and in the context of Claude, and their call sites are updated when an active function is renamed
or moved. That way you can refactor one feature area at a time.

### Try another approach side by side

A repository can have several sessions, each on its own groupy branch. `groupy init --from-stage=propose-renamings`
starts a new session at the start of a stage of the current one, so you can redo that stage with another model
or config and compare the results. `groupy status --all` lists every session, with what it cost.

---

## Features at a glance

**Sessions**

- `groupy init` creates a groupy branch from the base branch (`--base`, default `main`), with a session file and a
  config file in `.groupy/`.
- `groupy next` runs the next stage; `groupy status` shows the last run, the remaining chunks and the costs.
- `groupy reset [<stage-id> | init]` returns to the start of a stage, and says what will be lost first.
- `groupy sync` updates the node files after you edited the code by hand.
- `groupy switch`, `groupy leave` and `groupy abort` manage several sessions; an abort writes an undo script.
- Groupy refuses to run on a dirty working tree, so every change ends up in a commit.

**Working with Claude**

- Each request runs in a fresh, headless Claude Code session (`claude -p`), with its context in a file.
- Requests for actions (RFA) may only read files and run callbacks; requests for refactoring (RFR) may also edit
  source files.
- A failed callback may be retried once; then the request stops and the working tree is restored.
- Follow-up requests list what is still missing (unanalyzed nodes, renaming conflicts, restructure problems).
- `claude_model` and `claude_model_by_stage` in the config file choose the model per stage.
- The session logs are kept per branch, and the costs are summed in `groupy status`.

**Analysis and refactoring**

- A call graph of the target code, with certain and uncertain edges, rebuilt for every chunk.
- Helper functions, concepts, local terms, aliases, abbreviations, responsibilities and steps per function.
- A project glossary (`glossary.groupy.yaml`) that guides the choice of names.
- Renamings that are checked for clashes, duplicates and cycles before they are applied.
- Methods that delegate to new actions, rules or utils, so that their call sites don't change.
- Dependency violations (e.g. a rule that calls an action) are reported for review.

**Configuration**

- Grouping strategy (`package` or `simple`), `max_group_lines` and `max_chunk_lines`.
- Every policy (RFA, RFR, grouping, refactoring) is named by an import path, so it can be replaced; the tests use
  fake policies that replay scripted callbacks.

---

## Before you start

Groupy runs Claude Code, which costs money, and it rewrites your code. `groupy init` explains the risks and asks
you to accept them:

- Groupy may introduce errors. You remain fully responsible for the correctness of the code, and review all
  changes. After the last stage, expect to fix circular imports and failing tests by hand.
- The costs that `groupy status` shows are an estimate, without any guarantee. Check the actual usage with
  Anthropic.
- Groupy is provided as is, without warranty of any kind.

## Install

```
pip install git+https://github.com/mnieber/groupy.git
```

Groupy needs Python 3, git, and [Claude Code](https://claude.com/claude-code) (the `claude` command) on your
path. Run it from the root of the repository that contains the target code.

## Documentation

The behaviour of Groupy is described in scenarios, one per command or stage:

- [A developer starts a session](doc/spec/scenarios/s01_a_developer_starts_a_session.md)
- [A developer runs the next stage](doc/spec/scenarios/s02_a_developer_runs_the_next_stage.md)
- [A developer resumes an interrupted stage](doc/spec/scenarios/s03_a_developer_resumes_an_interrupted_stage.md)
- [A developer syncs the node files](doc/spec/scenarios/s05_a_developer_syncs_the_node_files.md)
- [A developer works on several sessions](doc/spec/scenarios/s18_a_developer_works_on_several_sessions.md)
- [Claude refactors code in an RFR](doc/spec/scenarios/s04_claude_refactors_code_in_an_rfr.md)
- [Claude answers a request](doc/spec/scenarios/s16_claude_answers_a_request.md)
- The stages: [group-modules](doc/spec/scenarios/s17_groupy_groups_the_modules.md),
  [identify-helper-functions](doc/spec/scenarios/s06_groupy_identifies_helper_functions.md),
  [analyze-terminology](doc/spec/scenarios/s07_groupy_analyzes_the_terminology.md),
  [propose-renamings](doc/spec/scenarios/s08_groupy_proposes_renamings.md),
  [apply-renamings](doc/spec/scenarios/s09_groupy_applies_renamings.md),
  [extract-methods](doc/spec/scenarios/s10_groupy_extracts_methods.md),
  [propose-move-steps-to-caller](doc/spec/scenarios/s11_groupy_proposes_to_move_steps_to_the_caller.md),
  [apply-move-steps-to-caller](doc/spec/scenarios/s12_groupy_moves_steps_to_the_caller.md),
  [propose-module-layout](doc/spec/scenarios/s13_groupy_proposes_the_module_layout.md),
  [propose-code-restructure](doc/spec/scenarios/s14_groupy_proposes_the_code_restructure.md),
  [apply-code-restructure](doc/spec/scenarios/s15_groupy_restructures_the_code.md)

## License

MIT
