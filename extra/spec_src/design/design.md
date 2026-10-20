# groupy branches

A repository can have several groupy branches, each with a session of its own. A *groupy branch* is a local branch
that has a session file. Groupy works on the current branch, so the developer may also switch between groupy
branches with `git checkout` (`groupy switch` adds a confirmation, see below). Groupy commands that need a session
refuse to run on a detached HEAD, since it has no branch name.

## Branch names

`groupy init` creates a new branch from the base branch. The base branch defaults to `main` (`--base=<branch>`
chooses another one), and is recorded in the `base_branch` field of the session file.
Without `--branch-name`, the branch is named `groupy-<N>`, where N is the highest number of the `groupy-<N>` dirs in
`.groupy` plus one (see Per-branch files). Since these dirs outlive a deleted branch (see `groupy abort`), Groupy
never reuses a branch name. The first branch is `groupy-1`.
With `--branch-name`, `groupy init` raises a `BranchExistsError` when the branch or its per-branch dir already exists.
When the base branch doesn't exist, it raises a `NoBaseBranchError` (with a hint to use `--base`).
Both checks come before any change to the repo. Since `groupy init` may run on a groupy branch, it no longer raises a
`SessionExistsError`.

`groupy init` may run on a groupy branch: the new branch starts from the base branch (or from a stage tag, see below),
not from the current branch. It requires a clean working tree (`DirtyWorkingTreeError`, with a hint to commit or
stash the changes). Unlike the commands that can lose work (see Losing work), it never offers to discard them.

## Starting from a stage

`groupy init --from-stage=<stage_name>` creates a new branch that starts at the start tag of <stage_name> on the
current branch. `groupy init --from-stage=<branch_name>/<stage_name>` takes the stage of another branch.
The new branch gets copies of the init tag and of the start tags of the stages up to and including <stage_name>, so
that `groupy reset` (including `groupy reset init`) works on it as usual. The session file and the config file are
those of the tagged commit, so the new branch has the same base branch as the branch that it starts from.
<stage_name> may also be `init`, which starts the new branch at the init commit of the branch.
The new branch is named like any new branch (see Branch names), and `groupy init --from-stage` asks to accept the
risks like any `groupy init`. It makes no commit: the branch starts at the tagged commit.
`--target-dir` is required without `--from-stage`, and not allowed with it (the target dir is in the session file).

- When the stage has not started (it has no start tag on the branch), it raises a `StageNotStartedError`.
- When the branch doesn't exist or has no session file (e.g. `--from-stage=<stage_name>` on the base branch), it
  raises a `NoGroupyBranchError`.

Both checks come before any change to the repo.

## Tags

The tags include the branch name: `groupy/<branch_name>/init` and `groupy/<branch_name>/<stage_id>/start`.
A groupy branch name never contains a `/`: `groupy init --branch-name` with a `/` is a usage error. This keeps an
argument `<branch_name>/<stage_name>` unambiguous, and the per-branch dirs flat.
Sessions that were started with the old tags (`groupy/init`, `groupy/<stage_id>/start`) are not supported.

## Per-branch files

The files that groupy does not commit (`last-run.yaml`, `call-graph.yaml`, `logs/` and `requests/`) live in
`.groupy/<branch_name>/`, so that branches don't share them. `groupy init` creates this dir. All dirs in `.groupy` are
excluded from git (with a single `/.groupy/*/` line in `info/exclude`), since the committed groupy files
(`session.yaml`, `config.yaml` and `groups.txt`) are not in a dir.

# groupy status

`groupy status` reports the state of the session of the current branch, starting with `Branch: <branch_name>`. The
costs are those of the current branch only (the logs in `.groupy/<branch_name>/logs`). On a branch without a
session, it raises a `NoSessionError`.

`groupy status --all` also works without a session (e.g. on the base branch). It prints a line per groupy branch
(the current one marked with `*`), e.g.

```
* groupy-1: next stage analyze-terminology, last run finished, costs 0.25 USD
  groupy-2: next stage group-modules, no run yet, costs at least 0.05 USD
  groupy-3 (aborted): costs 0.20 USD
Total costs: at least 0.50 USD
```

- The next stage is read from the session file of the branch (with `git show`, without a checkout).
- The last run is `finished`, `interrupted` or `aborted` (see `groupy status`), or `no run yet`.
- An aborted branch has a per-branch dir but no branch anymore. It is listed with its costs.
- The total is a lower bound (`at least`) when the costs of a branch are.

# Losing work: confirmation and --force

The commands that can lose work (`reset`, `switch`, `leave` and `abort`) work alike:

- When nothing will be lost, they just run.
- Otherwise, they list what will be lost, and ask for confirmation. `--force` skips the confirmation (this replaces
  `groupy reset --yes`).
- `reset` loses the commits since the tag that it resets to (also the ones that groupy made, which cost Claude
  requests to redo). There are none when the stage was interrupted before its first commit.
- `abort` loses all commits of the branch, so it always asks (a branch has at least the init commit).
- `switch` and `leave` only lose the uncommitted changes.

What will be lost is listed as
`all <nr-commits> commits <where> as well as these uncommitted changes: <changes>`, where <where> is e.g.
`since the start of extract-methods` or `on branch groupy-2`. The commits part is left out when there are no commits
to lose (always for `switch` and `leave`), and the uncommitted changes part is left out when the working tree is
clean. The uncommitted changes
include untracked files.

Uncommitted changes are discarded with `git reset --hard` and `git clean -fd`.

# groupy reset

`groupy reset` resets the current branch to the start of the current stage.
`groupy reset <stage_name>` resets the current branch to the start of <stage_name>.
`groupy reset init` resets the current branch to the start of the session (this replaces `groupy reset --init`).
When the stage has not started (it has no start tag), Groupy raises a `StageNotStartedError` (as `groupy init
--from-stage` does), which the entrypoint of `groupy reset` turns into the message
`There is nothing to reset: <stage> has not started.` (exit code 0).
When nothing will be lost (HEAD is at the tag and the working tree is clean), it prints
`The repo is already at the start of <stage>.`, without a confirmation or an undo hint.
Otherwise, the confirmation only gives the number of commits (it no longer lists the commits of the developer), e.g.
`all 3 commits since the start of identify-helper-functions as well as these uncommitted changes: <changes>`.
Afterwards, it prints the previous head, so that the developer can undo the reset, as it does today.

# groupy switch

`groupy switch <branch_name>` checks out another groupy branch. Uncommitted changes on the current branch are lost
(see Losing work). Afterwards, it prints e.g. `Switched to groupy-2 (next stage: analyze-terminology).`

- When the branch doesn't exist or has no session file (e.g. the base branch, which `groupy leave` returns to), it
  raises a `NoGroupyBranchError`.
- When the branch is the current branch, it prints `Already on groupy-2.` and changes nothing.

# groupy leave and groupy abort

`groupy leave` checks out the base branch (the `base_branch` of the session), and keeps the groupy branch.
Uncommitted changes are lost (see Losing work). Afterwards, it prints e.g. `Left groupy-2; it is kept. Back on main.`
On a branch without a session (e.g. the base branch), it raises a `NoSessionError`.

`groupy abort` checks out the base branch, and deletes the current groupy branch and its tags. All commits of the
branch and the uncommitted changes are lost (see Losing work).
`groupy abort <branch_name>` deletes another groupy branch and its tags, and stays on the current branch. Only the
commits of that branch are lost. When <branch_name> is the current branch, it is the same as `groupy abort`.

The confirmation counts the commits that are lost: those that are on no other branch (after `groupy init
--from-stage`, a branch shares its first commits with the branch that it started from). Uncommitted changes are only
lost when the aborted branch is the current branch.
`groupy abort` without a branch name on a branch without a session (e.g. the base branch) raises a `NoSessionError`.
`groupy abort <branch_name>` raises a `NoGroupyBranchError` when the branch doesn't exist or has no session file.

`groupy abort` keeps `.groupy/<branch_name>/`, so that the logs (and the costs) of the session stay available and
the branch name is not reused. It writes `.groupy/<branch_name>/undo-abort.sh`, a script with a `git branch <name>
<sha>` line for the branch and a `git tag <tag> <sha>` line per tag, that recreates the branch and its tags at the
commits where they were. Afterwards, it prints e.g.
`Aborted groupy-2. To undo, run: sh .groupy/groupy-2/undo-abort.sh`.
The script cannot restore the uncommitted changes.

# Error hints

Since being on the base branch is normal now, the hint of `NoSessionError` mentions `groupy switch <branch_name>`
(to continue a session) and `groupy init` (to start one).

# progress messages

`process_chunks` prints a progress message on stderr at the start of each chunk: the request id and the position of
the chunk among all chunks of the stage, e.g. `extract-methods/group-2/chunk-1 (3/12)`.
When a stage resumes, the finished chunks are skipped without a message, so the count starts later (e.g. at `(4/12)`).
A stage without chunks (`group-modules` and `propose-module-layout`) prints a single line with its stage id when it
starts, e.g. `propose-module-layout`.
The progress messages go to stderr, so that the report of `groupy next` (on stdout) stays apart.

# Detached HEAD

The groupy commands that need the name of the current branch (e.g. `groupy next` and `groupy status`) raise a
`DetachedHeadError` on a detached HEAD, with a hint to check out a groupy branch (e.g. with `groupy switch`).
