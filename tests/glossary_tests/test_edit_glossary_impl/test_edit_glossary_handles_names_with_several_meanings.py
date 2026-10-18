from glossary_tests.glossary_test_env import Context, TestEnv

from groupy.concepts.utils.exceptions import AmbiguousEntryError
from groupy.nodes.utils.exceptions import EntryNotFoundError

GLOSSARY_YAML = """\
- name: report
  description: a markdown document with the statistics of a user
- name: report
  description: an error report that is sent to Sentry
- name: statistics
  description: the statistics of a user
"""


def create_env(context: Context):
    return Env(context)


def test_edit_glossary_handles_names_with_several_meanings(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a glossary with two entries for "report" (one per meaning), and
    # an entry for "statistics".
    if env.step(
        env.write_glossary(GLOSSARY_YAML),
        env.remember_glossary_file(),
    ):
        pass

    # We add an alias to "report" without a meaning_nr, and merge "statistics"
    # into "report" without an into_meaning_nr.
    #
    # It is not clear which entry is meant, so each should raise an
    # AmbiguousEntryError and leave the glossary unchanged.
    if env.step(
        env.catch_error(env.add_glossary_alias, "report", "error_doc"),
    ):
        assert isinstance(env.error, AmbiguousEntryError)

    if env.step(
        env.catch_error(env.merge_glossary_entries, "statistics", "report"),
    ):
        assert isinstance(env.error, AmbiguousEntryError)
        assert env.glossary_file_is_unchanged()

    # We add an alias to "report" with meaning_nr 3.
    #
    # There is no third meaning, so it should raise an EntryNotFoundError.
    if env.step(
        env.catch_error(env.add_glossary_alias, "report", "error_doc", meaning_nr=3),
    ):
        assert isinstance(env.error, EntryNotFoundError)
        assert env.glossary_file_is_unchanged()

    # We add an alias to the second meaning of "report", and change the
    # description of the first meaning.
    #
    # Only the entry of that meaning should change.
    if env.step(
        env.add_glossary_alias("report", "error_doc", meaning_nr=2),
        env.set_glossary_description(
            "report",
            "a markdown document with the usage statistics of a user",
            meaning_nr=1,
        ),
        env.load_glossary(),
    ):
        assert env.entry("report", meaning_nr=1).aliases == []
        assert env.entry("report", meaning_nr=2).aliases == ["error_doc"]
        assert env.descriptions("report") == [
            "a markdown document with the usage statistics of a user",
            "an error report that is sent to Sentry",
        ]

    # We merge "statistics" into the first meaning of "report".
    #
    # "statistics" should become an alias of that entry only.
    if env.step(
        env.merge_glossary_entries("statistics", "report", into_meaning_nr=1),
        env.load_glossary(),
    ):
        assert env.names() == ["report", "report"]
        assert env.entry("report", meaning_nr=1).aliases == ["statistics"]
        assert env.entry("report", meaning_nr=2).aliases == ["error_doc"]


class Env(TestEnv):
    pass
