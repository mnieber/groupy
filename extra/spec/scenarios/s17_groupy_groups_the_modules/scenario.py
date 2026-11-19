import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s17_groupy_groups_the_modules")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.groupy_cli = c.Runtime.Entrypoints.Groupy
    r.run_next_stage_action = c.Runtime.Actions.RunNextStage
    r.group_modules_action = c.Groups.Actions.GroupModules
    r.create_group_file_action = c.Groups.Actions.CreateGroupFile
    r.config = c.Sessions.Models.Config

    with goal().divide_the(r.modules).into(r.groups):

        # The developer configures the grouping
        the(r.developer).edits_the(r.grouping_strategy).and_the(
            r.max_group_lines
        ).in_the(r.config_file)
        the(r.developer).commits_the(r.config_file)

        # Group the modules
        with the(r.developer).runs(r.groupy_cli).with_the(r.next_command):
            with the(r.run_next_stage_action).calls(r.group_modules_action):
                with it().calls(r.create_group_file_action).with_the(r.config):
                    it().assigns_each(r.module).to_a(r.group)
                    it().writes(r.group_file)
                it().commits_the(r.group_file)
            the(r.run_next_stage_action).finishes_the(r.stage)

        the(r.developer).reviews_the(r.group_file)


markdown_node = sunya.add_markdown_node(scenario, "Groupy groups the modules")

markdown_node.markdown = """
To keep the workload per Claude request reasonable, the stages process the modules in *groups*, and the groups in
chunks. The first stage, group-modules, assigns each module to a group. Since it is a stage of its own
(and not part of `groupy init`), the developer can choose how the modules are grouped in the config file that
`groupy init` wrote, before the grouping happens.

### Steps

#### The developer configures the grouping

After `groupy init`, the developer may change the grouping strategy and the maximum group size in the config file
(`.groupy/config.yaml`), and commits the change.</br>

#### It groups the modules

The developer runs `groupy next`. Unlike the other stages, group-modules runs without a group file (it creates
one). The stage calls `create_group_file`, which assigns each module to a group, using the grouping strategy and
the maximum group size in the config file:</br>

- `simple`: the modules, sorted by path, are divided into groups of at most `max_group_lines` lines.
- `package` (the default): a group contains the entire file-tree of a sub-package of a top-level package (e.g.
  `myapp/books`); the modules directly in a top-level package form a group of their own.

It writes the group file (`.groupy/groups.txt`), which assigns each module (by its path, e.g. `myapp/books.py`) to
a group, and commits it with the message `group-modules: create the group file`. Then the stage finishes as usual.
The stage makes no Claude requests.</br>

#### The developer reviews the group file

The developer reviews the group file, and may edit it (e.g. to move a module to another group) before running the
next stage.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Groupy as Groupy (entrypoint)
    participant RunNextStage as RunNextStage (action)
    participant GroupModules as GroupModules (action)
    participant CreateGroupFile as CreateGroupFile (action)

    Note over Developer: The developer configures the grouping
    Developer->>Developer: edit the grouping strategy in the config file, commit

    Note over Developer,CreateGroupFile: Group the modules
    Developer->>Groupy: groupy next
    Groupy->>RunNextStage: run_next_stage()
    RunNextStage->>GroupModules: group_modules()
    GroupModules->>CreateGroupFile: create_group_file(config)
    CreateGroupFile-->>GroupModules: group file
    GroupModules->>GroupModules: commit "group-modules: create the group file"
    RunNextStage->>RunNextStage: finish the stage

    Developer->>Developer: review the group file
```
"""
