import sunya
from sunya import M as m
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s01_a_developer_starts_a_session")


def run_scenario():
    r.developer = m.External.Actors.Developer
    r.groupy_cli = m.Runtime.Entrypoints.Groupy
    r.init_session_action = m.Sessions.Actions.InitSession
    r.session = m.Sessions.Models.Session
    r.config = m.Sessions.Models.Config
    r.create_package_node_file_action = m.Nodes.Actions.CreatePackageNodeFile
    r.create_module_node_file_action = m.Nodes.Actions.CreateModuleNodeFile
    r.create_group_file_action = m.Groups.Actions.CreateGroupFile

    with goal().start_a(r.session).for_the(r.target_code):

        # Start the session
        with the(r.developer).runs(r.groupy_cli).with_the(r.init_command):
            it().calls(r.init_session_action).with_the(r.target_dir).and_the(
                r.branch_name
            )

        with the(r.init_session_action).checks_the(r.preconditions):
            it().raises(r.session_exists_error).if_the_repo_already_has_a(
                r.session_file
            )
            it().raises(r.dirty_working_tree_error).if_the(
                r.working_tree
            ).is_not_clean()

        with the(r.init_session_action).creates_the(r.branch):
            it().creates(r.session).with_the(r.target_dir).and_the(r.next_stage)
            it().writes(r.session).to_the(r.session_file)
            it().writes_the_default(r.config).to_the(
                r.config_file
            ).if_the_repo_has_none()

        # Create the source map
        with the(r.init_session_action).creates_node_files_for(r.target_code):
            with the(r.init_session_action).calls(
                r.create_package_node_file_action
            ).for_each(r.package):
                it().creates(r.package_node_file).with_the(r.module_names)

            with the(r.init_session_action).calls(
                r.create_module_node_file_action
            ).for_each(r.module):
                it().creates(r.module_node_file).that_reflects_the_structure_of(
                    r.module
                )

        # Group the modules
        with the(r.init_session_action).calls(r.create_group_file_action).with_the(
            r.config
        ):
            it().assigns_each(r.module).to_a(r.group)
            it().writes(r.group_file)

        the(r.init_session_action).commits(r.session_file).and_the(
            r.config_file
        ).and_the(r.group_file).and_the(r.node_files)
        the(r.developer).reviews(r.node_files).and_the(r.group_file)


markdown_node = sunya.add_markdown_node(scenario, "A developer starts a session")

markdown_node.markdown = """
Groupy is a radical refactoring tool that takes a Python code-base (the *target code*) apart and rebuilds it. Since
it is expected to break the code, the developer helps with fixing errors and testing.

The work is organized in a *session* that runs a fixed sequence of *stages*, one per `groupy next`. A session
starts with `groupy init`, which creates a branch to work on and a *source map* of the target code: a yaml *node
file* per module and package. In the later stages, Groupy and Claude fill the node files with an analysis of the
code (e.g. its concepts, responsibilities and steps), propose changes in them, and apply those changes to the
code. For Groupy, the node files are the record of what was analyzed, proposed and done.

### Steps

#### It checks the preconditions

The developer runs `groupy init --target-dir=<target-dir> --branch-name=<branch-name>` from the repository root.
The branch name defaults to `groupy`.</br>
`init_session` refuses to start when the repository already has a session (`SessionExistsError`), or when the
working tree is not clean (`DirtyWorkingTreeError`).</br>

#### It creates the branch, the session file and the config file

`init_session` creates the branch and writes the session file (`.groupy/session.yaml`). The session file contains:</br>

- `target_dir`: the dir that contains the target code.
- `next_stage`: the stage that the next `groupy next` runs (initially `identify-helper-functions`).

The config file (`.groupy/config.yaml`) holds the choices that the developer makes for the session, such as the
grouping strategy and the maximum sizes of groups and chunks, and the policies that Groupy uses to talk to Claude
and to refactor the code. When the repository has no config file, Groupy writes one that lists every field with its
default value, so that the developer can see what can be configured. An existing config file is kept, so the
developer can prepare it before running `groupy init`.</br>

#### It creates the node files

Groupy creates a *package node file* (`package-node.groupy.yaml`) in the dir of every package, and a *module node
file* (e.g. `books.py.groupy.yaml`) next to every module.</br>

- A package is the target dir itself (the root package, with the name `.`), or a dir below it that contains Python
  modules, directly or in a sub-dir. It does not need an `__init__.py` (namespace packages are packages too). Its
  node file lists its `module_names`.
- An `__init__.py` is just another module, so it gets a module node file.
- Paths in node files are relative to the target dir (e.g. `myapp/books.py`).

Initially, a module node file only reflects the structure of the module:</br>

```yaml
module_node:
  name: myapp/books.py
  line_count: 14
  function_nodes:
    - name: create_book
    - name: _normalize_title
  class_nodes:
    - name: Book
      method_nodes:
        - name: __init__
  variable_nodes:
    - name: MAX_CHAPTERS
```

Every top-level function gets a function node, every class a class node (with a node per method), and every
module-level variable a variable node. A function that is nested in the Python code (e.g. a closure) has no node
of its own: it counts as part of the body of its enclosing function. The `helper_function_nodes` of a function node
are still empty: identifying helper functions is the first stage.</br>
Groupy leaves out the fields that have their default value (e.g. `null`, `[]` or `false`), and reads a missing
field as its default value.</br>

#### It creates the group file

To keep the workload per Claude request reasonable, the stages process the modules in groups, and the groups in
chunks. `create_group_file` assigns each module to a group, using the grouping strategy and the maximum group size
in the config file, and writes the group file (`.groupy/groups.txt`).</br>

#### It commits

Groupy commits the session file, the config file, the group file and the node files on the new branch. Before
running the first stage, the developer can inspect (and edit) the node files and the group file.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Groupy as Groupy (entrypoint)
    participant InitSession as InitSession (action)
    participant CreatePackageNodeFile as CreatePackageNodeFile (action)
    participant CreateModuleNodeFile as CreateModuleNodeFile (action)
    participant CreateGroupFile as CreateGroupFile (action)

    Note over Developer,InitSession: Start the session
    Developer->>Groupy: groupy init --target-dir --branch-name
    Groupy->>InitSession: init_session(target_dir, branch_name)
    InitSession->>InitSession: check: no session, clean working tree
    InitSession->>InitSession: create branch
    InitSession->>InitSession: write session file (next_stage = identify-helper-functions)
    InitSession->>InitSession: write default config file (if missing)

    Note over InitSession,CreateModuleNodeFile: Create the source map
    loop for each package
        InitSession->>CreatePackageNodeFile: create_package_node_file(package)
    end
    loop for each module
        InitSession->>CreateModuleNodeFile: create_module_node_file(module)
    end

    Note over InitSession,CreateGroupFile: Group the modules
    InitSession->>CreateGroupFile: create_group_file(config)
    CreateGroupFile-->>InitSession: group file

    InitSession->>InitSession: commit session, config, group and node files
    Developer->>Developer: review node files and group file
```
"""
