import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s14_groupy_proposes_the_code_restructure")


def run_scenario():
    r.claude = c.External.Actors.Claude
    r.developer = c.External.Actors.Developer
    r.stage_action = c.Restructure.Actions.ProposeCodeRestructure
    r.set_code_unit_type_action = c.Nodes.Actions.SetCodeUnitType
    r.set_move_to_file_action = c.Nodes.Actions.SetMoveToFile
    r.set_rename_to_action = c.Nodes.Actions.SetRenameTo
    r.validate_code_restructure_rule = c.Restructure.Rules.ValidateCodeRestructure
    r.find_dependency_violations_rule = c.Restructure.Rules.FindDependencyViolations

    with goal().propose_a(r.target_file).for_each(r.code_unit):
        with the(r.stage_action).processes_each(r.chunk):

            # Claude proposes the restructure
            with the(r.stage_action).sends_an(r.rfa).with_the(r.module_sources).and_the(
                r.proposed_modules
            ).and_the(r.call_graph_view).and_the(r.glossary).to(r.claude):
                with the(r.claude).classifies_each(r.top_level_node):
                    it().calls(r.set_code_unit_type_action)
                    it().calls(r.set_move_to_file_action).if_the(
                        r.target_file
                    ).is_another_file()
                it().calls(r.set_rename_to_action).for_each(r.module).that_stays()
                it().calls(r.set_code_unit_type_action).and_(
                    r.set_move_to_file_action
                ).for_each(r.method).that_should_delegate()

            # Validate the proposal
            with the(r.stage_action).calls(r.validate_code_restructure_rule).for_the(
                r.chunk
            ):
                it().returns_the(r.problems)
            the(r.stage_action).sends_a(r.follow_up_rfa).with_the(r.problems).to(
                r.claude
            )
            it().raises(r.code_restructure_has_problems_error).if_problems_remain()

        # Report the dependency violations
        with the(r.stage_action).calls(r.find_dependency_violations_rule):
            it().returns_the(r.dependency_violations)
        the(r.stage_action).reports_the(r.dependency_violations).to_the(r.developer)

        the(r.developer).reviews_the(r.proposal)


markdown_node = sunya.add_markdown_node(
    scenario, "Groupy proposes the code restructure"
)

markdown_node.markdown = """
In this stage, Claude decides for every code unit what kind of code unit it is (e.g. an action or a rule), and in
which file of the module layout it belongs. The proposal is recorded in the node files, validated by Groupy, and
reviewed by the developer before the next stage applies it.

### Steps

#### Claude proposes the restructure

Groupy makes an RFA per chunk, whose context contains the sources of the modules, the proposed modules, the call
graph view (with the callers and callees, so that Claude can follow the dependency direction) and the glossary.
Claude records the proposal with callbacks:</br>

- For every top-level function, class and module-level variable: its `code_unit_type` and, when it goes to another
  file, its `move_to_file`. Since an empty `move_to_file` is left out of the node file, Groupy uses
  `code_unit_type` to check that every node was considered. Helper functions need neither: they stay with their
  parent.
- For a module that continues to exist (typically named after its main function): its `rename_to`.
- For a method that should delegate: a `code_unit_type` (`action`, `rule` or `util`) and a `move_to_file`.

The target structure follows these guidelines:</br>

| Code unit | What it is | Where it goes |
|---|---|---|
| action | a function that changes the application state (e.g. it writes to a database, a file or a network service, or mutates its arguments) | `<package>/actions/<name>.py` |
| rule | a function that retrieves or computes information subject to business logic, without changing the state | `<package>/rules/<name>.py` |
| util | a function without business logic (a generic helper) | `<package>/utils/<name>.py`, or a shared group file for many small related utils |
| model | a dataclass (using `dataclassy`) that represents a domain entity | `<package>/models/<name>.py` |
| schema | a pydantic class that describes the structure of a JSON blob | a schema file close to the code that uses it |
| enum | an enum | `<package>/enums.py` (all enums of a package) |
| setting | a module-level variable that configures the application (including reads of environment variables) | `<app_package>/settings.py` |
| constant | any other module-level variable | the file of the code unit that uses it (when several use it: preferably the lowest in the dependency direction) |
| entrypoint | an entrypoint of the application | `<app_package>/runtime/entrypoints/<name>.py` |
| exception | an exception class | the action file that raises it (generic ones in `<package>/utils/exceptions.py`) |
| policy | the interface to an external service (e.g. Claude or a payment provider) | `<package>/policies/<name>.py`, with each implementation in its own file next to it |

A class that fits none of these types gets the type `other`.

- Each action, rule, util and model gets a file of its own, named after it in snake_case (e.g. `CreateChapterForm`
  and `create_chapter` live in `chapters/actions/create_chapter.py`). Helper functions stay in the file of their
  parent.
- Dependencies point in one direction: entrypoints → actions → rules → utils. Models, schemas and enums may be used
  by all code units. A policy is passed as an argument to the action that uses it, so that tests can pass a fake.
- Type references to models in other modules use a `typing.TYPE_CHECKING` guard, to avoid circular imports.

A method is a special case. Some methods must stay methods, because Python or a framework calls them: dunder
methods, properties, overrides of a base class method (e.g. `save` in a Django model), and methods with several
implementations across subclasses. Any other method may *delegate*: the method keeps existing, but its body
becomes a call of a new action, rule or util that takes the instance as its first argument. The new function is
named after its target file (e.g. `save_book` for `myapp/books/actions/save_book.py`). Since the method stays, its
call sites (which may be uncertain in the call graph) don't change; the developer can later inline the method.</br>

#### It validates the proposal

After the RFA of a chunk, `validate_code_restructure` checks the proposal for the nodes of the chunk:</br>

- every top-level node has a `code_unit_type`;
- each `move_to_file` matches the location of its `code_unit_type` (e.g. a model goes to `<package>/models/`);
- no target file receives more than one public code unit (except for util group files, enums, schemas, settings,
  constants, and the exceptions and forms that go with an action);
- a method with a `move_to_file` can delegate (e.g. it is not a dunder method, a property or an override of a
  method in the target code, and it does not use `super()`);
- no target package has the name of a module that stays (e.g. `myapp/books/` next to `myapp/books.py`), because
  Python cannot import both.

Each problem is a line such as `myapp/reports/report.py:count_reports: has no code_unit_type`. Problems get one
follow-up RFA; problems that remain raise `CodeRestructureHasProblemsError`, which interrupts the stage.</br>

#### It reports the dependency violations

After the last chunk, Groupy uses the call graph to find calls that go against the dependency direction (e.g.
`myapp/reports/report.py:get_overdue_reports (rule) calls myapp/reports/report.py:send_reminder (action)`). A helper
function has the type of its parent, and a method the type of its class, unless it delegates. The violations are
only printed: they don't block the stage, because the developer may accept them during the review.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Claude
    actor Developer
    participant Stage as ProposeCodeRestructure (action)
    participant NodeEdits as set_code_unit_type, set_move_to_file, set_rename_to (actions)
    participant ValidateCodeRestructure as ValidateCodeRestructure (rule)
    participant FindDependencyViolations as FindDependencyViolations (rule)

    loop for each chunk
        Note over Stage,NodeEdits: Claude proposes the restructure
        Stage->>Claude: RFA(module_sources, proposed_modules, call_graph_view, glossary)
        loop for each top-level node, module and delegating method
            Claude->>NodeEdits: code_unit_type, move_to_file, rename_to
        end

        Note over Stage,ValidateCodeRestructure: Validate the proposal
        Stage->>ValidateCodeRestructure: validate_code_restructure(chunk)
        ValidateCodeRestructure-->>Stage: problems
        opt there are problems
            Stage->>Claude: follow-up RFA(restructure_problems)
        end
    end

    Note over Stage,FindDependencyViolations: Report the dependency violations
    Stage->>FindDependencyViolations: find_dependency_violations()
    FindDependencyViolations-->>Developer: dependency violations (printed)
    Developer->>Developer: review the proposal
```
"""
