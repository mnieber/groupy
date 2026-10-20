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
With `--branch-name`, `groupy init` raises an error when the branch or its per-branch dir already exists.

`groupy init` may run on a groupy branch: the new branch starts from the base branch (or from a stage tag, see below),
not from the current branch. It requires a clean working tree (`DirtyWorkingTreeError`, with a hint to commit or
stash the changes). Unlike the commands that can lose work (see Losing work), it never offers to discard them.

## Starting from a stage

`groupy init --from-stage=<stage_name>` creates a new branch that starts at the start tag of <stage_name> on the
current branch. `groupy init --from-stage=<branch_name>/<stage_name>` takes the stage of another branch.
The new branch gets copies of the init tag and of the start tags of the stages up to and including <stage_name>, so
that `groupy reset` (including `groupy reset init`) works on it as usual. The session file and the config file are
those of the tagged commit, so the new branch has the same base branch as the branch that it starts from.
It is an error when the stage has not started (it has no start tag).

## Tags

The tags include the branch name: `groupy/<branch_name>/init` and `groupy/<branch_name>/<stage_id>/start`.
Since a branch name may contain a `/`, an argument `<branch_name>/<stage_name>` is split at the last `/` (stage names
never contain one).
Sessions that were started with the old tags (`groupy/init`, `groupy/<stage_id>/start`) are not supported.

## Per-branch files

The files that groupy does not commit (`last-run.yaml`, `call-graph.yaml`, `logs/` and `requests/`) live in
`.groupy/<branch_name>/`, so that branches don't share them. `groupy init` creates this dir. All dirs in `.groupy` are
excluded from git (with a single `/.groupy/*/` line in `info/exclude`), since the committed groupy files
(`session.yaml`, `config.yaml` and `groups.txt`) are not in a dir.

# groupy status

`groupy status` reports the state of the session of the current branch, starting with the branch name. The costs are
those of the current branch only.
`groupy status --all` prints a line per groupy branch, with its name, its next stage, the result of its last run and
its costs. It also lists the aborted branches (that have a per-branch dir but no branch anymore), with their costs.
It ends with the total costs of all branches.

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
`since the start of extract-methods` or `on branch groupy-2`. The commits part is left out for `switch` and
`leave`, and the uncommitted changes part is left out when the working tree is clean. The uncommitted changes
include untracked files.

Uncommitted changes are discarded with `git reset --hard` and `git clean -fd`.

# groupy reset

`groupy reset` resets the current branch to the start of the current stage.
`groupy reset <stage_name>` resets the current branch to the start of <stage_name>.
`groupy reset init` resets the current branch to the start of the session (this replaces `groupy reset --init`).
It is an error when the stage has not started (it has no start tag), as it is today.
Afterwards, it prints the previous head, so that the developer can undo the reset, as it does today.

# groupy switch

`groupy switch <branch_name>` checks out another groupy branch. Uncommitted changes on the current branch are lost
(see Losing work).

# groupy leave and groupy abort

`groupy leave` checks out the base branch, and keeps the groupy branch. Uncommitted changes are lost (see Losing
work).

`groupy abort` checks out the base branch, and deletes the current groupy branch and its tags. All commits of the
branch and the uncommitted changes are lost (see Losing work).
`groupy abort <branch_name>` deletes another groupy branch and its tags, and stays on the current branch. Only the
commits of that branch are lost. When <branch_name> is the current branch, it is the same as `groupy abort`.

`groupy abort` keeps `.groupy/<branch_name>/`, so that the logs (and the costs) of the session stay available and
the branch name is not reused. It writes `.groupy/<branch_name>/undo-abort.sh`, a script that recreates the branch
and its tags at the commits where they were, and prints how to run it (`sh .groupy/<branch_name>/undo-abort.sh`).
The script cannot restore the uncommitted changes.

# Error hints

Since being on the base branch is normal now, the hint of `NoSessionError` mentions `groupy switch <branch_name>`
(to continue a session) and `groupy init` (to start one).

# progress messages

Groupy prints a progress message on stderr at the start of each chunk, with the request id and the position of the
chunk among all chunks of the stage, e.g. `extract-methods/group-2/chunk-1 (3/12)`.
When a stage resumes, the finished chunks are skipped without a message, so the count starts later (e.g. at `(4/12)`).
A stage without chunks prints a single message when it starts, e.g. `propose-module-layout`.
