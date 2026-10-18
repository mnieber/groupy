import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario(f"s13_groupy_proposes_the_module_layout")


def run_scenario():
    r.claude = c.External.Actors.Claude
    r.developer = c.External.Actors.Developer
    r.stage_action = c.Restructure.Actions.ProposeModuleLayout
    r.set_proposed_module_action = c.PackageNodes.Actions.SetProposedModule
    r.remove_proposed_module_action = c.PackageNodes.Actions.RemoveProposedModule
    r.process_chunks_action = c.Sessions.Actions.ProcessChunks

    with goal().propose_the(r.feature_packages).of_the(r.application):

        # Summarize the code-base
        with the(r.stage_action).summarizes_each(r.module_node_file):
            it().takes_the(r.module_concepts)
            it().takes_the(r.first_responsibility).of_each(r.top_level_node)

        # Claude proposes the module layout
        with the(r.stage_action).calls(r.process_chunks_action).with_a(r.single_chunk):
            with the(r.stage_action).sends_an(r.rfa).with_the(
                r.module_summaries
            ).and_the(r.glossary).to(r.claude):
                the(r.claude).calls(r.set_proposed_module_action).for_each(
                    r.feature_package
                )
                it().may_call(r.remove_proposed_module_action)

        the(r.developer).reviews_the(r.proposed_modules)


markdown_node = sunya.add_markdown_node(scenario, "Groupy proposes the module layout")

markdown_node.markdown = """
The code restructure moves every code unit to a file in a *feature package*. In this stage, Claude proposes these
feature packages, before the next stage decides where each code unit goes. Since the layout must fit the entire
code-base, this stage makes a single request for the whole code-base instead of one per chunk. To keep it small,
Groupy condenses the node files into summaries.

### Steps

#### It summarizes the code-base

Per module node file, Groupy takes the module concepts and maps each top-level function and class onto its first
responsibility (or `None`). Module-level variables and helper functions are left out.</br>

#### Claude proposes the module layout

Groupy makes a single RFA (`propose-module-layout/all`), whose context contains the module summaries and the
glossary. It is recorded as a finished chunk, so that a resumed stage does not repeat it.</br>
Claude records the proposed feature packages in the `proposed_modules` of the root package node file, mapping the
path of each package onto a one-line description (e.g. `myapp/books: the creation and publication of books`), with
`set_proposed_module` and `remove_proposed_module`. It follows these guidelines:</br>

- The application consists of a single application package (e.g. `myapp/`), which is divided into feature
  packages (e.g. `myapp/books/` and `myapp/chapters/`).
- Each feature package covers one cohesive area of the domain, and is named after its main concept, using the
  canonical name from the glossary. When in doubt, the plural form is preferred (e.g. `books`).
- Code that is used by several feature packages but belongs to none of them goes into a shared package (e.g.
  `myapp/utils/` for generic utils).

#### The developer reviews the module layout

The developer reviews (and possibly edits) the proposed modules before running the next stage.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Claude
    actor Developer
    participant Stage as ProposeModuleLayout (action)
    participant SetProposedModule as SetProposedModule (action)

    Note over Stage: Summarize the code-base
    Stage->>Stage: module concepts and first responsibilities per module node file

    Note over Stage,SetProposedModule: Claude proposes the module layout
    Stage->>Claude: RFA(module_summaries, glossary)
    loop for each feature package
        Claude->>SetProposedModule: set_proposed_module(name, description)
    end

    Developer->>Developer: review the proposed modules
```
"""
