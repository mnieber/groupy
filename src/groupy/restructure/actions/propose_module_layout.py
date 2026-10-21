from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.concepts.rules.get_glossary_path import get_glossary_path
from groupy.concepts.rules.get_glossary_text import get_glossary_text
from groupy.nodes.rules.get_active_module_names import get_active_module_names
from groupy.nodes.rules.get_module_names import get_module_names
from groupy.restructure.rules.get_module_summaries import get_module_summaries
from groupy.sessions.actions.run_unfinished_step import run_unfinished_step
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_exclude_patterns import get_exclude_patterns
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config
from groupy.utils.print_progress import print_progress

PROMPT = """\
Propose the feature packages of the application, using the module summaries and the
glossary. The application consists of a single application package (e.g. myapp),
which is divided into feature packages (e.g. myapp/books). Each feature package
covers one cohesive area of the domain, and is named after its main concept, using
the canonical name from the glossary (preferably in plural form). Code that is used by
several feature packages but belongs to none of them goes into a shared package (e.g.
myapp/utils). Record each feature package with set_proposed_module(name,
description), where name is the path of the package.
"""


def propose_module_layout() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    rfa_policy = create_rfa_policy(config)
    source_root = get_source_root()

    # The passive modules keep their location, so they are left out
    active_module_names = get_active_module_names(
        get_module_names(source_root), get_exclude_patterns()
    )

    def _propose(rfa_id: str) -> None:
        print_progress(Stages.PROPOSE_MODULE_LAYOUT.value)
        rfa_policy.run(
            Rfa(
                id=rfa_id,
                prompt=PROMPT,
                context={
                    "glossary": get_glossary_text(get_glossary_path(source_root)),
                    "module_summaries": get_module_summaries(
                        source_root, active_module_names
                    ),
                },
            )
        )

    # The single RFA for the whole code-base is recorded as a finished chunk
    run_unfinished_step(Stages.PROPOSE_MODULE_LAYOUT, "all", _propose)
