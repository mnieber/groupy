from groupy.nodes.utils.exceptions import EntryNotFoundError
from glossary_tests.glossary_test_env import Context, TestEnv

GLOSSARY_YAML = """\
- name: title
  description: the name of a book
  aliases: [name]
"""


def create_env(context: Context):
    return Env(context)


def test_edit_glossary_rejects_unknown_names(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a glossary with an entry for "title", which has the alias
    # "name".
    if env.step(
        env.write_glossary(GLOSSARY_YAML),
        env.remember_glossary_file(),
    ):
        pass

    # We edit the entry of "author", which is not in the glossary.
    #
    # Each edit should raise an EntryNotFoundError and leave the glossary
    # unchanged, so that a typo does not go unnoticed.
    if env.step(
        env.catch_error(env.set_glossary_description, "author", "the writer of a book"),
    ):
        assert isinstance(env.error, EntryNotFoundError)

    if env.step(
        env.catch_error(env.add_glossary_alias, "author", "writer"),
    ):
        assert isinstance(env.error, EntryNotFoundError)

    if env.step(
        env.catch_error(env.set_glossary_abbreviation, "author", "aut"),
    ):
        assert isinstance(env.error, EntryNotFoundError)
        assert env.glossary_file_is_unchanged()

    # We merge "author" into "title", and "title" into "author".
    #
    # Both should raise an EntryNotFoundError and leave the glossary unchanged.
    if env.step(
        env.catch_error(env.merge_glossary_entries, "author", "title"),
    ):
        assert isinstance(env.error, EntryNotFoundError)

    if env.step(
        env.catch_error(env.merge_glossary_entries, "title", "author"),
    ):
        assert isinstance(env.error, EntryNotFoundError)
        assert env.glossary_file_is_unchanged()

    # We add the alias "name" of "title" a second time.
    #
    # The alias should be listed once.
    if env.step(
        env.add_glossary_alias("title", "name"),
        env.load_glossary(),
    ):
        assert env.entry("title").aliases == ["name"]


class Env(TestEnv):
    pass
